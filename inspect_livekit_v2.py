import inspect
from livekit.agents import AgentSession

print("Dir:", dir(AgentSession))
try:
    print("Start Args:", AgentSession.start.__code__.co_varnames)
except Exception as e:
    print("Error getting args:", e)

sig = inspect.signature(AgentSession.start)
print(f"Signature: {sig}")
