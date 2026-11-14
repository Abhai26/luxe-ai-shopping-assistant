"""Query helpers, password hashing, and admin gating."""
import re

import pytest
from fastapi import HTTPException

from backend import auth
from backend.utils.mongo import case_insensitive_contains, case_insensitive_exact, price_range_filter
from backend.utils.passwords import hash_password, verify_password


def test_regex_input_is_escaped_against_regex_injection():
    # LLM-chosen keywords go straight into a Mongo $regex; metacharacters must be literal.
    frag = case_insensitive_contains(".*")
    assert frag == {"$regex": re.escape(".*"), "$options": "i"}
    assert case_insensitive_exact("men")["$regex"] == "^men$"


@pytest.mark.parametrize(
    "lo,hi,expected",
    [(None, None, {}), (None, 2000, {"$lte": 2000}), (500, 2000, {"$gte": 500, "$lte": 2000})],
)
def test_price_range_filter(lo, hi, expected):
    assert price_range_filter(lo, hi) == expected


def test_password_hashing_roundtrip():
    h = hash_password("hunter2")
    assert h != "hunter2"
    assert verify_password("hunter2", h) and not verify_password("wrong", h)
    assert verify_password("anything", None) is False  # Google-only account


class FakeUsers:
    def __init__(self, docs):
        self.docs = docs

    def find_one(self, q):
        return next((d for d in self.docs if d["email"] == q["email"]), None)


def test_admin_gate(monkeypatch):
    monkeypatch.setattr(auth, "users_collection", FakeUsers([
        {"email": "boss@luxe.com", "is_admin": True},
        {"email": "shopper@luxe.com"},
    ]))
    assert auth.require_admin("  Boss@LUXE.com ") == "  Boss@LUXE.com "
    for who in ("shopper@luxe.com", None, "nobody@x.com"):
        with pytest.raises(HTTPException) as exc:
            auth.require_admin(who)
        assert exc.value.status_code == 403
