# GradPilot AI — Product Requirements Document

| Field | Value |
|-------|-------|
| **Product** | GradPilot AI |
| **Version** | 1.0 |
| **Status** | Draft |
| **Owner** | Product |
| **Last Updated** | June 2026 |
| **Mission** | Become the AI Operating System for students pursuing higher education abroad |

---

## Executive Summary

GradPilot AI is an AI-native platform that guides international students from discovery to enrollment. It unifies university search, scholarship matching, AI counseling, SOP co-piloting, and application tracking into a single workflow — replacing fragmented spreadsheets, consultants, and generic search tools.

**Core value proposition:** Personalized, data-driven guidance at a fraction of the cost and friction of traditional education consultants.

**Initial wedge:** Masters applicants from emerging markets (India, Nigeria, Southeast Asia) applying to US, UK, Canada, and Australia.

---

## 1. Problem Statement

### The problem

Every year, millions of students pursue higher education abroad. The process is:

- **Opaque** — admission requirements, deadlines, and funding options are scattered across hundreds of websites.
- **Expensive** — education consultants charge $1,000–$10,000+ with inconsistent quality.
- **Overwhelming** — students manage 10–20 applications across universities, scholarships, visas, and documents manually.
- **High-stakes** — a single missed deadline or weak SOP can cost a year of opportunity.

### Why now

1. **International student mobility is at record highs** — demand for graduate programs continues to grow post-pandemic.
2. **AI can personalize at scale** — LLMs enable context-aware guidance previously only available from human counselors.
3. **Students are AI-native** — Gen Z applicants expect conversational, mobile-first tools.
4. **Data is becoming accessible** — university catalogs, rankings, and scholarship databases can be structured and semantically searched.

### What success looks like

A student opens GradPilot AI, builds a profile once, and receives a ranked shortlist of universities and scholarships, AI-drafted SOPs, and a live application tracker — all updated as deadlines approach and new opportunities emerge.

---

## 2. User Personas

### Persona 1: Priya — Masters Applicant (Primary)

| Attribute | Detail |
|-----------|--------|
| **Age** | 23 |
| **Location** | Bangalore, India |
| **Goal** | MSc Computer Science in US/Canada |
| **CGPA** | 3.6 / 4.0 |
| **Budget** | $40,000/year |
| **Pain** | Overwhelmed by 200+ university options; unsure which are realistic vs. reach schools |
| **Behavior** | Uses Reddit, YouTube, and WhatsApp groups; distrusts expensive agents |
| **Jobs to be done** | Find safe/target/ambitious schools, identify scholarships, draft SOP, track deadlines |

### Persona 2: James — PhD Applicant

| Attribute | Detail |
|-----------|--------|
| **Age** | 27 |
| **Location** | Lagos, Nigeria |
| **Goal** | PhD in Public Health (fully funded) |
| **Pain** | Finding professors with funding; writing research statements; navigating visa timelines |
| **Jobs to be done** | Discover funded programs, align research interests, manage multi-year application pipeline |

### Persona 3: Sofia — Undergraduate Transfer

| Attribute | Detail |
|-----------|--------|
| **Age** | 19 |
| **Location** | Mexico City |
| **Goal** | Transfer to US university for BSc Engineering |
| **Pain** | Limited understanding of credit transfer, SAT/ACT requirements, and financial aid |
| **Jobs to be done** | Understand eligibility, compare costs, plan timeline from sophomore year |

### Persona 4: Ahmed — Scholarship Seeker

| Attribute | Detail |
|-----------|--------|
| **Age** | 25 |
| **Location** | Cairo, Egypt |
| **Goal** | Fully funded Masters in Europe |
| **Pain** | Scholarship deadlines are scattered; eligibility criteria are vague |
| **Jobs to be done** | Filter scholarships by nationality/eligibility, get reminders, auto-match to profile |

### Persona 5: Lin — International Student (In-Country)

| Attribute | Detail |
|-----------|--------|
| **Age** | 24 |
| **Location** | Currently in UK (from China) |
| **Goal** | Extend to PhD or switch programs |
| **Pain** | Visa constraints, program switching rules, funding for second degree |
| **Jobs to be done** | Navigate in-country options, compliance-aware planning |

---

## 3. User Journeys

### Journey A: Discovery → Shortlist (MVP Critical Path)

```
Sign up → Build profile (GPA, tests, budget, major, countries)
       → Receive Safe / Target / Ambitious university recommendations
       → Filter & semantic search universities
       → Save favorites to shortlist
       → View scholarship matches per university
```

**Emotional arc:** Confusion → Clarity → Confidence

### Journey B: Application Execution

```
Select university → Create application record
                 → AI reviews profile fit & flags gaps
                 → Co-write SOP with AI (draft → refine → export)
                 → Upload documents checklist
                 → Track status (draft → submitted → decision)
                 → Receive deadline reminders
```

**Emotional arc:** Anxiety → Progress → Control

### Journey C: AI Guidance (Ongoing)

```
Open chat → Ask "Which schools fit my profile?"
         → Get personalized answer grounded in profile + catalog
         → Follow up: "Compare MIT vs. CMU for my background"
         → Save conversation; link to applications
```

**Emotional arc:** Uncertainty → Informed decision

### Journey D: Scholarship Hunt

```
Set funding goal → Browse / search scholarships
                → Filter by country, deadline, amount
                → Match score vs. eligibility
                → Add to application tracker
                → Get deadline alerts
```

---

## 4. User Stories

### Epic 1: Identity & Profile

| ID | Story | Priority |
|----|-------|----------|
| US-1.1 | As a student, I want to register with email so I can save my progress. | P0 |
| US-1.2 | As a student, I want to create an academic profile (GPA, tests, major, budget) so recommendations are personalized. | P0 |
| US-1.3 | As a student, I want to update my profile anytime so guidance stays current. | P0 |
| US-1.4 | As a student, I want to specify target countries and degree level so results are relevant. | P1 |

### Epic 2: University Discovery

| ID | Story | Priority |
|----|-------|----------|
| US-2.1 | As a Masters applicant, I want university recommendations in Safe/Target/Ambitious tiers so I can build a balanced list. | P0 |
| US-2.2 | As a student, I want to filter universities by tuition, GPA, IELTS, and country so I find affordable options. | P0 |
| US-2.3 | As a student, I want to search universities in natural language (e.g., "affordable CS in Canada") so I don't need exact keywords. | P0 |
| US-2.4 | As a student, I want to see ranking, deadlines, fees, and programs on one card so I can compare quickly. | P0 |
| US-2.5 | As a student, I want to save universities to a shortlist so I can revisit later. | P1 |

### Epic 3: Scholarship Discovery

| ID | Story | Priority |
|----|-------|----------|
| US-3.1 | As a scholarship seeker, I want to search scholarships by country and deadline so I don't miss funding. | P1 |
| US-3.2 | As a student, I want scholarships matched to my profile so I see only eligible options. | P1 |
| US-3.3 | As a student, I want to know which universities offer scholarships so I can prioritize applications. | P0 |

### Epic 4: AI Guidance

| ID | Story | Priority |
|----|-------|----------|
| US-4.1 | As a student, I want to chat with an AI counselor about study abroad so I get instant answers. | P1 |
| US-4.2 | As a student, I want AI answers grounded in my profile so advice is personalized. | P1 |
| US-4.3 | As a student, I want to compare two universities with AI so I can decide faster. | P2 |

### Epic 5: SOP & Documents

| ID | Story | Priority |
|----|-------|----------|
| US-5.1 | As an applicant, I want AI to draft an SOP from my profile so I overcome writer's block. | P1 |
| US-5.2 | As an applicant, I want to iteratively refine my SOP with AI feedback so quality improves. | P2 |
| US-5.3 | As an applicant, I want a document checklist per application so nothing is missed. | P2 |

### Epic 6: Application Tracking

| ID | Story | Priority |
|----|-------|----------|
| US-6.1 | As an applicant, I want to create and track applications by status so I see my pipeline. | P0 |
| US-6.2 | As an applicant, I want deadline reminders so I never miss a submission. | P1 |
| US-6.3 | As an applicant, I want a dashboard of all applications so I have a single source of truth. | P0 |

---

## 5. Functional Requirements

### 5.1 Authentication & Accounts

| ID | Requirement |
|----|-------------|
| FR-A1 | Email/password registration and login with JWT sessions |
| FR-A2 | Password reset via email |
| FR-A3 | User roles: student (default), admin (internal) |
| FR-A4 | Account deletion and data export (GDPR-ready) |

### 5.2 Student Profile

| ID | Requirement |
|----|-------------|
| FR-P1 | Store: nationality, education level, field of study, GPA, test scores (IELTS, TOEFL, GRE), target degree, target countries, budget range |
| FR-P2 | Profile completeness score with prompts to fill gaps |
| FR-P3 | Profile powers all recommendation and matching engines |

### 5.3 University Discovery Engine

| ID | Requirement |
|----|-------------|
| FR-U1 | University catalog with: name, country, city, ranking, tuition, fees, GPA/IELTS/TOEFL minimums, deadlines, programs, scholarships flag, website |
| FR-U2 | Filter API: country, city, major, tuition range, ranking range, GPA/IELTS thresholds, scholarships |
| FR-U3 | Keyword search across name, programs, description |
| FR-U4 | Semantic search via vector embeddings (Qdrant) |
| FR-U5 | Recommendation API: input CGPA, IELTS, budget, country, major → output Safe / Target / Ambitious lists |
| FR-U6 | Ranking algorithm weights: GPA match (25%), IELTS match (20%), budget match (25%), ranking preference (20%), scholarship availability (10%) |
| FR-U7 | University detail page with programs and requirements |

### 5.4 Scholarship Engine

| ID | Requirement |
|----|-------------|
| FR-S1 | Scholarship catalog: title, provider, country, amount, eligibility, deadline, URL |
| FR-S2 | Search and filter by country, amount, deadline |
| FR-S3 | Profile-based scholarship matching (Phase 2) |

### 5.5 AI Copilot

| ID | Requirement |
|----|-------------|
| FR-AI1 | Conversational chat with session history |
| FR-AI2 | Context injection: student profile + saved universities |
| FR-AI3 | LangGraph workflows for multi-step guidance (program comparison, gap analysis) |
| FR-AI4 | SOP generation and refinement with export (PDF/DOCX) |
| FR-AI5 | Guardrails: no guaranteed admission claims; cite sources where possible |

### 5.6 Application Tracker

| ID | Requirement |
|----|-------------|
| FR-AP1 | CRUD applications linked to university, program, and/or scholarship |
| FR-AP2 | Status workflow: draft → in_progress → submitted → accepted / rejected / withdrawn |
| FR-AP3 | Notes, deadlines, submitted date per application |
| FR-AP4 | Dashboard aggregate view with filters |

### 5.7 Notifications

| ID | Requirement |
|----|-------------|
| FR-N1 | Email reminders for deadlines (7 days, 3 days, 1 day) |
| FR-N2 | In-app notification center (Phase 2) |

### 5.8 Admin (Internal)

| ID | Requirement |
|----|-------------|
| FR-AD1 | University and scholarship data ingestion |
| FR-AD2 | Catalog quality monitoring and duplicate detection |
| FR-AD3 | Usage analytics dashboard |

---

## 6. Non-Functional Requirements

### Performance

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-P1 | API response time (p95) | < 300ms (non-AI endpoints) |
| NFR-P2 | Semantic search latency | < 2s |
| NFR-P3 | AI chat first token | < 3s |
| NFR-P4 | Concurrent users (MVP) | 1,000 |

### Reliability & Availability

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-R1 | Uptime | 99.5% (MVP) → 99.9% (GA) |
| NFR-R2 | Database backups | Daily, 30-day retention |
| NFR-R3 | Graceful degradation if Qdrant/Gemini unavailable | Fallback to keyword search or context-grounded summaries |

### Security & Privacy

| ID | Requirement |
|----|-------------|
| NFR-S1 | HTTPS everywhere; JWT with short-lived access tokens |
| NFR-S2 | Password hashing (bcrypt); no plaintext secrets |
| NFR-S3 | PII encrypted at rest; minimal data collection |
| NFR-S4 | SOC 2 readiness path for B2B/university partnerships |
| NFR-S5 | AI prompts must not leak other users' data |

### Scalability

| ID | Requirement |
|----|-------------|
| NFR-SC1 | Horizontally scalable API (stateless containers) |
| NFR-SC2 | Separate vector DB (Qdrant) from transactional DB (PostgreSQL) |
| NFR-SC3 | CDN for frontend static assets |

### Usability

| ID | Requirement |
|----|-------------|
| NFR-U1 | Mobile-responsive web (MVP); native apps (Phase 3) |
| NFR-U2 | Onboarding completable in < 5 minutes |
| NFR-U3 | WCAG 2.1 AA accessibility target (GA) |

### Maintainability

| ID | Requirement |
|----|-------------|
| NFR-M1 | Monorepo: Next.js frontend + FastAPI backend |
| NFR-M2 | API versioning (`/api/v1`) |
| NFR-M3 | Repository + service layer; Alembic migrations |
| NFR-M4 | 80%+ test coverage on ranking and recommendation logic |

---

## 7. MVP Scope

**Goal:** Validate that students will use AI-powered discovery + tracking instead of spreadsheets and Reddit.

**Timeline:** 8–12 weeks from foundation to private beta.

### In Scope (MVP)

| Area | Features |
|------|----------|
| **Auth** | Register, login, profile |
| **Discovery** | University filter, search, semantic search, Safe/Target/Ambitious recommendations |
| **Scholarships** | Browse and search (no AI matching yet) |
| **Applications** | Create, update, track status, basic dashboard |
| **AI** | Basic chat guidance (profile-aware, no SOP yet) |
| **Data** | 500+ universities (US, UK, Canada, Australia, Germany); 200+ scholarships |
| **Platform** | Web app; local development environment; API docs |

### Out of Scope (MVP)

- Native mobile apps
- SOP co-pilot (Phase 2)
- Email deadline reminders (Phase 2)
- Payment / subscriptions
- University or counselor B2B portal
- Visa workflow
- PhD supervisor matching
- Community / forum

### MVP Definition of Done

- [ ] Student can sign up, build profile, get recommendations in < 10 minutes
- [ ] 3+ universities saved and 1+ application tracked per active beta user
- [ ] Semantic search returns relevant results for 10 test queries
- [ ] NPS survey deployed; 20+ beta users onboarded

---

## 8. Future Scope

### Phase 2 — AI Copilot & Engagement (Months 4–6)

- SOP co-pilot with iterative refinement
- Scholarship profile matching
- Email/push deadline reminders
- Shortlist and compare view
- Expanded catalog (2,000+ universities, Europe + Asia)

### Phase 3 — Monetization & Growth (Months 7–12)

- Freemium: free discovery, paid AI + unlimited applications
- Premium tier: SOP reviews, mock interviews, priority support
- Referral program
- SEO content hub ("Best CS programs under $30k")
- Partnerships with test prep and loan providers (affiliate revenue)

### Phase 4 — Platform & B2B (Year 2+)

- University recruitment dashboard (analytics on applicant interest)
- High school / agency white-label
- PhD funding and supervisor discovery
- Visa document checklist by country
- Native iOS/Android apps
- Multi-language support (Hindi, Mandarin, Arabic, Spanish)

---

## 9. Success Metrics

### North Star Metric

**Applications submitted through GradPilot** — measures end-to-end value delivery.

### Product Metrics

| Metric | Definition | MVP Target | GA Target |
|--------|------------|------------|-----------|
| **Activation rate** | % signups completing profile | 60% | 75% |
| **Recommendation engagement** | % users clicking ≥3 recommended universities | 50% | 65% |
| **Shortlist rate** | % users saving ≥5 universities | 30% | 45% |
| **Application creation** | % MAU with ≥1 tracked application | 25% | 40% |
| **AI chat usage** | % MAU with ≥1 chat session/week | 20% | 35% |
| **D7 retention** | % users returning day 7 | 25% | 35% |
| **D30 retention** | % users returning day 30 | 15% | 25% |
| **Time to first recommendation** | Median seconds from signup | < 180s | < 120s |

### Quality Metrics

| Metric | Target |
|--------|--------|
| Recommendation relevance (user thumbs up/down) | ≥ 70% positive |
| Semantic search satisfaction | ≥ 65% positive |
| API error rate | < 0.5% |
| Support tickets per 100 MAU | < 5 |

---

## 10. Business KPIs

### Growth

| KPI | MVP (3 mo) | Year 1 |
|-----|------------|--------|
| Registered users | 2,000 | 50,000 |
| Monthly Active Users (MAU) | 500 | 15,000 |
| Beta → waitlist conversion | 40% | — |
| Organic traffic (SEO) | 5K visits/mo | 100K visits/mo |

### Revenue (Post-MVP)

| KPI | Year 1 Target |
|-----|---------------|
| Paid subscribers | 1,000 |
| ARPU (monthly) | $15–25 |
| MRR | $15K–$25K |
| Free → paid conversion | 5–8% |
| Affiliate revenue (loans, test prep) | $5K/mo |

### Unit Economics (Target at Scale)

| Metric | Target |
|--------|--------|
| CAC (blended) | < $20 |
| LTV | > $80 |
| LTV:CAC | > 4:1 |
| Gross margin | > 75% |
| AI cost per MAU | < $1.50/mo |

### Strategic KPIs

| KPI | Purpose |
|-----|---------|
| Applications submitted via platform | Proves workflow ownership |
| Partner university inbound interest | B2B pipeline |
| Press / community mentions | Brand in study-abroad ecosystem |
| Consultant displacement stories | Qualitative PMF signal |

---

## 11. Product Roadmap

### Q3 2026 — Foundation ✅ (Current)

| Milestone | Deliverables |
|-----------|--------------|
| **Platform foundation** | Monorepo, auth, profiles, REST APIs |
| **University Discovery Engine** | Schema, filter/search, semantic search, Qdrant, ranking, recommend API |
| **Frontend shell** | Landing, auth, dashboard scaffold |
| **Seed data** | 12+ universities; migration pipeline |

### Q4 2026 — MVP Beta

| Month | Focus | Key Ships |
|-------|-------|-----------|
| **M1** | Data & UX | 500 university ingest; discovery UI; shortlist |
| **M2** | AI v1 | Profile-aware chat; chat sessions API |
| **M3** | Applications | Full tracker UI; status dashboard; beta launch (20–50 users) |

### Q1 2027 — MVP → GA

| Month | Focus | Key Ships |
|-------|-------|-----------|
| **M4** | SOP co-pilot | Draft, refine, export |
| **M5** | Scholarships+ | Profile matching; deadline emails |
| **M6** | Monetization | Freemium launch; payment integration |

### Q2 2027 — Growth

| Focus | Key Ships |
|-------|-----------|
| SEO & content | Program guides, country comparisons |
| Referrals | Invite friends, unlock premium features |
| Mobile PWA | Installable web app |
| Catalog expansion | 2,000+ universities; Europe focus |

### H2 2027 — Platform

| Focus | Key Ships |
|-------|-----------|
| PhD track | Funding discovery, research alignment |
| B2B pilot | University analytics dashboard |
| Internationalization | Hindi, Spanish UI |
| Native apps | iOS/Android (if retention warrants) |

---

## Appendix

### Competitive Landscape

| Competitor | Strength | GradPilot Differentiation |
|------------|----------|---------------------------|
| Education consultants | Human touch | 10x cheaper, 24/7, data-driven |
| Studee, ApplyBoard | University partnerships | AI-first, student-owned workflow |
| ChatGPT / generic AI | Flexible | Profile-grounded, catalog-integrated, application tracking |
| Spreadsheets / Notion | Free, flexible | Purpose-built, recommendations, semantic search |

### Key Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Stale university data | Automated ingestion + user feedback loop |
| AI hallucinations | RAG on catalog; guardrails; human review for SOP |
| Low willingness to pay | Freemium wedge; prove value before paywall |
| Regulatory (education advice) | Disclaimers; not a licensed counselor |
| High AI costs | Gemini usage controls, caching, and usage caps on free tier |

### Open Questions

1. Which country pair is the highest-conversion wedge (India → US vs. Nigeria → UK)?
2. Should SOP co-pilot be free (acquisition) or paid (monetization)?
3. Do universities pay for applicant leads (B2B) or is B2C subscription the primary model?
4. What is the minimum catalog size for perceived completeness in beta?

---

*This document is a living artifact. Updates require Product sign-off and engineering feasibility review.*
