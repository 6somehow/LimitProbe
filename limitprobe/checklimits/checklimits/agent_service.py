"""Run `cl` for a sandboxed agent OUTSIDE its sandbox (clean blind mode, S5b).

In a blind run the agent's sandbox does not contain the harness at all: the package directory is an empty tmpfs and the
rule documents are hidden. `agent/cl` there is a thin client (`agent/cl_client.py`) that sends the command over a Unix
socket to this service, which runs the real command and returns its output. The agent therefore sees exactly what the
harness prints (task text, lint messages, the run report with `next_steps`) and nothing about how it is computed.

What the service runs is limited: only `task`, `init`, `lint` and `run`; only the flags the agent instructions use;
paths must stay inside the run directory (`--attempt`, `--out`) or the step 4 / data inputs. `run` executes the agent's
driver, so the command runs inside the same bubblewrap sandbox as the agent (same hidden paths and read-only file
system), with the harness source visible to that process. The agent cannot read it through a shell. A driver that
printed harness source would defeat the blindness; the agent is not assumed to attack the sandbox (agent_loop.py).
"""
from __future__ import annotations

import json
import os
import re
import shutil
import socket
import socketserver
import subprocess
import sys
import threading
from pathlib import Path
from typing import Callable, Optional

from .models import PIPELINE_ROOT, PROJECT_ROOT

ALLOWED = ("task", "init", "lint", "run")
FLAGS = {"task": {"--findings-file": "in", "--data-dir": "in"},
         "init": {"--findings-file": "in", "--data-dir": "in", "--out": "work"},
         "lint": {"--attempt": "work"},
         "run": {"--attempt": "work", "--out": "out", "--fast": None}}
SOCK_IN_SANDBOX = "/tmp/cl/sock"
TIMEOUT_S = 1800


def service_dir(run_dir: Path) -> Path:
    """Short path (AF_UNIX allows about 100 characters) that is bind-mounted into the sandbox as /tmp/cl."""
    return Path(f"/tmp/clsvc-{os.getuid()}-{run_dir.name}")


class BadRequest(ValueError):
    pass


def sanitize(argv: list[str], cwd: str, run_dir: Path) -> list[str]:
    """Validated argv with absolute paths, or BadRequest."""
    if not argv or argv[0] not in ALLOWED:
        raise BadRequest(f"command must be one of {', '.join(ALLOWED)}")
    cmd, rest = argv[0], argv[1:]
    spec = FLAGS[cmd]
    work, out = (run_dir / "workspace").resolve(), (run_dir / "out").resolve()
    res = [cmd]
    positional = 0
    i = 0
    seen: set[str] = set()
    while i < len(rest):
        a = rest[i]
        if a in spec:
            seen.add(a)
            kind = spec[a]
            res.append(a)
            if kind is None:
                i += 1
                continue
            if i + 1 >= len(rest):
                raise BadRequest(f"{a} needs a value")
            v = rest[i + 1]
            p = (Path(cwd) / v) if not os.path.isabs(v) else Path(v)
            if kind == "work":
                p = p.resolve()
                if work != p and work not in p.parents:
                    raise BadRequest(f"{a} must be inside {work}")
                v = str(p)
            elif kind == "out":
                p = p.resolve()
                if out != p and out not in p.parents and work not in p.parents and p != work:
                    raise BadRequest(f"{a} must be inside {out}")
                v = str(p)
            else:                                    # an input of the pipeline: relative to the pipeline root, no escapes
                if os.path.isabs(v) or ".." in Path(v).parts:
                    raise BadRequest(f"{a} must be a path relative to the pipeline root without '..'")
                if not (a == "--findings-file" and v.startswith("results/step4/")) and not (a == "--data-dir" and v.startswith("data/")):
                    raise BadRequest(f"{a} {v}: only results/step4/... and data/... are readable inputs")
            res.append(v)
            i += 2
        elif a.startswith("-"):
            raise BadRequest(f"flag {a} is not available through the service")
        else:
            positional += 1
            if cmd in ("task", "init") and positional == 1 and re.fullmatch(r"[A-Za-z0-9_.-]{1,80}", a):
                res.append(a)
            else:
                raise BadRequest(f"unexpected argument {a!r}")
            i += 1
    if cmd in ("task", "init") and positional != 1:
        raise BadRequest(f"{cmd} takes exactly one finding id")
    if cmd in ("lint", "run") and "--attempt" not in seen:
        raise BadRequest(f"{cmd} needs --attempt")
    if cmd == "init" and "--out" not in seen:
        raise BadRequest("init needs --out")
    if cmd == "run" and "--out" not in seen:
        res += ["--out", str(out)]
    return res


def default_executor(run_dir: Path) -> Callable[[list[str]], tuple[int, str, str]]:
    from .agent_loop import agent_env, sandbox_cmd

    def run(argv: list[str]) -> tuple[int, str, str]:
        env = {**agent_env(run_dir), "PYTHONPATH": str(PROJECT_ROOT)}
        env.pop("CL_SOCKET", None)
        cmd = sandbox_cmd(run_dir, [sys.executable, "-m", "checklimits", *argv], blind=False)
        try:
            p = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=TIMEOUT_S)
            return p.returncode, p.stdout, p.stderr
        except subprocess.TimeoutExpired:
            return 124, "", f"timed out after {TIMEOUT_S} s"
    return run


class ClService:
    def __init__(self, run_dir: Path, executor: Optional[Callable[[list[str]], tuple[int, str, str]]] = None) -> None:
        self.run_dir = run_dir
        self.dir = service_dir(run_dir)
        self.executor = executor or default_executor(run_dir)
        self.log: list[dict] = []
        outer = self

        class Handler(socketserver.StreamRequestHandler):
            def handle(self) -> None:
                try:
                    req = json.loads(self.rfile.readline().decode())
                    argv = sanitize(list(req["argv"]), str(req["cwd"]), outer.run_dir)
                    rc, out, err = outer.executor(argv)
                    outer.log.append({"argv": argv, "rc": rc})
                    reply = {"rc": rc, "stdout": out, "stderr": err}
                except BadRequest as e:
                    outer.log.append({"rejected": str(e)})
                    reply = {"rc": 2, "stdout": "", "stderr": f"cl: {e}\n"}
                except Exception as e:     # a broken request must not kill the service
                    reply = {"rc": 1, "stdout": "", "stderr": f"cl service error: {type(e).__name__}: {str(e)[:200]}\n"}
                self.wfile.write((json.dumps(reply) + "\n").encode())

        class Server(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
            daemon_threads = True

        shutil.rmtree(self.dir, ignore_errors=True)
        self.dir.mkdir(mode=0o700)
        self.server = Server(str(self.dir / "sock"), Handler)
        os.chmod(self.dir / "sock", 0o600)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def start(self) -> "ClService":
        self.thread.start()
        return self

    def stop(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        shutil.rmtree(self.dir, ignore_errors=True)

    def __enter__(self) -> "ClService":
        return self.start()

    def __exit__(self, *a) -> None:
        self.stop()


def call(sock_path: str, argv: list[str], cwd: str) -> dict:
    """The client side (also used by tests); agent/cl_client.py is the same thing in a stand-alone stdlib script."""
    with socket.socket(socket.AF_UNIX) as s:
        s.connect(sock_path)
        s.sendall((json.dumps({"argv": argv, "cwd": cwd}) + "\n").encode())
        data = b""
        while chunk := s.recv(65536):
            data += chunk
    return json.loads(data.decode())
