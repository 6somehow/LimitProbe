"""SoCLaaS OpenAI-compatible chat client with streaming, deadline and full archiving."""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from pathlib import Path

from .util import dump, sha


class ProviderError(RuntimeError):
    pass


def collect_stream(lines):
    """Reconstruct a chat-completion message from SSE data lines."""
    message = {"role": "assistant", "content": ""}
    calls = {}
    model = finish = usage = None
    for raw in lines:
        if not raw.startswith(b"data:"):
            continue
        data = raw[5:].strip()
        if data == b"[DONE]":
            break
        chunk = json.loads(data)
        if chunk.get("error"):
            raise ProviderError(str(chunk["error"]))
        model = chunk.get("model") or model
        if chunk.get("usage"):
            usage = chunk["usage"]
        for choice in chunk.get("choices") or []:
            finish = choice.get("finish_reason") or finish
            delta = choice.get("delta") or {}
            for field in ("content", "reasoning", "reasoning_content", "reasoning_details"):
                value = delta.get(field)
                if isinstance(value, str):
                    message[field] = message.get(field, "") + value
                elif isinstance(value, list):
                    message.setdefault(field, []).extend(value)
            for part in delta.get("tool_calls") or []:
                call = calls.setdefault(part["index"], {"type": "function",
                                                         "function": {"name": "", "arguments": ""}})
                if part.get("id"):
                    call["id"] = part["id"]
                for field, value in (part.get("function") or {}).items():
                    call["function"][field] += value
    if calls:
        message["tool_calls"] = [calls[i] for i in sorted(calls)]
    return {"model": model, "usage": usage or {},
            "choices": [{"message": message, "finish_reason": finish or "stop"}]}


class Client:
    def __init__(self, key: str, base: str, archive: Path, model: str = "x-test-2",
                 max_tokens: int = 32768, timeout: int = 600, retries: int = 1):
        self.key = key
        self.base = base.rstrip("/")
        self.archive = Path(archive)
        self.model = model
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.retries = retries
        self.requests = 0
        self.tokens = 0
        self.usage: list[dict] = []

    def chat(self, messages, tools=None, tool_choice=None, max_tokens=None, thinking=True) -> dict:
        self.requests += 1
        number = self.requests
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens or self.max_tokens,
            "stream": True,
            "stream_options": {"include_usage": True},
        }
        if thinking:
            payload["thinking"] = {"type": "enabled"}
            payload["reasoning_effort"] = "max"
        else:
            payload["temperature"] = 0
            payload["reasoning_effort"] = "none"
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = tool_choice or "auto"
        dump(self.archive / f"request-{number:02d}.json", payload)
        body = None
        last = None
        for attempt in range(self.retries + 1):
            request = urllib.request.Request(
                self.base + "/chat/completions",
                data=json.dumps(payload).encode(),
                headers={"Authorization": "Bearer " + self.key,
                         "Content-Type": "application/json",
                         "Accept": "text/event-stream"},
            )
            start = time.time()
            capture = self.archive / f"response-{number:02d}.sse"
            try:
                with urllib.request.urlopen(request, timeout=120) as response, capture.open("wb") as log:
                    for line in response:
                        log.write(line)
                        if time.time() - start > self.timeout:
                            raise ProviderError(f"deadline exceeded after {self.timeout}s")
                body = collect_stream(capture.read_bytes().splitlines())
                break
            except (urllib.error.URLError, TimeoutError, ConnectionError, ProviderError,
                    json.JSONDecodeError) as exc:
                last = exc
                if attempt < self.retries:
                    time.sleep(3)
        if body is None:
            raise ProviderError(f"transport failed after retries: {last}")
        dump(self.archive / f"response-{number:02d}.json", body)
        choice = (body.get("choices") or [{}])[0]
        usage = body.get("usage") or {}
        self.tokens += usage.get("total_tokens") or 0
        row = {
            "request": number,
            "elapsed_seconds": round(time.time() - start, 2),
            "model": body.get("model"),
            "finish_reason": choice.get("finish_reason"),
            "usage": usage,
            "prompt_sha256": sha(json.dumps(messages, ensure_ascii=False).encode()),
        }
        self.usage.append(row)
        return {
            "number": number,
            "message": choice.get("message") or {},
            "finish_reason": choice.get("finish_reason"),
            "usage": usage,
            "model": body.get("model"),
            "elapsed_seconds": row["elapsed_seconds"],
        }


def assistant_message(message: dict) -> dict:
    out = {"role": "assistant", "content": message.get("content") or ""}
    if message.get("tool_calls"):
        out["tool_calls"] = message["tool_calls"]
    for key in ("reasoning", "reasoning_content", "reasoning_details"):
        if message.get(key):
            out[key] = message[key]
    return out
