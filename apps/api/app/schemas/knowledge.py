from uuid import UUID

from pydantic import BaseModel, Field


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    source_types: list[str] | None = Field(
        default=None,
        description="Filter: university, scholarship, country_guide, visa_requirement, etc.",
    )
    limit: int = Field(default=10, ge=1, le=50)


class KnowledgeSearchResultItem(BaseModel):
    document_id: UUID
    source_type: str
    source_id: str | None
    title: str
    content: str
    score: float
    metadata: dict = Field(default_factory=dict)


class KnowledgeSearchResponse(BaseModel):
    query: str
    rewritten_query: str
    results: list[KnowledgeSearchResultItem]
    total: int


class KnowledgeChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_id: UUID | None = Field(default=None, description="Existing conversation session")
    source_types: list[str] | None = None
    llm_provider: str | None = Field(default=None, description="openai | gemini | local")
    stream: bool = Field(default=False)


class CitationResponse(BaseModel):
    index: int
    document_id: UUID
    source_type: str
    title: str
    excerpt: str
    source_id: str | None = None


class ScoreExplanationItem(BaseModel):
    score: float | None = None
    label: str | None = None
    explanation: str | None = None


class KnowledgeChatResponse(BaseModel):
    answer: str
    citations: list[CitationResponse]
    confidence: float
    validation_passed: bool
    hallucination_risk: str
    rewritten_query: str
    model: str
    session_id: UUID | None = None
    sources: list[KnowledgeSearchResultItem] = Field(default_factory=list)


class ConversationSummary(BaseModel):
    id: UUID
    title: str | None
    session_type: str
    message_count: int
    created_at: str
    updated_at: str


class ConversationListResponse(BaseModel):
    conversations: list[ConversationSummary]
    total: int
