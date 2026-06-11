# my-agent

A minimal LangChain + Deep Agents starter project.

## Setup

```bash
# 1. Install dependencies
uv sync
# or: pip install -e .

# 2. Add your API key
cp .env.example .env
# then edit .env and paste your key

# 3. Run
python main.py                        # interactive chat
python main.py "what's the weather in Delhi?"   # single question
```

## Project structure

```
my-agent/
├── .env                  ← your API keys (never commit)
├── .env.example          ← template to copy from
├── pyproject.toml        ← dependencies
├── main.py               ← run this
├── agent/
│   ├── __init__.py
│   ├── prompt.py         ← system prompt (edit agent behaviour here)
│   ├── tools.py          ← add new tools here
│   ├── model.py          ← swap LLM provider here
│   └── memory.py         ← swap to DB checkpointer for production
└── tests/
    └── test_agent.py     ← smoke tests
```

## Adding a new tool

Open `agent/tools.py` and add a function with the `@tool` decorator:

```python
@tool
def search_web(query: str) -> str:
    """Search the web for a given query. Returns top results."""
    # your implementation here
    return "..."
```

Then add it to `get_tools()`:

```python
def get_tools():
    return [fetch_text_from_url, get_weather, search_web]
```

That's it — the agent will automatically know it can use the new tool.

## Running tests

```bash
python -m pytest tests/ -v
# or
python tests/test_agent.py
```
