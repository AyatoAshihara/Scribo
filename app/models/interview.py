from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class Role(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class ChatMessage(BaseModel):
    role: Role
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)

class DesignProposal(BaseModel):
    theme: str = Field(default="", description="Proposed theme")
    breakdown: Dict[str, Any] = Field(default={}, description="Proposed breakdown")
    structure: List[Dict[str, Any]] = Field(default=[], description="Proposed structure")
    module_map: Dict[str, List[str]] = Field(default={}, description="Proposed module mapping")
    reasoning: Optional[str] = Field(default=None, description="AI reasoning for the proposal")

class InterviewSession(BaseModel):
    user_id: str
    exam_id: str
    history: List[ChatMessage] = []
    current_proposal: Optional[DesignProposal] = None
    status: str = "active" # active, completed
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class ChatRequest(BaseModel):
    message: str
