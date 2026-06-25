# Scholarship Matching Engine

Match students to scholarships with eligibility scoring, probability estimation, explanations, Redis caching, and admin analytics.

## Endpoint

```
POST /api/v1/recommendations/scholarships
```

### Request

```json
{
  "cgpa": 3.6,
  "ielts": 7.0,
  "degree_level": "masters",
  "major": "Computer Science",
  "country_preference": "United States",
  "has_research_experience": true,
  "work_experience_years": 2,
  "nationality": "India",
  "min_score": 60,
  "limit": 50,
  "use_cache": true
}
```

### Response

```json
{
  "matches": [
    {
      "scholarship": {
        "title": "Fulbright Foreign Student Program",
        "country": "United States",
        "degree_level": "masters",
        "funding_type": "full",
        "minimum_gpa": "3.2",
        "minimum_ielts": "6.5"
      },
      "score": {
        "academic_match": 0.92,
        "language_match": 0.88,
        "degree_match": 1.0,
        "country_match": 1.0,
        "research_match": 1.0,
        "work_experience_match": 0.85,
        "scholarship_score": 91.5,
        "eligibility_probability": 0.892,
        "match_category": "excellent"
      },
      "explanation": "You meet the GPA requirement (3.2). You meet IELTS requirements. ..."
    }
  ],
  "grouped": {
    "excellent": [],
    "strong": [],
    "possible": [],
    "low": []
  },
  "total_candidates_evaluated": 150,
  "cache_hit": false,
  "history_id": "uuid"
}
```

## Scoring Formula (0–100)

| Factor | Weight |
|--------|--------|
| Academic Match (CGPA vs minimum GPA) | 30% |
| Language Match (IELTS) | 20% |
| Degree Match | 15% |
| Country Match | 15% |
| Research Match | 10% |
| Work Experience Match | 10% |

Nationality eligibility acts as a gate (ineligible nationalities score 0).
Major relevance applies a soft adjustment factor.

## Match Categories

| Category | Score | Meaning |
|----------|-------|---------|
| **Excellent Match** | 90–100 | Highly likely eligible |
| **Strong Match** | 75–89 | Good fit |
| **Possible Match** | 60–74 | Worth applying with gaps |
| **Low Match** | < 60 | Unlikely fit |

## Eligibility Probability

Derived from scholarship score with tiered calibration (0.05–0.98 range).

## Admin Analytics

```
GET /api/v1/recommendations/scholarships/analytics
```

Returns:
- Total recommendations run
- Average scholarship score
- Average eligibility probability
- Cache hit rate
- Match category distribution
- Total active scholarships in catalog
- Recent request history

## Scholarship Schema Fields

| Field | Description |
|-------|-------------|
| `degree_level` | bachelors, masters, phd |
| `funding_type` | full, partial, tuition_waiver |
| `minimum_gpa` | Minimum CGPA required |
| `minimum_ielts` | Minimum IELTS band |
| `research_required` | Research experience required |
| `work_experience_required_years` | Minimum work years |
| `eligible_nationalities` | Restricted nationalities (optional) |
| `eligible_majors` | Eligible fields of study (optional) |

## Performance

- Pre-filters candidates via indexed DB queries (country, degree level)
- Batch in-memory scoring supports **5,000+ scholarships** per request
- Redis caching avoids recomputation for identical profiles

## History

Stored in `scholarship_recommendation_history` (migration `005`).

## Tests

```bash
cd apps/api
pytest tests/test_scholarship_recommendation.py -v
```

## Example

```bash
curl -X POST http://localhost:8000/api/v1/recommendations/scholarships \
  -H "Content-Type: application/json" \
  -d '{
    "cgpa": 3.5,
    "ielts": 7.0,
    "degree_level": "masters",
    "major": "Computer Science",
    "country_preference": "United States",
    "nationality": "India",
    "work_experience_years": 1
  }'
```
