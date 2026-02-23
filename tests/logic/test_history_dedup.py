import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from core.ai.client import EHClient
import logging

logging.basicConfig(level=logging.INFO)

def test_history_dedup():
    # Mock the client to avoid real API calls
    class MockClient:
        chat = None
        def create(self, **kwargs):
             class Choice:
                  class Message:
                       content = "Response"
                  message = Message()
             class Resp:
                  choices = [Choice()]
             return Resp()

    client = EHClient(thread_id="test_dedup")
    client.clear_history()
    client.openai_client = MockClient()
    
    msg = "Hello!"
    # Call the actual logic path
    client._chat_openai_compatible(client.openai_client, "gpt-4o", msg, "OpenAI")
    
    # Try sending the same raw message again (simulating provider fallback/retry)
    client._chat_openai_compatible(client.openai_client, "gpt-4o", msg, "OpenAI")
    
    print("History length after 2 calls with same raw message:", len(client.unified_history))
    # Should be: System + 1 User + 1 Assistant + (No 2nd User) + 1 Assistant (Wait, assistant might double, but User shouldn't)
    # Actually, if User is skipped, Assistant will be appended to the existing chain or correctly handled?
    # In my logic, if User is skipped, it proceeds to call the provider and appends the assistant. 
    # This might lead to User -> Assistant -> Assistant. Still better than User -> Assistant -> User -> Assistant (Double turns).
    
    # Let's count "user" roles
    user_turns = [m for m in client.unified_history if m["role"] == "user"]
    print("User turns:", len(user_turns))
    assert len(user_turns) == 1, f"Expected 1 user turn, got {len(user_turns)}"

if __name__ == "__main__":
    test_history_dedup()
    print("Dedup test PASSED")
