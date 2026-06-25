# University Recommendation Engine

Personalized university recommendations with **Safe / Target / Ambitious** classification, explainable scores, Redis caching, and history tracking.

## Endpoint

```
POST /api/v1/recommendations/universities
```

### Request

```json
{
  "cgpa": 3.5,
  "ielts": 7.0,
  "budget": 50000,
  "country_preference": "United States",
  "major": "Computer Science",
  "work_experience_years": 2,
  "has_research_experience": true,
  "limit_per_tier": 10,
  "use_cache": true
}
```

### Response

```json
{
  "request": { "...": "..." },
  "recommendations": {
    "safe": [
      {
        "university": { "name": "...", "country": "...", "tuition_fee": "40000" },
        "score_breakdown": {
          "academic_match": 0.92,
          "language_match": 0.88,
          "budget_match": 0.95,
          "program_match": 1.0,
          "scholarship_match": 1.0,
          "recommendation_score": 93.5,
          "tier": "safe"
        },
        "explanation": "You meet GPA requirements. You meet IELTS requirements. Tuition is within budget. Strong program match for Computer Science. Scholarship opportunities available. Classified as Safe (score: 94/100)."
      }
    ],
    "target": [],
    "ambitious": []
  },
  "total_candidates_evaluated": 45,
  "cache_hit": false,
  "history_id": "uuid",
  "scoring_weights": {
    "academic_match": 0.35,
    "language_match": 0.20,
    "budget_match": 0.20,
    "program_match": 0.15,
    "scholarship_match": 0.10
  }
}
```

## Scoring Formula (0–100)

| Factor | Weight | Inputs |
|--------|--------|--------|
| **Academic Match** | 35% | CGPA vs minimum GPA, work experience, research experience |
| **Language Match** | 20% | IELTS vs minimum IELTS |
| **Budget Match** | 20% | Student budget vs tuition fee |
| **Program Match** | 15% | Major vs university programs/majors |
| **Scholarship Match** | 10% | Scholarship availability flag |

```
score = (academic×0.35 + language×0.20 + budget×0.20 + program×0.15 + scholarship×0.10) × 100
```

## Tier Classification

| Tier | Score Range | Meaning |
|------|-------------|---------|
| **Safe** | ≥ 80 | Strong fit — high admission probability |
| **Target** | 60–79 | Realistic match — competitive but achievable |
| **Ambitious** | < 60 | Stretch school — requires profile strengthening |

## Explanation Engine

Each recommendation includes a human-readable explanation covering:

- GPA requirement status
- Work/research experience impact
- IELTS requirement status
- Budget vs tuition fit
- Program/major alignment
- Scholarship availability
- Tier classification with score

## Redis Caching

- Cache key: SHA-256 hash of request payload
- Default TTL: 3600 seconds (1 hour)
- Graceful degradation if Redis is unavailable
- Set `use_cache: false` to bypass cache

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |
| `REDIS_ENABLED` | `true` | Enable/disable caching |
| `RECOMMENDATION_CACHE_TTL_SECONDS` | `3600` | Cache TTL |

## Recommendation History

Every request is persisted to `recommendation_history`:

| Column | Description |
|--------|-------------|
| `user_id` | Authenticated user (optional) |
| `request_payload` | Full request JSON |
| `response_summary` | Tier counts, cache hit status |
| `total_score_avg` | Average score across returned recommendations |
| `cache_hit` | Whether response came from cache |

Migration: `004_recommendation_history`

## Authentication

- **Optional** — anonymous users can get recommendations
- If `Authorization: Bearer <token>` is provided, history is linked to the user

## Example

```bash
curl -X POST http://localhost:8000/api/v1/recommendations/universities \
  -H "Content-Type: application/json" \
  -d '{
    "cgpa": 3.4,
    "ielts": 7.0,
    "budget": 45000,
    "country_preference": "United States",
    "major": "Computer Science",
    "work_experience_years": 1,
    "has_research_experience": false
  }'
```

## Legacy Endpoint

The original discovery endpoint remains available:

```
POST /api/v1/recommend-universities
```

The new `/recommendations/universities` endpoint uses the updated scoring formula and includes explanations.

## Tests

```bash
cd apps/api
pytest tests/test_recommendation_engine.py -v
```

## Architecture

```
Request → Cache Check → Candidate Fetch → Score (5 factors) → Tier Classify
       → Explain → Group by Tier → Cache Store → History Save → Response
```

Modules:

| Module | Path |
|--------|------|
| Scoring | `app/services/recommendation/scoring.py` |
| Explainer | `app/services/recommendation/explainer.py` |
| Engine | `app/services/recommendation/engine.py` |
| Cache | `app/services/recommendation/cache.py` |
