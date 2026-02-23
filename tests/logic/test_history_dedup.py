import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from core.ai.client import EHClient
import logging

logging.basicConfig(level=logging.INFO)

def test_history_dedup():
    # Success Mock
    class MockSuccessClient:
        class Chat:
            class Completions:
                def create(self, **kwargs):
                     class Choice:
                          class Message:
                               content = "Response"
                          message = Message()
                     class Resp:
                          choices = [Choice()]
                     return Resp()
            completions = Completions()
        chat = Chat()

    # Failure Mock
    class MockFailClient:
        class Chat:
            class Completions:
                def create(self, **kwargs):
                    raise Exception("API Failure")
            completions = Completions()
        chat = Chat()

    client = EHClient(thread_id="test_dedup")
    client.clear_history()
    
    msg = "Hello!"
    # Call 1: Simulate Fail (User turn appended, but API fails)
    try:
        client._chat_openai_compatible(MockFailClient(), "gpt-4o", msg, "OpenAI")
    except:
        pass
    
    # Call 2: Simulate Retry/Fallback (Should NOT append second user turn)
    client._chat_openai_compatible(MockSuccessClient(), "gpt-4o", msg, "OpenAI")
    
    print("History length after fail and retry:", len(client.unified_history))
    
    # Let's count "user" roles
    user_turns = [m for m in client.unified_history if m["role"] == "user"]
    print("User turns:", len(user_turns))
    assert len(user_turns) == 1, f"Expected 1 user turn, got {len(user_turns)}"

if __name__ == "__main__":
    test_history_dedup()
    print("Dedup test PASSED")
