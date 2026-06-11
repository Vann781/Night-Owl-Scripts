"""
Basic smoke tests for the agent.

Run with:
    python -m pytest tests/ -v
or just:
    python tests/test_agent.py
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Make sure the project root is on the path when running directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agent import get_model, get_tools, SYSTEM_PROMPT, get_checkpointer
from agent.tools import fetch_text_from_url, get_weather
from deepagents import create_deep_agent


# ── Tool unit tests ──────────────────────────────────────────────────────────

def test_get_weather_returns_string():
    result = get_weather.invoke({"city": "Delhi"})
    assert isinstance(result, str)
    assert "Delhi" in result
    print(f"  weather tool: {result}")


def test_fetch_invalid_url_returns_error():
    result = fetch_text_from_url.invoke({"url": "https://this-does-not-exist-xyz.com"})
    assert "failed" in result.lower() or "error" in result.lower()
    print(f"  fetch error handled: {result[:60]}")


# ── Agent integration test ───────────────────────────────────────────────────

def test_agent_responds():
    agent = create_deep_agent(
        model=get_model(),
        tools=get_tools(),
        system_prompt=SYSTEM_PROMPT,
        checkpointer=get_checkpointer(),
    )
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "Say hello in one sentence."}]},
        config={"configurable": {"thread_id": "test-hello"}},
    )
    blocks = result["messages"][-1].content_blocks
    assert blocks, "Agent returned empty response"
    print(f"  agent response: {blocks}")


def test_agent_uses_weather_tool():
    agent = create_deep_agent(
        model=get_model(),
        tools=get_tools(),
        system_prompt=SYSTEM_PROMPT,
        checkpointer=get_checkpointer(),
    )
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "What's the weather in Mumbai?"}]},
        config={"configurable": {"thread_id": "test-weather"}},
    )
    blocks = result["messages"][-1].content_blocks
    assert blocks
    print(f"  weather agent response: {blocks}")


# ── Run directly ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        test_get_weather_returns_string,
        test_fetch_invalid_url_returns_error,
        test_agent_responds,
        test_agent_uses_weather_tool,
    ]
    passed = 0
    for t in tests:
        try:
            print(f"Running {t.__name__}...")
            t()
            print(f"  ✓ passed\n")
            passed += 1
        except Exception as e:
            print(f"  ✗ FAILED: {e}\n")

    print(f"Results: {passed}/{len(tests)} passed")
