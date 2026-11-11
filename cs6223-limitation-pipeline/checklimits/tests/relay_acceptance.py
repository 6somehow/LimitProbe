"""Manual acceptance check for the relay (needs network; not collected by pytest).

Start the relay first:
  set -a; . /home/somehow6/LLM_API_KEY/SoCLaaS/soclaas.env; set +a
  python -m checklimits.relay --port 8787 --log runs/relay.log &
Then:  python tests/relay_acceptance.py [port] [log]
Uses a fake key. Exits non-zero if any check fails.
"""
import json
import sys
import urllib.request

PORT = sys.argv[1] if len(sys.argv) > 1 else "8787"
LOG = sys.argv[2] if len(sys.argv) > 2 else "runs/relay.log"
BASE = f"http://127.0.0.1:{PORT}/v1"
HDR = {"Authorization": "Bearer fake-key-not-real", "Content-Type": "application/json"}
ok = True


def check(name, cond, extra=""):
    global ok
    ok &= bool(cond)
    print(("PASS" if cond else "FAIL"), name, extra)


def post(body, timeout=120):
    req = urllib.request.Request(BASE + "/chat/completions", json.dumps(body).encode(), HDR)
    return urllib.request.urlopen(req, timeout=timeout)


with urllib.request.urlopen(urllib.request.Request(BASE + "/models", headers=HDR), timeout=60) as r:
    ids = [m["id"] for m in json.load(r)["data"]]
    check("GET /v1/models -> 200 and lists x-test-2", r.status == 200 and "x-test-2" in ids, f"status={r.status} n_models={len(ids)}")

tools = [{"type": "function", "function": {"name": "get_weather", "description": "weather by city",
         "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}}}]
with post({"model": "x-test-2", "temperature": 0, "tools": tools, "tool_choice": "auto",
           "messages": [{"role": "user", "content": "What is the weather in Paris? Use the tool."}]}) as r:
    d = json.load(r)
    fr = d["choices"][0]["finish_reason"]
    check("tools request -> finish_reason=tool_calls", fr == "tool_calls", f"finish_reason={fr} model={d.get('model')}")

with post({"model": "x-test-2", "stream": True, "messages": [{"role": "user", "content": "Say hi"}]}) as r:
    lines = [ln.decode().strip() for ln in r if ln.strip()]
    check("stream ends with [DONE]", lines[-1] == "data: [DONE]", f"events={len(lines)}")

log = open(LOG).read()
check("relay log has no 'clsk_'", "clsk_" not in log)
check("relay log has no 'fake-key'", "fake-key" not in log)
print(log)
sys.exit(0 if ok else 1)
