"""The token counter talks to the serving model's tokenizer, or says it guessed."""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from netclaw_tokens.counter import count_message_tokens, count_tokens


class _Tokenizer(BaseHTTPRequestHandler):
    """A stand-in for vLLM/SGLang's POST /tokenize."""

    reply: dict = {"count": 7}
    seen: dict = {}

    def do_POST(self):  # noqa: N802
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        _Tokenizer.seen = {"path": self.path, "body": body}
        payload = json.dumps(self.reply).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *a):  # silence
        pass


@pytest.fixture
def server(monkeypatch):
    httpd = HTTPServer(("127.0.0.1", 0), _Tokenizer)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    # deliberately WITH the /v1 suffix: that is what the config carries
    monkeypatch.setenv("NETGENIUSCLAW_MODEL_BASE_URL",
                       f"http://127.0.0.1:{httpd.server_port}/v1")
    yield httpd
    httpd.shutdown()


def test_exact_count_from_the_serving_model(server):
    _Tokenizer.reply = {"count": 7}
    t = count_tokens("some text", model="qwen/qwen3.5-4b")
    assert t.input_tokens == 7
    assert t.estimated is False


def test_v1_prefix_is_stripped(server):
    """/tokenize lives at the server ROOT, not under the OpenAI /v1 prefix."""
    count_tokens("x", model="m")
    assert _Tokenizer.seen["path"] == "/tokenize"


def test_a_tokens_array_is_accepted_too(server):
    """Servers disagree about the response shape; both are read, neither guessed."""
    _Tokenizer.reply = {"tokens": [1, 2, 3, 4, 5]}
    assert count_tokens("x", model="m").input_tokens == 5


def test_an_unrecognised_shape_falls_back_rather_than_guessing(server):
    _Tokenizer.reply = {"something_else": 99}
    t = count_tokens("abcdefgh", model="m")
    assert t.estimated is True
    assert t.input_tokens == 2          # len/4


def test_system_prompt_travels_as_a_message(server):
    """A server applying a chat template must see the system turn to count it."""
    _Tokenizer.reply = {"count": 11}
    count_message_tokens([{"role": "user", "content": "hi"}], model="m", system="be brief")
    msgs = _Tokenizer.seen["body"]["messages"]
    assert msgs[0] == {"role": "system", "content": "be brief"}
    assert msgs[1]["role"] == "user"


def test_no_server_means_estimated_never_an_exception(monkeypatch):
    monkeypatch.delenv("NETGENIUSCLAW_MODEL_BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    t = count_tokens("four chars here ok")
    assert t.estimated is True


def test_an_unreachable_server_costs_the_count_not_the_call(monkeypatch):
    """A capture failure must never propagate into the interaction it measures."""
    monkeypatch.setenv("NETGENIUSCLAW_MODEL_BASE_URL", "http://127.0.0.1:1/v1")
    t = count_tokens("hello", model="m")
    assert t.estimated is True
