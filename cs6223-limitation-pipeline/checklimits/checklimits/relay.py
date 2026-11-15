"""Local relay in front of SoCLaaS (PLAN.md D5, section 4 item 1).

Why it exists: the code agent and the repository code it runs must never see the real
API key. The agent talks to http://127.0.0.1:<port>/v1 with a fake key. This relay
drops the client's Authorization header, adds the real one on the outbound request,
and binds the outbound socket to eth0 (SO_BINDTODEVICE plus the interface's current
address; the default route goes out of eth1 and cannot reach SoCLaaS).

Standard library only. Configuration comes from the environment:
  SOCLAAS_BASE_URL   upstream base, e.g. https://host/v1
  SOCLAAS_API_KEY    real key (read here only, never logged)

The log records method, path, status, duration and model name. It never records
request headers or request bodies.

Run:  python -m checklimits.relay --port 8787 [--log relay.log] [--iface eth0]
"""
from __future__ import annotations

import argparse
import http.client
import json
import os
import re
import socket
import ssl
import subprocess
import sys
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOP_BY_HOP = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te",
    "trailers", "transfer-encoding", "upgrade",
}
# Request headers that are never forwarded. Host and length are rebuilt; the client's
# Authorization is discarded on purpose (it is a fake key).
DROP_REQUEST = HOP_BY_HOP | {"host", "authorization", "content-length", "accept-encoding"}
DROP_RESPONSE = HOP_BY_HOP | {"content-length", "content-encoding"}
MAX_BODY = 32 * 1024 * 1024
UPSTREAM_TIMEOUT = 300
_SAFE_MODEL = re.compile(r"^[A-Za-z0-9._:/-]{1,100}$")


def iface_ipv4(iface: str) -> str:
    """Current IPv4 address of `iface`, read at run time (never hard-coded)."""
    out = subprocess.run(
        ["ip", "-4", "-o", "addr", "show", iface],
        capture_output=True, text=True, timeout=10, check=True,
    ).stdout
    m = re.search(r"inet (\d+\.\d+\.\d+\.\d+)/", out)
    if not m:
        raise RuntimeError(f"no IPv4 address on {iface}")
    return m.group(1)


def _bound_socket(host: str, port: int, iface: str, src: str, timeout: float) -> socket.socket:
    """TCP socket bound to `iface` and to its address `src`, then connected.

    Binding only the source address is not enough on this machine: the default route
    goes out of eth1, and a packet with an eth0 source address sent through eth1 is
    dropped (measured: bind-address only times out, SO_BINDTODEVICE connects in 40 ms).
    SO_BINDTODEVICE works without root on this kernel.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.settimeout(timeout)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, iface.encode())
        s.bind((src, 0))
        addr = socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_STREAM)[0][4]
        s.connect(addr)
        return s
    except Exception:
        s.close()
        raise


class _BoundMixin:
    iface = "eth0"
    src = ""

    def connect(self):  # type: ignore[override]
        self.sock = _bound_socket(self.host, self.port, self.iface, self.src, self.timeout)
        if isinstance(self, http.client.HTTPSConnection):
            self.sock = ssl.create_default_context().wrap_socket(self.sock, server_hostname=self.host)


class _BoundHTTP(_BoundMixin, http.client.HTTPConnection):
    pass


class _BoundHTTPS(_BoundMixin, http.client.HTTPSConnection):
    pass


class RelayConfig:
    def __init__(self, base_url: str, api_key: str, iface: str = "eth0",
                 log_path: str | None = None, source_ip: str | None = None):
        p = urllib.parse.urlparse(base_url)
        if p.scheme not in ("http", "https") or not p.hostname:
            raise ValueError("SOCLAAS_BASE_URL must be an http(s) URL")
        self.scheme = p.scheme
        self.host = p.hostname
        self.port = p.port or (443 if p.scheme == "https" else 80)
        self.base_path = p.path.rstrip("/")  # e.g. "/v1"
        self.api_key = api_key
        self.iface = iface
        self.source_ip = source_ip
        self.log_path = log_path
        self._log_lock = threading.Lock()

    def log(self, method: str, path: str, status: int, ms: int, model: str) -> None:
        # Deliberately only these five fields. No headers, no body.
        safe_path = re.sub(r"[^\x21-\x7e]", "?", path)[:200]
        line = f"{time.strftime('%Y-%m-%dT%H:%M:%S')} {method} {safe_path} {status} {ms}ms model={model}\n"
        with self._log_lock:
            if self.log_path:
                with open(self.log_path, "a", encoding="utf-8") as f:
                    f.write(line)
            else:
                sys.stderr.write(line)
                sys.stderr.flush()


def make_handler(cfg: RelayConfig):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"
        server_version = "checklimits-relay"

        def log_message(self, *a, **k):  # silence the default stderr logger
            pass

        def _send_json(self, status: int, obj: dict) -> None:
            body = json.dumps(obj).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _handle(self) -> None:
            t0 = time.monotonic()
            model, status = "-", 502
            try:
                path = self.path
                parsed = urllib.parse.urlsplit(path)
                if not parsed.path.startswith("/v1/") or ".." in parsed.path:
                    status = 404
                    self._send_json(404, {"error": "only /v1/* is relayed"})
                    return
                n = int(self.headers.get("Content-Length") or 0)
                if n > MAX_BODY:
                    status = 413
                    self._send_json(413, {"error": "body too large"})
                    return
                body = self.rfile.read(n) if n else b""
                if body:
                    try:
                        m = json.loads(body).get("model")
                        if isinstance(m, str) and _SAFE_MODEL.match(m):
                            model = m
                    except Exception:
                        pass
                up_path = cfg.base_path + parsed.path[len("/v1"):]
                if parsed.query:
                    up_path += "?" + parsed.query
                headers = {k: v for k, v in self.headers.items() if k.lower() not in DROP_REQUEST}
                headers["Authorization"] = f"Bearer {cfg.api_key}"
                headers["Host"] = cfg.host
                headers["Accept-Encoding"] = "identity"
                if body:
                    headers["Content-Length"] = str(len(body))
                src = cfg.source_ip or iface_ipv4(cfg.iface)
                conn = (_BoundHTTPS if cfg.scheme == "https" else _BoundHTTP)(
                    cfg.host, cfg.port, timeout=UPSTREAM_TIMEOUT)
                conn.iface, conn.src = cfg.iface, src
                try:
                    conn.request(self.command, up_path, body=body or None, headers=headers)
                    resp = conn.getresponse()
                    status = resp.status
                    self.send_response(resp.status)
                    for k, v in resp.getheaders():
                        if k.lower() not in DROP_RESPONSE:
                            self.send_header(k, v)
                    self.send_header("Transfer-Encoding", "chunked")
                    self.end_headers()
                    # read1 returns as soon as some bytes are available, so SSE events
                    # are forwarded as they arrive instead of being buffered.
                    while True:
                        chunk = resp.read1(8192)
                        if not chunk:
                            break
                        self.wfile.write(b"%x\r\n" % len(chunk) + chunk + b"\r\n")
                        self.wfile.flush()
                    self.wfile.write(b"0\r\n\r\n")
                    self.wfile.flush()
                finally:
                    conn.close()
            except (BrokenPipeError, ConnectionResetError):
                pass
            except Exception:
                # Generic message only: exception text could echo request details.
                try:
                    self._send_json(502, {"error": "upstream request failed"})
                except Exception:
                    pass
            finally:
                cfg.log(self.command, urllib.parse.urlsplit(self.path).path, status,
                        int((time.monotonic() - t0) * 1000), model)

        do_GET = do_POST = do_PUT = do_DELETE = do_PATCH = _handle

    return Handler


def serve(cfg: RelayConfig, host: str = "127.0.0.1", port: int = 8787) -> ThreadingHTTPServer:
    srv = ThreadingHTTPServer((host, port), make_handler(cfg))
    srv.daemon_threads = True
    return srv


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--port", type=int, default=8787)
    ap.add_argument("--iface", default="eth0")
    ap.add_argument("--log", default=None, help="log file (default: stderr)")
    a = ap.parse_args(argv)
    base, key = os.environ.get("SOCLAAS_BASE_URL"), os.environ.get("SOCLAAS_API_KEY")
    if not base or not key:
        print("SOCLAAS_BASE_URL and SOCLAAS_API_KEY must be set in the environment", file=sys.stderr)
        return 2
    cfg = RelayConfig(base, key, iface=a.iface, log_path=a.log)
    srv = serve(cfg, "127.0.0.1", a.port)
    print(f"relay listening on 127.0.0.1:{a.port} (outbound via {a.iface})", file=sys.stderr)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
