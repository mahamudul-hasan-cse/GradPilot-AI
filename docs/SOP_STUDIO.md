# SOP Studio

Rich-text Statement of Purpose authoring with AI assistance, version history, collaboration architecture, and export.

## Features

| Feature | Description |
|---------|-------------|
| AI Draft | Generate full SOP from Student Digital Twin profile |
| AI Rewrite | Improve clarity, tone, or sections per instruction |
| Grammar Review | Rule-based checks + optional LLM polish |
| University Tailoring | Adapt essay for target program and highlights |
| Scholarship Tailoring | Adapt essay for funding eligibility and mission |
| Version History | Snapshots for manual edits, AI actions, and autosave |
| Autosave | Rich-text editor autosave with cursor metadata |
| Comments | Threaded reviewer comments with anchor text |
| Word Counter | Live count vs target word count |
| AI Scoring | Clarity, structure, uniqueness, program fit |
| Plagiarism | Placeholder interface for external provider integration |
| Export | PDF, DOCX, Markdown |
| Collaboration | Session tokens, roles, heartbeat (architecture for real-time sync) |

## Architecture

```
Digital Twin → SOPDraftEngine → SOPStudioService → sop_documents / sop_versions
                    ↓                                    ↓
              Rewrite / Grammar / Tailor            sop_history / sop_comments
                    ↓                                    ↓
              ScoringEngine / ExportEngine         sop_collaboration_sessions
```

## Components

| Component | Path |
|-----------|------|
| SOPStudioService | `services/sop_studio/service.py` |
| DraftEngine | `services/sop_studio/draft_engine.py` |
| RewriteEngine | `services/sop_studio/rewrite_engine.py` |
| GrammarEngine | `services/sop_studio/grammar_engine.py` |
| TailoringEngine | `services/sop_studio/tailoring_engine.py` |
| ScoringEngine | `services/sop_studio/scoring_engine.py` |
| ExportEngine | `services/sop_studio/export_engine.py` |
| PlagiarismService | `services/sop_studio/plagiarism.py` |

## Storage

| Table | Purpose |
|-------|---------|
| `sop_documents` | SOP metadata, current version pointer, word counts |
| `sop_versions` | Content snapshots (HTML + plain), autosave flag |
| `sop_comments` | Reviewer comments |
| `sop_history` | Audit log of actions |
| `sop_collaboration_sessions` | Collaborative editing sessions |

## APIs

All routes under `/api/v1/sop-studio`. Swagger: `http://localhost:8000/docs` → **SOP Studio**.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/documents` | List user's SOPs |
| POST | `/documents` | Create SOP |
| GET | `/documents/{id}` | Get SOP with content |
| PATCH | `/documents/{id}` | Update metadata |
| DELETE | `/documents/{id}` | Delete SOP |
| POST | `/documents/{id}/autosave` | Autosave editor content |
| GET | `/documents/{id}/word-count` | Word counter |
| POST | `/documents/{id}/ai/draft` | AI draft |
| POST | `/documents/{id}/ai/rewrite` | AI rewrite |
| POST | `/documents/{id}/ai/grammar` | Grammar review |
| POST | `/documents/{id}/ai/tailor/university` | University tailoring |
| POST | `/documents/{id}/ai/tailor/scholarship` | Scholarship tailoring |
| POST | `/documents/{id}/ai/score` | AI scoring |
| POST | `/documents/{id}/plagiarism` | Plagiarism placeholder |
| POST | `/documents/{id}/export?format=pdf` | Export (pdf/docx/markdown) |
| GET | `/documents/{id}/versions` | Version history |
| GET | `/documents/{id}/versions/compare` | Version comparison |
| GET | `/documents/{id}/comments` | List comments |
| POST | `/documents/{id}/comments` | Add comment |
| GET | `/documents/{id}/history` | Action history |
| POST | `/documents/{id}/collaboration/join` | Join collaboration session |
| GET | `/analytics` | Usage analytics |

## Digital Twin Events

| Event | When |
|-------|------|
| `sop.created` | New SOP document created |
| `sop.updated` | AI action applied (draft, rewrite, tailor) |
| `sop.exported` | Document exported |
| `sop.scored` | AI scoring completed |

## Setup

```bash
cd apps/api
pip install -r requirements.txt
alembic upgrade head
pytest tests/test_sop_studio.py -v
```

## Export Dependencies

- `python-docx` — DOCX export
- `fpdf2` — PDF export

Fallback minimal exporters are used if packages are unavailable.
