"""One entry point for a new paper: check the setup, start the model relay, run steps 1 to 4, run the tests.

    python -m pipeline doctor [<id>] [--paper-side] [--agent] [--live]     check the setup only
    python -m pipeline e2e <id> --pdf P [--run-paper-side] [--run-agent]    check, relay, run, test

All configuration comes from environment variables (or the `.env` file in the pipeline root; the environment wins):

  SOCLAAS_API_KEY     the real key. Only the relay process receives it; every other process gets a placeholder.
  SOCLAAS_BASE_URL    upstream base URL of the model service, for example https://host/v1
  PIPELINE_MODEL      model id the pipeline records and caches answers under (default x-test-2; the study's
                      model, so changing it regenerates every cached LLM answer). SOCLAAS_MODEL is not used.
  SOCLAAS_IFACE       network interface the relay binds its outgoing connections to (default eth0);
                      set it empty to use the ordinary route
  SOCLAAS_RELAY_PORT  not configurable: the code agent's sandbox config expects 127.0.0.1:8787

`doctor` never prints a value of SOCLAAS_API_KEY. Every check says ok, warn or FAIL; any FAIL stops `e2e`
before a model call or a git clone is made.
"""

from __future__ import annotations

import os
import re
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional
from urllib.parse import urlparse

from pipeline import run as P

RELAY_HOST, RELAY_PORT = "127.0.0.1", 8787
RELAY_URL = f"http://{RELAY_HOST}:{RELAY_PORT}/v1"
PLACEHOLDER_KEY = "placeholder-not-a-secret"
OPENCODE = P.CHECKLIMITS / "scratch" / "opencode" / "node_modules" / "opencode-linux-x64" / "bin" / "opencode"
RELAY_LOG = P.CHECKLIMITS / "runs" / "relay.log"


@dataclass
class Check:
    name: str
    level: str          # ok | warn | FAIL
    detail: str

    def line(self) -> str:
        return f"  {self.level:<4}  {self.name:<22} {self.detail}"


def _mod(name: str) -> bool:
    try:
        __import__(name)
        return True
    except Exception:
        return False


def _iface_has_ipv4(iface: str) -> Optional[str]:
    """None when the interface has an IPv4 address, else the reason."""
    try:
        out = subprocess.run(["ip", "-4", "-o", "addr", "show", iface], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired) as e:
        return f"cannot run `ip`: {type(e).__name__}"
    if out.returncode != 0:
        return f"interface {iface!r} not found"
    return None if re.search(r"inet \d+\.\d+\.\d+\.\d+/", out.stdout) else f"interface {iface!r} has no IPv4 address"


def _node_major(which: Callable[[str], Optional[str]]) -> Optional[int]:
    node = which("node")
    if not node:
        return None
    try:
        v = subprocess.run([node, "--version"], capture_output=True, text=True, timeout=10).stdout.strip()
        return int(v.lstrip("v").split(".")[0])
    except Exception:
        return None


def check_environment(e: dict, aid: Optional[str] = None, *, paper_side: bool = False, agent: bool = False,
                      pdf: Optional[str] = None, which: Callable[[str], Optional[str]] = shutil.which,
                      iface_check: Callable[[str], Optional[str]] = _iface_has_ipv4) -> list[Check]:
    """Static checks of the setup. `e` is the environment (see P.env()); nothing here calls the network."""
    out: list[Check] = []
    add = lambda n, l, d: out.append(Check(n, l, d))

    key = (e.get("SOCLAAS_API_KEY") or "").strip()
    if not key:
        add("SOCLAAS_API_KEY", "FAIL", "not set (environment or .env)")
    elif key == PLACEHOLDER_KEY:
        add("SOCLAAS_API_KEY", "FAIL", "is the placeholder value: set the real key")
    elif re.search(r"\s", key):
        add("SOCLAAS_API_KEY", "FAIL", "contains whitespace")
    else:
        add("SOCLAAS_API_KEY", "ok", f"set ({len(key)} characters, not shown)")

    base = (e.get("SOCLAAS_BASE_URL") or "").strip()
    u = urlparse(base)
    if not base:
        add("SOCLAAS_BASE_URL", "FAIL", "not set, for example https://host/v1")
    elif u.scheme not in ("http", "https") or not u.hostname:
        add("SOCLAAS_BASE_URL", "FAIL", f"not an http(s) URL: {base!r}")
    elif u.hostname in (RELAY_HOST, "localhost") and (u.port or 80) == RELAY_PORT:
        add("SOCLAAS_BASE_URL", "FAIL", "points at the local relay itself: set the upstream URL "
            "(the e2e command points the child processes at the relay)")
    elif not u.path.rstrip("/").endswith("/v1"):
        add("SOCLAAS_BASE_URL", "warn", f"{base} does not end in /v1")
    else:
        add("SOCLAAS_BASE_URL", "ok", base)

    model = e.get("PIPELINE_MODEL") or "x-test-2"
    add("PIPELINE_MODEL", "ok" if model == "x-test-2" else "warn",
        model if model == "x-test-2" else f"{model}: not the study's x-test-2; cached LLM answers will not be reused")

    iface = e.get("SOCLAAS_IFACE", "eth0")
    if not iface:
        add("SOCLAAS_IFACE", "ok", "empty: ordinary routing")
    else:
        why = iface_check(iface)
        add("SOCLAAS_IFACE", "FAIL" if why else "ok", why or f"{iface} has an IPv4 address")

    add("python", "ok" if sys.version_info >= (3, 10) else "FAIL",
        f"{sys.version.split()[0]} at {sys.executable}")
    missing = [m for m in ("pydantic", "openai", "dotenv", "fitz") if not _mod(m)]
    add("python packages", "FAIL" if missing else "ok",
        ("missing " + ", ".join(missing) + ': pip install -e ".[llm,verify,dev]"') if missing else
        "pydantic, openai, dotenv, fitz")
    add("git", "ok" if which("git") else "FAIL", which("git") or "not on PATH")

    if paper_side:
        miss = [m for m in ("paperprobe", "pypdf") if not _mod(m)]
        add("paper-side packages", "FAIL" if miss else "ok",
            ("missing " + ", ".join(miss) + ": python -m pipeline setup-paperside") if miss else "paperprobe, pypdf")
        major = _node_major(which)
        add("node", "ok" if major and major >= 20 else "FAIL",
            f"v{major}" if major and major >= 20 else "node >= 20 not found on PATH")
        add("pi agent modules", "ok" if (P.PAPERSIDE / "tools/pi-mechanism-agent/node_modules").is_dir() else "FAIL",
            "installed" if (P.PAPERSIDE / "tools/pi-mechanism-agent/node_modules").is_dir()
            else "missing: python -m pipeline setup-paperside")
    if agent:
        add("bwrap", "ok" if which("bwrap") else "FAIL", which("bwrap") or "not on PATH (agent sandbox)")
        add("opencode", "ok" if OPENCODE.is_file() else "FAIL",
            "installed" if OPENCODE.is_file() else f"missing: {OPENCODE.relative_to(P.ROOT)}")

    if aid:
        try:
            P_ = P.Paths(aid)
        except P.StageError:
            add("artifact", "FAIL", f"no data/*/artifact.json with artifact_id {aid!r}: "
                f"python -m pipeline init --id {aid} ...")
        else:
            d = P_.art
            ok = bool(re.fullmatch(r"[0-9a-f]{40}", d.get("commit", ""))) and bool(d.get("entry_points"))
            add("artifact", "ok" if ok else "FAIL",
                f"{d.get('repo_url')} @ {d.get('commit', '')[:10]}, {len(d.get('entry_points', []))} entry point(s)"
                if ok else "commit must be 40 hex characters and entry_points must not be empty")
            url = P.arxiv_pdf_url(d.get("paper_url", ""))
            outputs = [(P_.handoff / "paper_side.json"), P_.verify3b, P_.lims]
            if P_.pdf.is_file():
                add("paper pdf", "ok", P._rel(P_.pdf))
            elif pdf and Path(pdf).is_file():
                add("paper pdf", "ok", pdf)
            elif url:
                add("paper pdf", "ok", f"not on disk: will be downloaded from {url}")
            elif all(o.is_file() for o in outputs):
                add("paper pdf", "ok", "not on disk and not needed: paper-side, 3b and code outputs exist")
            else:
                add("paper pdf", "FAIL", f"missing and {d.get('paper_url')} is not an arXiv link: pass --pdf <file>")
    free = shutil.disk_usage(P.ROOT).free / 2**30
    add("disk", "ok" if free >= 10 else "warn", f"{free:.0f} GiB free (provisioning a venv needs a few)")
    return out


def relay_up() -> bool:
    try:
        with socket.create_connection((RELAY_HOST, RELAY_PORT), timeout=2):
            return True
    except OSError:
        return False


def probe_models(timeout: float = 30) -> tuple[bool, str]:
    """GET /v1/models through the relay: proves the key, the URL and the route all work."""
    req = urllib.request.Request(RELAY_URL + "/models", headers={"Authorization": "Bearer " + PLACEHOLDER_KEY})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status == 200, f"HTTP {r.status}"
    except urllib.error.HTTPError as ex:
        return False, f"HTTP {ex.code} (a 401 or 403 means the key is wrong)"
    except Exception as ex:
        return False, f"{type(ex).__name__}: the service is not reachable (check SOCLAAS_BASE_URL and SOCLAAS_IFACE)"


class Relay:
    """Start the relay (the only process that sees the real key) unless one already answers on the port."""

    def __init__(self, e: dict):
        self.e, self.proc, self.started = e, None, False

    def __enter__(self) -> "Relay":
        if relay_up():
            print(f"  relay already running on {RELAY_HOST}:{RELAY_PORT}; using it", flush=True)
            return self
        RELAY_LOG.parent.mkdir(parents=True, exist_ok=True)
        renv = dict(os.environ)
        renv.update(SOCLAAS_API_KEY=self.e["SOCLAAS_API_KEY"], SOCLAAS_BASE_URL=self.e["SOCLAAS_BASE_URL"])
        cmd = [sys.executable, "-m", "checklimits.relay", "--port", str(RELAY_PORT), "--log", str(RELAY_LOG),
               "--iface", self.e.get("SOCLAAS_IFACE", "eth0")]
        # cwd must be checklimits/ (from the pipeline root `-m checklimits` resolves to the directory)
        self.proc = subprocess.Popen(cmd, cwd=P.CHECKLIMITS, env=renv, stdout=subprocess.DEVNULL,
                                     stderr=open(P.CHECKLIMITS / "runs" / "relay.stderr", "w"))
        for _ in range(50):
            if relay_up():
                self.started = True
                print(f"  relay started on {RELAY_HOST}:{RELAY_PORT} (pid {self.proc.pid}, log {P._rel(RELAY_LOG)})",
                      flush=True)
                return self
            if self.proc.poll() is not None:
                break
            time.sleep(0.2)
        raise P.StageError("the relay did not start; see checklimits/runs/relay.stderr")

    def __exit__(self, *exc) -> None:
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.proc.kill()
            print("  relay stopped", flush=True)


def point_children_at_relay() -> None:
    """From here on, every process this one starts talks to the relay and holds only a placeholder key."""
    os.environ["SOCLAAS_BASE_URL"] = RELAY_URL
    os.environ["SOCLAAS_API_KEY"] = PLACEHOLDER_KEY
    # P.env() reads .env with setdefault, so the real key in .env can no longer win


def report(checks: list[Check]) -> int:
    for c in checks:
        print(c.line())
    n = sum(c.level == "FAIL" for c in checks)
    print(f"  {len(checks) - n}/{len(checks)} checks pass" + (f", {n} FAIL" if n else ""))
    return n


def doctor(a) -> None:
    e = P.env()
    checks = check_environment(e, a.artifact_id, paper_side=a.paper_side, agent=a.agent, pdf=getattr(a, "pdf", None))
    n = report(checks)
    if n == 0 and a.live:
        with Relay(e):
            ok, detail = probe_models()
        print(f"  {'ok' if ok else 'FAIL':<4}  {'live call':<22} GET /models through the relay: {detail}")
        n += not ok
    if n:
        sys.exit("stopped: fix the FAIL lines above")
    print("ready" + ("" if a.live else " (static checks only; add --live to call the service)"))


def e2e(a) -> None:
    """Check, start the relay, run steps 1 to 4 (`run`), run the tests (`test`, with --provision)."""
    e = P.env()
    print("[check] setup")
    if report(check_environment(e, a.artifact_id, paper_side=a.run_paper_side, agent=a.run_agent, pdf=a.pdf)):
        sys.exit("stopped: fix the FAIL lines above (nothing was run)")
    with Relay(e):
        ok, detail = probe_models()
        print(f"  {'ok' if ok else 'FAIL':<4}  live call              GET /models through the relay: {detail}")
        if not ok:
            sys.exit("stopped: the model service did not answer through the relay (nothing was run)")
        point_children_at_relay()
        a.model = a.model or e.get("PIPELINE_MODEL") or "x-test-2"
        P.run(a.artifact_id, a)
        a.provision = True
        out = P.test(a.artifact_id, a)
    print(f"[done] {a.artifact_id}: {P._rel(P.Paths(a.artifact_id).report)}")
    print(f"  tested {out['counts'].get('tested')} of {out.get('n_input')} Findings")
