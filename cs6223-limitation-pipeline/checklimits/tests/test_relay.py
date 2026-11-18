"""The relay in unbound mode against a fake upstream: the real key is added, the client's header is dropped,
and an upstream 502 is retried."""
import json
import threading
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

from checklimits import relay


def start_upstream(statuses):
    seen = []

    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            seen.append(self.headers.get("Authorization"))
            code = statuses.pop(0) if statuses else 200
            body = json.dumps({"ok": code == 200}).encode()
            self.send_response(code)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *a):
            pass

    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, seen


def test_relay_swaps_key_and_retries_502(monkeypatch, tmp_path):
    monkeypatch.setattr(relay.time, "sleep", lambda s: None)
    up, seen = start_upstream([502, 200])
    cfg = relay.RelayConfig(f"http://127.0.0.1:{up.server_port}/v1", "REALKEY", iface="", log_path=str(tmp_path / "log"))
    srv = relay.serve(cfg, "127.0.0.1", 0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{srv.server_port}/v1/models",
                                     headers={"Authorization": "Bearer placeholder"})
        with urllib.request.urlopen(req, timeout=10) as r:
            assert r.status == 200 and json.load(r) == {"ok": True}
    finally:
        srv.shutdown()
        up.shutdown()
    assert seen == ["Bearer REALKEY", "Bearer REALKEY"]          # first attempt 502, second 200
    assert "REALKEY" not in (tmp_path / "log").read_text()
