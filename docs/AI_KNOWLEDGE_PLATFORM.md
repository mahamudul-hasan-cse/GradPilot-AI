# AI Knowledge Platform

GradPilot's RAG-powered knowledge system — **not a generic chatbot**. Answers study-abroad questions using verified sources with citations, hallucination guards, and hybrid retrieval.

## Architecture

```
User Question
    ↓
Query Rewriter
    ↓
Hybrid Retriever
    ├── PostgreSQL (full-text)
    ├── Qdrant (semantic)
    └── BM25 (keyword scoring)
    ↓
Reciprocal Rank Fusion (RRF)
    ↓
Context Builder + Compression
    ↓
GeminiService
    ↓
Citation Generator
    ↓
Hallucination Guard + Answer Validator
    ↓
Response (with sources)
```

## Knowledge Sources

| Source Type | Description |
|-------------|-------------|
| `university` | Indexed from universities table |
| `scholarship` | Indexed from scholarships table |
| `country_guide` | Static country study guides |
| `visa_requirement` | Visa process knowledge |
| `admission_requirement` | General admission criteria |
| `sop_knowledge` | SOP writing guidance |
| `profile_analysis` | User's profile analysis (authenticated) |
| `recommendation_history` | User's recommendation history (authenticated) |

## Endpoints

### `POST /api/v1/ai/search`

Hybrid search without LLM generation. Public (optional auth for personalized sources).

```json
{
  "query": "F-1 visa requirements USA",
  "source_types": ["visa_requirement", "country_guide"],
  "limit": 10
}
```

### `POST /api/v1/ai/chat`

Knowledge-grounded Q&A with citations. **Requires authentication.**

```json
{
  "message": "What IELTS score do I need for UK masters?",
  "session_id": null,
  "stream": false
}
```

Set `"stream": true` for SSE streaming. The deprecated `llm_provider` field is ignored for backward compatibility; Gemini is always used.

### `GET /api/v1/ai/conversations`

List user's knowledge conversation sessions.

### `POST /api/v1/ai/index`

Re-index knowledge base (universities + scholarships + static guides).

## Configuration

```env
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-1.5-flash
KNOWLEDGE_MEMORY_TTL_SECONDS=86400
```

Without `GEMINI_API_KEY`, the service returns context-grounded fallback summaries.

## Modular Components

| Component | Path |
|-----------|------|
| KnowledgeService | `services/knowledge/service.py` |
| HybridRetriever | `services/knowledge/retrieval/hybrid.py` |
| BM25Scorer | `services/knowledge/retrieval/bm25.py` |
| KnowledgeVectorStore | `services/knowledge/retrieval/semantic.py` |
| QueryRewriter | `services/knowledge/pipeline/query_rewriter.py` |
| ContextBuilder | `services/knowledge/pipeline/context_builder.py` |
| CitationGenerator | `services/knowledge/pipeline/citation_generator.py` |
| HallucinationGuard | `services/knowledge/pipeline/hallucination_guard.py` |
| AnswerValidator | `services/knowledge/pipeline/answer_validator.py` |
| PromptManager | `services/knowledge/prompts/prompt_manager.py` |
| ConversationMemory | `services/knowledge/memory/conversation_memory.py` |
| GeminiService | `services/ai/gemini_service.py` |
| Legacy LLM Shim | `services/knowledge/llm/providers.py` |

## Setup

```bash
cd apps/api
alembic upgrade head
python scripts/seed_universities.py
python scripts/seed_knowledge.py
pytest tests/test_knowledge_platform.py -v
```

## Example

```bash
# Search
curl -X POST http://localhost:8000/api/v1/ai/search \
  -H "Content-Type: application/json" \
  -d '{"query": "SOP structure for masters application"}'

# Chat (authenticated)
curl -X POST http://localhost:8000/api/v1/ai/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "How do I write a strong SOP for CS masters?"}'
```

## Future ML / Local LLM

Register providers in `get_llm_provider()` and indexers in `KnowledgeIndexer`. The `ProfileAnalyzer` pattern applies — pluggable backends behind a protocol.
