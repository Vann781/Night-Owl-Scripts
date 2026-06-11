from langgraph.checkpoint.memory import InMemorySaver


def get_checkpointer():
    """Return a memory checkpointer for the agent.

    InMemorySaver stores conversation history in RAM.
    - Good for: development, testing, single-session scripts
    - Bad for:  production (resets every time the script restarts)

    For production, swap this out for a persistent checkpointer:

        from langgraph.checkpoint.postgres import PostgresSaver
        return PostgresSaver.from_conn_string("postgresql://...")

        from langgraph.checkpoint.redis import RedisSaver
        return RedisSaver.from_conn_string("redis://...")
    """
    return InMemorySaver()
