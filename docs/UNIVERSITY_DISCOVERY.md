# University Discovery Engine API

GradPilot AI's University Discovery Engine provides filtering, keyword search, semantic search via Qdrant embeddings, and personalized recommendations with Safe / Target / Ambitious tiers.

## Base URL

```
http://localhost:8000/api/v1
```

Interactive docs: `http://localhost:8000/docs`

---

## Data model

Each university record includes:

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | University name |
| `country` | string | Country |
| `city` | string | City |
| `ranking` | int | World ranking (lower is better) |
| `tuition_fee` | decimal | Annual tuition (USD) |
| `application_fee` | decimal | Application fee |
| `minimum_gpa` | decimal | Minimum GPA (4.0 scale) |
| `minimum_ielts` | decimal | Minimum IELTS band |
| `minimum_toefl` | int | Minimum TOEFL score |
| `deadline` | date | Application deadline |
| `programs` | string[] | Program names |
| `scholarships_available` | bool | Scholarship flag |
| `website` | string | Official website |
| `majors` | string[] | Supported majors |

---

## Endpoints

### 1. Filter universities

`GET /universities/filter`

Query parameters for structured discovery.

**Example**

```bash
curl "http://localhost:8000/api/v1/universities/filter?country=Canada&major=Computer%20Science&max_tuition=50000&scholarships_available=true&limit=10"
```

**Parameters**

| Param | Description |
|-------|-------------|
| `country` | Country name (partial match) |
| `city` | City name |
| `major` | Major / field of study |
| `min_ranking` | Minimum ranking number |
| `max_ranking` | Maximum ranking number |
| `max_tuition` | Max annual tuition |
| `min_tuition` | Min annual tuition |
| `max_gpa_required` | Max required GPA filter |
| `min_gpa_required` | Min required GPA filter |
| `max_ielts_required` | Max required IELTS |
| `scholarships_available` | `true` / `false` |
| `skip`, `limit` | Pagination |

---

### 2. Keyword search

`POST /universities/search`

Full-text search across name, city, description, programs.

**Example**

```bash
curl -X POST http://localhost:8000/api/v1/universities/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "software engineering silicon valley",
    "country": "United States",
    "limit": 10
  }'
```

---

### 3. Semantic search

`POST /universities/semantic-search`

Natural-language search powered by deterministic local embeddings stored in **Qdrant**.

**Example**

```bash
curl -X POST http://localhost:8000/api/v1/universities/semantic-search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "affordable masters in computer science with scholarships in Europe",
    "limit": 5
  }'
```

Falls back to keyword search if Qdrant is unavailable.

---

### 4. Recommend universities

`POST /recommend-universities`

Personalized recommendations in three tiers based on student profile.

**Example**

```bash
curl -X POST http://localhost:8000/api/v1/recommend-universities \
  -H "Content-Type: application/json" \
  -d '{
    "cgpa": 3.4,
    "ielts": 7.0,
    "budget": 45000,
    "country": "United States",
    "major": "Computer Science",
    "limit_per_tier": 5
  }'
```

**Response structure**

```json
{
  "input": { "cgpa": "3.4", "ielts": "7.0", "budget": "45000", "major": "Computer Science" },
  "recommendations": {
    "safe": [ { "name": "...", "match_score": 0.82, "ranking_breakdown": { "tier": "safe" } } ],
    "target": [ ... ],
    "ambitious": [ ... ]
  },
  "total_candidates_evaluated": 12
}
```

---

## Ranking algorithm

Each university receives a **composite score** (0–1) from weighted factors:

| Factor | Weight | Description |
|--------|--------|-------------|
| GPA Match | 25% | How well student CGPA meets `minimum_gpa` |
| IELTS Match | 20% | IELTS band vs `minimum_ielts` |
| Budget Match | 25% | Student budget vs `tuition_fee` |
| Ranking Preference | 20% | Prestige signal from world ranking |
| Scholarship Availability | 10% | Bonus when scholarships available |

### Tier classification

| Tier | Criteria |
|------|----------|
| **Safe** | Strong fit on GPA, IELTS, and budget; composite ≥ 0.68 |
| **Target** | Moderate fit; realistic admission chance |
| **Ambitious** | Stretch schools (top-ranked) or below requirements |

---

## Seed data & indexing

```bash
# Load 12 universities + index vectors
cd apps/api
python scripts/seed_universities.py

# Force reload
python scripts/seed_universities.py --force

# Skip vector indexing
python scripts/seed_universities.py --no-index
```

---

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `QDRANT_HOST` | `localhost` | Qdrant host |
| `QDRANT_PORT` | `6333` | Qdrant port |

Semantic indexing uses deterministic local embeddings in Phase 1, so no external embedding provider is required.

---

## Running tests

```bash
cd apps/api
pytest tests/test_university_ranking.py tests/test_university_discovery.py -v
```
