import inspect
try:
    from livekit.agents import AgentSession
    print(f"AgentSession found: {AgentSession}")
    sig = inspect.signature(AgentSession.start)
    print(f"Signature of start: {sig}")
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")
