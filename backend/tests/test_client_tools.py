"""Test de chat_with_tools via httpx.MockTransport. Exécution: backend\.venv\Scripts\python.exe -X utf8 backend\tests\test_client_tools.py"""
import asyncio
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
from axiom.claude.client import LocalAPIClient, TokenBucketRateLimiter


def _make_client(responses: list[dict]):
    """Client avec MockTransport qui sert les réponses données (dans l'ordre)."""
    def handler(request):
        if not responses:
            return httpx.Response(200, json={})
        item = responses.pop(0)
        if isinstance(item, tuple):
            status, payload = item
            return httpx.Response(status, json=payload)
        return httpx.Response(200, json=item)
    c = LocalAPIClient(api_key="test")
    c.http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    c.rate_limiter = TokenBucketRateLimiter(rpm=1000, tpm=100000)
    return c


async def test_tool_calls_parsed():
    c = _make_client([{
        "choices": [{"message": {
            "content": None,
            "tool_calls": [{
                "id": "call_1",
                "type": "function",
                "function": {"name": "web_search", "arguments": json.dumps({"query": "qtest"})},
            }],
        }}],
    }])
    resp = await c.chat_with_tools("model", "sys", [{"role": "user", "content": "u"}], tools=[{"type": "function", "function": {"name": "web_search"}}])
    assert resp["error"] is None, resp
    assert len(resp["tool_calls"]) == 1
    tc = resp["tool_calls"][0]
    assert tc["name"] == "web_search" and tc["arguments"] == {"query": "qtest"}, tc
    assert resp["content"] == ""


async def test_plain_content_when_no_tools():
    c = _make_client([{"choices": [{"message": {"content": "reponse directe", "tool_calls": None}}]}])
    resp = await c.chat_with_tools("model", "sys", [{"role": "user", "content": "u"}])
    assert resp["content"] == "reponse directe" and resp["tool_calls"] == [] and resp["error"] is None


async def test_error_surface():
    c = _make_client([(429, {"error": {"message": "rate limited"}})])
    resp = await c.chat_with_tools("model", "sys", [{"role": "user", "content": "u"}])
    assert resp["error"] is not None, resp


def run():
    asyncio.run(test_tool_calls_parsed())
    asyncio.run(test_plain_content_when_no_tools())
    asyncio.run(test_error_surface())
    print("ALL PASS")


if __name__ == "__main__":
    run()