"""The cl service: what a sandboxed agent may ask for, and that the answer comes back unchanged."""
import json
import shutil
from pathlib import Path

import pytest

from checklimits import agent_service as svc

RUN = Path("/tmp/clsvc-test-run")


@pytest.fixture
def run_dir(tmp_path):
    r = tmp_path / "r1"
    (r / "workspace" / "attempt").mkdir(parents=True)
    (r / "out").mkdir()
    return r


def ok(argv, run_dir, cwd=None):
    return svc.sanitize(argv, str(cwd or run_dir), run_dir)


def bad(argv, run_dir, cwd=None):
    with pytest.raises(svc.BadRequest) as e:
        ok(argv, run_dir, cwd)
    return str(e.value)


def test_the_commands_the_agent_instructions_use_are_accepted(run_dir):
    a, o = run_dir / "workspace" / "attempt", run_dir / "out"
    assert ok(["task", "nnsmith-F004", "--findings-file", "results/step4/nnsmith/limitations_for_tests.json",
               "--data-dir", "data/nnsmith"], run_dir)[:2] == ["task", "nnsmith-F004"]
    assert ok(["init", "F07", "--out", str(a)], run_dir) == ["init", "F07", "--out", str(a.resolve())]
    assert ok(["lint", "--attempt", "workspace/attempt"], run_dir, cwd=run_dir) == ["lint", "--attempt", str(a.resolve())]
    assert ok(["run", "--attempt", str(a), "--out", str(o), "--fast"], run_dir)[-1] == "--fast"
    r = ok(["run", "--attempt", str(a)], run_dir)                       # --out defaults to the run's out directory
    assert r[-2:] == ["--out", str(o.resolve())]


def test_everything_else_is_refused(run_dir):
    a = run_dir / "workspace" / "attempt"
    assert "must be one of" in bad(["bench"], run_dir) and "must be one of" in bad([], run_dir)
    assert "must be one of" in bad(["agent", "F07", "--run-id", "x"], run_dir)
    assert "not available" in bad(["run", "--attempt", str(a), "--python", "/bin/sh"], run_dir)
    assert "not available" in bad(["run", "--attempt", str(a), "--repeats", "1"], run_dir)
    assert "must be inside" in bad(["run", "--attempt", "/etc", "--out", str(run_dir / "out")], run_dir)
    assert "must be inside" in bad(["lint", "--attempt", str(run_dir / "workspace" / ".." / ".." / "x")], run_dir)
    assert "must be inside" in bad(["run", "--attempt", str(a), "--out", "/tmp/elsewhere"], run_dir)
    assert "only results/step4" in bad(["task", "F1", "--findings-file", "checklimits/scratch/x.json"], run_dir)
    assert "without '..'" in bad(["task", "F1", "--findings-file", "../x.json"], run_dir)
    assert "without '..'" in bad(["task", "F1", "--data-dir", "/etc"], run_dir)
    assert "exactly one finding" in bad(["task"], run_dir) and "unexpected argument" in bad(["task", "a b"], run_dir)
    assert "needs --attempt" in bad(["lint"], run_dir) and "needs --out" in bad(["init", "F1"], run_dir)


def test_service_runs_the_command_and_returns_its_output_untouched(run_dir):
    seen = []

    def fake(argv):
        seen.append(argv)
        return 3, "line one\nline two\n", "warning\n"
    with svc.ClService(run_dir, fake) as s:
        r = svc.call(str(s.dir / "sock"), ["lint", "--attempt", str(run_dir / "workspace" / "attempt")], str(run_dir))
        assert r == {"rc": 3, "stdout": "line one\nline two\n", "stderr": "warning\n"}
        r = svc.call(str(s.dir / "sock"), ["bench"], str(run_dir))                    # refused before anything runs
        assert r["rc"] == 2 and "must be one of" in r["stderr"] and len(seen) == 1
    assert not s.dir.exists()                                                           # the socket directory is removed
    assert [x.get("rejected") is not None for x in s.log] == [False, True]


def test_the_client_script_prints_stdout_and_stderr_and_exits_with_the_command_status(run_dir):
    import subprocess
    import sys
    client = Path(svc.PROJECT_ROOT) / "agent" / "cl_client.py"
    with svc.ClService(run_dir, lambda argv: (7, "out\n", "err\n")) as s:
        p = subprocess.run([sys.executable, str(client), "lint", "--attempt", str(run_dir / "workspace" / "attempt")],
                           env={"CL_SOCKET": str(s.dir / "sock")}, cwd=run_dir, capture_output=True, text=True)
    assert (p.returncode, p.stdout, p.stderr) == (7, "out\n", "err\n")
    p = subprocess.run([sys.executable, str(client), "lint"], env={}, capture_output=True, text=True)
    assert p.returncode == 2 and "CL_SOCKET" in p.stderr
