"""Parsing of safety-model responses, using a fake Groq client."""
from types import SimpleNamespace

import pytest

from backend.chatbot import guardrails


def _client(content):
    async def create(**_):
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])

    return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))


@pytest.mark.parametrize("score,expected", [("0.97", True), ("0.5", True), ("0.12", False), ("not-a-number", False)])
async def test_prompt_guard_threshold(monkeypatch, score, expected):
    monkeypatch.setattr(guardrails, "guardrail_client", _client(score))
    assert await guardrails.is_prompt_injection("x") is expected


@pytest.mark.parametrize(
    "raw,expected",
    [
        ('{"violation": 1, "category": "jailbreak", "rationale": "r"}', True),
        ('```json\n{"violation": 0, "category": null, "rationale": "ok"}\n```', False),  # fenced output
        ("garbage", False),  # unparseable verdict fails open
    ],
)
async def test_policy_verdict_parsing(monkeypatch, raw, expected):
    monkeypatch.setattr(guardrails, "guardrail_client", _client(raw))
    assert await guardrails.violates_content_policy("x") is expected
    assert await guardrails.violates_output_policy("x") is expected
