"""Offline test setup: dummy keys so the agent/guardrail clients can be
constructed; nothing in these tests talks to Groq or MongoDB."""
import os

os.environ.setdefault("GROQ_API_KEY", "test-key")
os.environ.setdefault("MONGO_URI", "mongodb://localhost:27017")
os.environ["PORTKEY_API_KEY"] = ""
os.environ.setdefault("LOGFIRE_IGNORE_NO_CONFIG", "1")
