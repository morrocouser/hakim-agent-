from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional


class TaskType(str, Enum):
    CODE = "CODE"
    DEBUG = "DEBUG"
    ARCH = "ARCH"
    DATA = "DATA"
    DOC = "DOC"
    RESEARCH = "RESEARCH"
    PLAN = "PLAN"
    QUICK = "QUICK"


class AgentName(str, Enum):
    ARCHITECT = "AGENT_ARCHITECT"
    CODER = "AGENT_CODER"
    DEBUGGER = "AGENT_DEBUGGER"
    ANALYST = "AGENT_ANALYST"
    WRITER = "AGENT_WRITER"
    RESEARCHER = "AGENT_RESEARCHER"
    PLANNER = "AGENT_PLANNER"
    QUICKSHOT = "AGENT_QUICKSHOT"


class ModelName(str, Enum):
    BEST = "deepseek-v4-flash-free"
    LARGE = "mimo-v2.5-free"
    MEDIUM = "minimax-m3-free"
    SMALL = "nemotron-3-ultra-free"
    # Additional free models on OpenCode Zen
    FLASH = "qwen3.6-plus-free"
    CODE = "north-mini-code-free"
    LAGUNA = "big-pickle"
    # Fallback
    FALLBACK = "mimo-v2.5-free"


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


class ScoringDimensions(BaseModel):
    complexity: float = Field(default=5.0, ge=0, le=10)
    stakes: float = Field(default=5.0, ge=0, le=10)
    creativity: float = Field(default=5.0, ge=0, le=10)
    speed_need: float = Field(default=5.0, ge=0, le=10)
    domain_match: float = Field(default=5.0, ge=0, le=10)


class ScoringWeights(BaseModel):
    complexity: float = 0.30
    stakes: float = 0.25
    creativity: float = 0.20
    speed: float = 0.15
    domain: float = 0.10


class TaskRequest(BaseModel):
    description: str
    task_type: TaskType = TaskType.QUICK
    context: Optional[str] = None
    dimensions: Optional[ScoringDimensions] = None


class TaskResult(BaseModel):
    task_id: str
    description: str
    agent: AgentName
    model: ModelName
    score: float
    status: TaskStatus
    output: Optional[str] = None
    error: Optional[str] = None
    iteration: int = 1
    quality_score: float = 0.0


class TaskAssignment(BaseModel):
    task_id: str
    description: str
    agent: AgentName
    model: ModelName
    score: float
    dimensions: ScoringDimensions
    subtasks: list["TaskAssignment"] = []


class ChatMessage(BaseModel):
    role: str = "user"
    content: str


class MemoryEntry(BaseModel):
    level: int
    category: str
    key: str
    value: str
