from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, root_validator
from datetime import datetime

class CharacterProfile(BaseModel):
    """Static lore and profile data for a character."""
    id: str = Field(..., description="Unique identity ID (e.g., EH-01, PC-01)")
    name: str
    race: Optional[str] = None
    role: Optional[str] = None
    avatar_url: Optional[str] = None
    description: Optional[str] = None
    bio: Optional[str] = None
    motivation: Optional[str] = None
    secret: Optional[str] = None

class CharacterState(BaseModel):
    """Dynamic runtime state for a character."""
    id: str
    hp: Optional[int] = None
    max_hp: Optional[int] = None
    gold: Optional[int] = 0
    inventory: Dict[str, int] = Field(default_factory=dict)
    equipped_weapon: Optional[str] = None
    equipped_armor: Optional[str] = None
    status_effects: List[str] = Field(default_factory=list)
    location: Optional[str] = None

class QuestRecord(BaseModel):
    """State for an active or completed quest."""
    id: str
    title: str
    description: str
    status: str = Field(description="'active', 'completed', or 'failed'")
    giver_id: Optional[str] = None
    objectives: List[str] = Field(default_factory=list)
    rewards: Dict[str, Any] = Field(default_factory=dict)

class ConversationTurn(BaseModel):
    """A single dialogue or narrative exchange."""
    speaker: str
    speaker_id: Optional[str] = None
    content: str
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())

class ConversationThread(BaseModel):
    """A thread of conversation within a specific channel."""
    channel_id: str
    system_prompt: Optional[str] = None
    summary: Optional[str] = None
    turns: List[ConversationTurn] = Field(default_factory=list)

class NarrativeEvent(BaseModel):
    """A global narrative pulse event."""
    timestamp: str
    event_text: str

class StateMutation(BaseModel):
    """A generic wrapper for any state-changing operation directed to the coordinator."""
    mutation_type: str = Field(description="The type of mutation (e.g., 'update_gold', 'add_item', 'update_hp')")
    target_id: str = Field(description="The ID of the character or entity to mutate")
    payload: Dict[str, Any] = Field(description="The data payload for the mutation")
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())
