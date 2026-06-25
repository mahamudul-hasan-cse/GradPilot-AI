# Student Profile Intelligence Engine

Analyze a student's profile and generate actionable study-abroad guidance with scored readiness metrics, insights, and improvement recommendations.

## Endpoint

```
POST /api/v1/profile/analyze
```

### Request

```json
{
  "cgpa": 3.5,
  "ielts": 7.0,
  "degree_level": "masters",
  "major": "Computer Science",
  "country_preferences": ["United States", "Canada"],
  "work_experience_years": 2,
  "has_research_experience": true,
  "publications_count": 1,
  "certifications": ["AWS Certified Developer"],
  "target_intake": "Fall 2026",
  "use_cache": true,
  "analyzer_type": "rule_based"
}
```

### Response

```json
{
  "admission_readiness_score": 78,
  "scholarship_readiness_score": 70,
  "employability_score": 72,
  "strengths": ["Strong academic record (CGPA 3.5)", "..."],
  "weaknesses": [],
  "missing_requirements": [],
  "recommended_actions": ["Apply to 3–5 merit scholarships early..."],
  "recommended_countries": ["United States", "Canada", "..."],
  "recommended_university_tier": "Competitive (Top 100)",
  "profile_summary": "You are pursuing a masters in Computer Science...",
  "score_explanations": {
    "admission_readiness": {
      "score": 78,
      "label": "Admission Readiness",
      "explanation": "Based on your masters profile...",
      "factors": { "academic": 0.85, "language": 0.88, "...": 0.0 }
    }
  },
  "analyzer_type": "rule_based",
  "cache_hit": false,
  "history_id": "uuid"
}
```

## Scores

### Admission Readiness (0–100)

| Factor | Weight |
|--------|--------|
| Academic (CGPA vs degree benchmark) | 30% |
| Language (IELTS) | 25% |
| Research experience & publications | 20% |
| Work experience | 10% |
| Profile completeness | 15% |

### Scholarship Readiness (0–100)

| Factor | Weight |
|--------|--------|
| Academic | 30% |
| Language | 20% |
| Research & publications | 25% |
| Work experience | 15% |
| Certifications | 10% |

### Employability (0–100)

| Factor | Weight |
|--------|--------|
| Work experience | 35% |
| Certifications | 20% |
| Research & publications | 25% |
| Academic | 20% |

## University Tier Classification

| Tier | Admission Score |
|------|-----------------|
| Top Tier (R1 / Russell Group) | ≥ 85 |
| Competitive (Top 100) | 70–84 |
| Target (Mid-tier) | 55–69 |
| Foundation / Safety | < 55 |

## Architecture

```
ProfileIntelligenceService
  ├── ProfileAnalyzer (Protocol)     ← pluggable for future ML
  │     └── RuleBasedProfileAnalyzer
  ├── RecommendationGenerator        ← actions & country suggestions
  ├── RecommendationCache            ← Redis (prefix: profile:analysis:)
  └── ProfileAnalysisRepository      ← history persistence
```

Register new analyzers in `ANALYZER_REGISTRY` (e.g. `"ml": MLProfileAnalyzer`).

## Admin Analytics

```
GET /api/v1/profile/analyze/analytics
```

Web dashboard: `/admin/profile-intelligence`

## History

Stored in `profile_analysis` table (migration `006`).

## Tests

```bash
cd apps/api
pytest tests/test_profile_intelligence.py -v
```

## Example

```bash
curl -X POST http://localhost:8000/api/v1/profile/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "cgpa": 3.6,
    "ielts": 7.0,
    "degree_level": "masters",
    "major": "Data Science",
    "country_preferences": ["United Kingdom"],
    "work_experience_years": 1,
    "has_research_experience": true
  }'
```
