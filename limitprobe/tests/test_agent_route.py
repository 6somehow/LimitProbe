import json
from pathlib import Path

import pytest

from codeside.agent_extractor import KEEP_TOOL_OUTPUTS, MAX_FORCED_REREADS, MAX_TOOL_CHARS, REMIND_EVERY, AgentExplorer, RepoTools, enclosing_function, extract_agent
from codeside.extractor import ExtractConfig, extract

FIX = Path(__file__).resolve().parent / "fixtures"
FILE = "hybrid_module.py"
CFG = ExtractConfig(repo=FIX, entry=f"{FILE}::top", artifact_id="toy")


def call(name, cid="c", **args):
    return {"id": f"{cid}-{name}", "type": "function", "function": {"name": name, "arguments": json.dumps(args)}}


class Script:
    """Fake model: plays back a list of tool-call turns, then finishes."""

    def __init__(self, *turns):
        self.turns = list(turns)
        self.seen = []
        self.prompt_tokens = self.completion_tokens = 0

    def chat(self, messages, tools):
        self.seen.append(json.loads(json.dumps(messages)))
        calls = self.turns.pop(0) if self.turns else [call("finish")]
        if isinstance(calls, Exception):
            raise calls
        return {"role": "assistant", "content": "", "tool_calls": calls} if calls else {"role": "assistant", "content": "hm"}


def report(line=34, code="if warm:", cond="warm", outcome="mechanism_variant", file=FILE):
    return call("report", cid=f"r{line}{cond}", file=file, line=line, code=code, condition=cond, outcome=outcome, detail="d")


def test_tools_are_confined_to_the_repo(tmp_path):
    (tmp_path / "a.py").write_text("x = 1\n")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("secret\n")
    outside = tmp_path.parent / "outside_secret.txt"
    outside.write_text("secret\n")
    (tmp_path / "link.txt").symlink_to(outside)
    tools = RepoTools(tmp_path)
    assert "1: x = 1" in tools.read_file("a.py")
    for bad in ("../outside_secret.txt", "link.txt", ".git/config", str(outside)):
        with pytest.raises(ValueError):
            tools.read_file(bad)
    assert ".git" not in tools.list_dir()
    assert "secret" not in tools.grep("secret")
    with pytest.raises(ValueError):
        tools.grep("x", "..")


def test_grep_treats_a_leading_dash_as_a_pattern():
    assert "(no matches)" == RepoTools(FIX).grep("--zzz-not-there")


def test_read_file_pages_long_files(tmp_path):
    (tmp_path / "long.py").write_text("\n".join(f"x{i} = {i}" for i in range(600)))
    tools = RepoTools(tmp_path)
    first = tools.read_file("long.py")
    assert "250: x249" in first and "251:" not in first and "stopped at line 250; file has 600 lines" in first
    assert "300: x299" in tools.read_file("long.py", 300, 300)


def test_binary_files_are_refused(tmp_path):
    (tmp_path / "b.bin").write_bytes(b"\0\1\2")
    with pytest.raises(ValueError):
        RepoTools(tmp_path).read_file("b.bin")


def test_agent_can_read_outside_the_static_walk_and_report_there():
    # `Unrelated.helper` is never reached by route A from `top`.
    res = extract_agent([CFG], Script(
        [call("grep", pattern="never")],
        [report(line=17, code='assert mode == "never"', cond='mode != "never"', outcome="reject")]))
    added = [r for r in res.regions if r.region_id.startswith("D")]
    assert added[0].location.function == f"{FILE}::Unrelated.helper"
    assert added[0].provenance == "llm" and added[0].notes == "agent: outside the static walk"
    assert res.meta["added_outside_static_walk"] == 1 and res.meta["stop_reason"] == "finished"


def test_static_regions_always_stay():
    res = extract_agent([CFG], Script([report()]))
    assert {r.location.line_start for r in extract(CFG)} <= {r.location.line_start for r in res.regions}
    assert res.meta["added_regions"] == 1


@pytest.mark.parametrize("bad,reason", [
    (report(line=33, code="if warm:"), "code quote"),
    (report(line=9999), "line outside"),
    (report(cond="invented_name"), "names not in the function"),
    (report(outcome="crash"), "unknown outcome"),
    (report(outcome="mechanism"), "mechanism"),
    (report(cond="otherwise"), "condition must name"),
    (report(file="../evil.py"), "outside the repository"),
    (report(file="missing.py"), "no such path"),
    (report(file="./hybrid_module.py"), "relative to the repository root"),
])
def test_bad_reports_are_rejected_and_the_model_is_told(bad, reason):
    script = Script([bad])
    res = extract_agent([CFG], script)
    assert not [r for r in res.regions if r.region_id.startswith("D")]
    assert reason in res.meta["rejected_items"][0]["_reason"]
    assert res.meta["hallucination_rate"] == 1.0
    assert "rejected" in script.seen[1][-1]["content"]


def test_only_python_files_can_be_reported(tmp_path):
    (tmp_path / "m.py").write_text("def f(a):\n    assert a\n")
    (tmp_path / "conf.yaml").write_text("mode: fast\n")
    cfg = ExtractConfig(repo=tmp_path, entry="m.py::f", artifact_id="t")
    res = extract_agent([cfg], Script([report(file="conf.yaml", line=1, code="mode: fast", cond="mode")]))
    assert res.meta["rejected_items"][0]["_reason"] == "only Python files can be reported"


def test_repeating_a_location_is_a_duplicate_not_a_new_region():
    res = extract_agent([CFG], Script([report()], [report()],
                                      [report(line=33, code="assert x is not None", cond="x is None", outcome="reject")]))
    assert res.meta["added_regions"] == 1 and res.meta["duplicates"] == 2


def test_old_tool_outputs_are_removed_from_the_prompt():
    script = Script(*[[call("grep", cid=str(i), pattern="def ")] for i in range(KEEP_TOOL_OUTPUTS + 3)])
    extract_agent([CFG], script)
    tools = [m["content"] for m in script.seen[-1] if m["role"] == "tool"]
    assert sum("output removed" in t for t in tools) == 3
    assert sum("def top" in t for t in tools) == KEEP_TOOL_OUTPUTS


def test_step_budget_ends_the_run():
    script = Script(*[[call("list_dir", cid=str(i))] for i in range(20)])
    res = extract_agent([CFG], script, max_steps=3)
    assert res.meta["stop_reason"] == "max_steps" and res.meta["steps"] == 3


def test_token_budget_asks_for_a_last_report_then_stops():
    class Costly(Script):
        def chat(self, messages, tools):
            self.prompt_tokens += 100
            return super().chat(messages, tools)

    script = Costly(*[[call("list_dir", cid=str(i))] for i in range(20)])
    res = extract_agent([CFG], script, max_total_tokens=100)
    assert res.meta["stop_reason"] == "token_budget" and res.meta["steps"] == 2
    assert "Budget used up" in script.seen[-1][-1]["content"]


def test_api_failure_keeps_earlier_reports_and_is_recorded():
    boom = RuntimeError("server down")
    res = extract_agent([CFG], Script([report()], boom, boom, boom))
    assert res.meta["added_regions"] == 1 and res.meta["stop_reason"] == "llm_failure"
    assert "server down" in res.meta["failed_calls"][0]["error"]


def test_a_transient_failure_is_retried():
    res = extract_agent([CFG], Script(RuntimeError("blip"), [report()]))
    assert res.meta["added_regions"] == 1 and not res.meta["failed_calls"]


def test_a_model_that_stops_calling_tools_is_nudged_once():
    res = extract_agent([CFG], Script([], []))
    assert res.meta["stop_reason"] == "no_tool_call" and res.meta["steps"] == 2


def test_malformed_tool_arguments_go_back_to_the_model():
    bad = {"id": "x", "type": "function", "function": {"name": "read_file", "arguments": "{not json"}}
    script = Script([bad])
    res = extract_agent([CFG], script)
    assert res.meta["stop_reason"] == "finished"
    assert script.seen[1][-1]["content"].startswith("error:")


def test_enclosing_function_is_decided_by_code():
    src = "class A:\n    def f(self):\n        def g():\n            return 1\n        return g\n\nX = 1\n"
    assert enclosing_function("m.py", src, 4).qual == "A.f.g"
    assert enclosing_function("m.py", src, 5).qual == "A.f"
    assert enclosing_function("m.py", src, 7).qual == "<module>"


def test_prompt_lists_the_static_regions_and_entries():
    script = Script()
    AgentExplorer([CFG], script, paper="Some Paper").run()
    user = script.seen[0][1]["content"]
    assert "Some Paper" in user and f"{FILE}::top" in user and "not (x is not None)" in user


def test_rereading_returns_nothing_unless_forced_and_forcing_is_limited(tmp_path):
    (tmp_path / "a.py").write_text("\n".join(f"x{i} = {i}" for i in range(20)))
    tools = RepoTools(tmp_path)
    assert "5: x4" in tools.read_file("a.py", 1, 10)
    assert "already read" in tools.read_file("a.py", 2, 5) and tools.refused_rereads == 1
    assert "11: x10" in tools.read_file("a.py", 5, 11)  # partly new lines are fine
    for _ in range(MAX_FORCED_REREADS):
        assert "2: x1" in tools.read_file("a.py", 2, 3, force=True)
    assert "No forced rereads are left" in tools.read_file("a.py", 2, 3, force=True)


def test_long_lines_stop_a_read_early_and_only_shown_lines_count_as_read(tmp_path):
    (tmp_path / "a.py").write_text("\n".join("# " + "y" * 290 for _ in range(100)))
    tools = RepoTools(tmp_path)
    first = tools.read_file("a.py")
    assert "stopped at line" in first and len(first) <= MAX_TOOL_CHARS + 100
    last = int(first.rsplit("stopped at line ", 1)[1].split(";")[0])
    assert last < 100 and "already read" not in tools.read_file("a.py", last + 1, last + 1)


def test_notes_stay_in_the_conversation_and_progress_reminders_arrive():
    turns = [[call("note", text="remember x")], *[[call("list_dir", cid=str(i))] for i in range(REMIND_EVERY)]]
    script = Script(*turns)
    extract_agent([CFG], script)
    history = json.dumps(script.seen[-1])
    assert "remember x" in history and "Progress: step 10" in history
