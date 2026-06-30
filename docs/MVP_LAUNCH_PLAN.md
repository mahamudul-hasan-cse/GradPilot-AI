# GradPilot MVP Launch Plan

GradPilot is being simplified into a polished SaaS MVP for international students. The product should prioritize useful workflows over backend complexity.

## Product Focus

The launch experience should help a student:

1. Register and build a profile
2. Upload IELTS, CV, and transcript documents
3. Receive university and scholarship matches
4. Chat with a Gemini-powered AI advisor
5. Generate SOP drafts
6. Practice interview questions
7. Track applications
8. Use the dashboard as a daily command center

## AI Direction

Gemini is the only AI engine for launch. Multi-provider routing, AI gateway abstractions, prompt registries, A/B testing, cost analytics, Anthropic, Ollama, and OpenAI support are out of scope for the MVP.

## Module Order

1. Dashboard command center
2. Profile wizard
3. Gemini-only AI advisor
4. University explorer and matches
5. Scholarship explorer and matches
6. Application tracker
7. Document upload and extraction
8. SOP Studio MVP
9. Interview Coach MVP
10. Production cleanup

## Complexity To Remove Or Defer

- AI gateway and provider routing
- Prompt registry and A/B testing
- AI cost analytics
- Admin CMS and operations dashboards
- Local development complexity
- Unnecessary workers for MVP flows
- Duplicate models, repositories, and APIs
- Overly complex digital-twin orchestration where direct reads are enough

## Dashboard Command Center

The dashboard now groups existing functionality into clear product sections:

- At a Glance: readiness, profile progress, application stats, progress
- Today: tasks and deadlines
- Matches: universities and scholarships
- Recent Activity: applications and documents
- AI Guidance: insights and quick actions

The dashboard should stay lightweight: use existing data hooks first, add backend aggregation only when it removes real duplication or latency.
