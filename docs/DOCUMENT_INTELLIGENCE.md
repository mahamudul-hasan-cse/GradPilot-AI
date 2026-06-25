# Document Intelligence Platform

Convert uploaded admission documents into structured, validated knowledge that updates the Student Digital Twin.

## Pipeline

```
Upload → Queue → OCR → Classify → Extract → Validate → Score → Twin Sync
```

## Supported Documents

| Type | Extracted Fields |
|------|------------------|
| Passport | name, passport_number, expiry_date, nationality |
| Transcript | institution, degree, CGPA, courses |
| Degree Certificate | institution, degree, major, graduation_date |
| CV/Resume | skills, experience, projects, education |
| IELTS TRF | overall_band, listening, reading, writing, speaking, test_date |
| TOEFL | total_score, section scores, test_date |
| GRE | verbal, quantitative, analytical_writing, total |
| LOR | recommender_name, institution, relationship |
| SOP | target_program, university, word_count, themes |

## Components

| Component | Location |
|-----------|----------|
| DocumentIntelligenceService | `services/document_intelligence/service.py` |
| DocumentPipeline | OCR → classify → extract → validate → sync |
| OCR Providers | `fallback`, `tesseract` (pluggable) |
| DocumentClassifier | Rule-based keyword + filename classification |
| Field Extractors | Per-document-type regex extractors |
| ValidationEngine | Schema + business rule validation |
| ConfidenceScorer | Weighted confidence 0-1 |
| DuplicateDetector | SHA-256 file hash dedup |
| DocumentProcessingQueue | Redis-backed async queue |
| TwinSyncService | Updates profile + publishes twin events |

## APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/documents/upload` | Upload document (multipart) |
| GET | `/api/v1/documents` | List user documents |
| GET | `/api/v1/documents/{id}` | Get with extraction results |
| POST | `/api/v1/documents/{id}/parse` | Run parsing pipeline |
| POST | `/api/v1/documents/{id}/validate` | Re-validate extracted fields |
| GET | `/api/v1/documents/{id}/versions` | Version history |
| GET | `/api/v1/documents/jobs/{id}` | Processing job status |

## Digital Twin Integration

On successful extraction:
1. Updates student profile (IELTS, GPA, nationality from documents)
2. Publishes `document.uploaded` event
3. Triggers twin sync + recommendation refresh
4. Records timeline entry

## Configuration

```env
DOCUMENT_UPLOAD_DIR=uploads
DOCUMENT_OCR_PROVIDER=fallback
```

## Setup

```bash
cd apps/api
alembic upgrade head
pytest tests/test_document_intelligence.py -v
```

## Example

```bash
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@ielts_trf.pdf" \
  -F "document_type=ielts_trf"
```
