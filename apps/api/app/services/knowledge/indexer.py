"""Index universities, scholarships, and static guides into the knowledge base."""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_document import KnowledgeDocument
from app.models.scholarship import Scholarship
from app.models.university import University
from app.repositories.knowledge_document import KnowledgeDocumentRepository
from app.services.knowledge.retrieval.semantic import KnowledgeVectorStore

logger = logging.getLogger(__name__)

STATIC_GUIDES: list[dict] = [
    {
        "source_type": "country_guide",
        "source_id": "usa",
        "title": "Study in the United States — Country Guide",
        "content": (
            "The United States hosts 4,000+ universities. Typical requirements: GPA 3.0+, "
            "IELTS 6.5+ or TOEFL 80+, GRE for many STEM masters, SOP, 2-3 LORs, resume. "
            "F-1 student visa requires I-20 from university, SEVIS fee, DS-160, visa interview. "
            "Intakes: Fall (August) primary, Spring (January) limited. "
            "Funding: assistantships, scholarships, on-campus work (20 hrs/week)."
        ),
        "metadata": {"country": "United States"},
    },
    {
        "source_type": "country_guide",
        "source_id": "uk",
        "title": "Study in the United Kingdom — Country Guide",
        "content": (
            "UK masters are typically 1 year. Requirements: bachelor's 2:1 or equivalent (GPA 3.2+), "
            "IELTS 6.5+ (no band below 6.0). CAS letter required for Student Route visa. "
            "Intakes: September/October primary, January for some programs. "
            "Graduate Route visa allows 2 years post-study work (3 years for PhD)."
        ),
        "metadata": {"country": "United Kingdom"},
    },
    {
        "source_type": "visa_requirement",
        "source_id": "usa-f1",
        "title": "USA F-1 Student Visa Requirements",
        "content": (
            "F-1 visa steps: 1) Receive I-20 from SEVP-certified school. "
            "2) Pay SEVIS I-901 fee. 3) Complete DS-160 form. "
            "4) Schedule embassy interview. 5) Show proof of funds for tuition + living costs. "
            "6) Demonstrate ties to home country. Processing: 2-8 weeks. "
            "Maintain full-time enrollment; CPT/OPT available for work authorization."
        ),
        "metadata": {"country": "United States", "visa_type": "F-1"},
    },
    {
        "source_type": "visa_requirement",
        "source_id": "uk-student",
        "title": "UK Student Route Visa Requirements",
        "content": (
            "Student Route visa requires CAS from licensed sponsor, valid passport, "
            "financial evidence (tuition + £1,334/month London / £1,023 outside for 9 months), "
            "IELTS/SELT if required by university, TB test for certain countries. "
            "Apply up to 6 months before course start. Decision typically within 3 weeks."
        ),
        "metadata": {"country": "United Kingdom", "visa_type": "Student Route"},
    },
    {
        "source_type": "admission_requirement",
        "source_id": "masters-general",
        "title": "General Masters Admission Requirements",
        "content": (
            "Common masters requirements: bachelor's degree (4-year preferred), "
            "GPA 3.0/4.0 or 2:1 UK equivalent, IELTS 6.5+ or TOEFL 90+, "
            "Statement of Purpose (500-1000 words), 2-3 Letters of Recommendation, "
            "CV/resume, transcripts, application fee ($50-$150). "
            "STEM programs may require GRE. Deadlines: 8-12 months before intake."
        ),
        "metadata": {"degree_level": "masters"},
    },
    {
        "source_type": "sop_knowledge",
        "source_id": "sop-structure",
        "title": "Statement of Purpose — Structure & Best Practices",
        "content": (
            "Strong SOP structure: 1) Hook — personal motivation (1 paragraph). "
            "2) Academic background & relevant coursework/projects. "
            "3) Research/work experience aligned with program. "
            "4) Why this university & specific professors/labs. "
            "5) Career goals (short & long term). 6) Conclusion tying narrative together. "
            "Avoid clichés, be specific, show fit with program. Length: 500-1000 words. "
            "Tailor each SOP per university — never submit generic essays."
        ),
        "metadata": {"topic": "sop"},
    },
    {
        "source_type": "sop_knowledge",
        "source_id": "sop-mistakes",
        "title": "Common SOP Mistakes to Avoid",
        "content": (
            "Avoid: vague career goals, repeating CV verbatim, generic praise of university ranking, "
            "grammatical errors, exceeding word limit, mentioning wrong university name, "
            "focusing only on financial need, lack of program-specific research. "
            "Admissions committees want evidence of fit, intellectual curiosity, and clear trajectory."
        ),
        "metadata": {"topic": "sop"},
    },
]


class KnowledgeIndexer:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = KnowledgeDocumentRepository(db)
        self.vector_store = KnowledgeVectorStore()

    async def index_all(self) -> dict[str, int]:
        counts = {
            "universities": await self._index_universities(),
            "scholarships": await self._index_scholarships(),
            "static_guides": await self._index_static_guides(),
        }
        counts["total"] = sum(counts.values())
        return counts

    async def _index_universities(self) -> int:
        result = await self.db.execute(select(University).where(University.is_active.is_(True)))
        count = 0
        for uni in result.scalars().all():
            await self.repo.delete_by_source("university", str(uni.id))
            content = uni.build_search_text()
            doc = KnowledgeDocument(
                source_type="university",
                source_id=str(uni.id),
                title=uni.name,
                content=content,
                doc_metadata={"country": uni.country, "ranking": uni.ranking},
                token_count=len(content.split()),
            )
            doc = await self.repo.create(doc)
            self._index_vector(doc)
            count += 1
        return count

    async def _index_scholarships(self) -> int:
        result = await self.db.execute(select(Scholarship).where(Scholarship.is_active.is_(True)))
        count = 0
        for sch in result.scalars().all():
            await self.repo.delete_by_source("scholarship", str(sch.id))
            content = " ".join(
                filter(
                    None,
                    [
                        sch.title,
                        sch.provider,
                        sch.country or "",
                        sch.description or "",
                        sch.eligibility or "",
                        f"Degree: {sch.degree_level}" if sch.degree_level else "",
                        f"Min GPA: {sch.minimum_gpa}" if sch.minimum_gpa else "",
                        f"Min IELTS: {sch.minimum_ielts}" if sch.minimum_ielts else "",
                    ],
                )
            )
            doc = KnowledgeDocument(
                source_type="scholarship",
                source_id=str(sch.id),
                title=sch.title,
                content=content,
                doc_metadata={"country": sch.country, "provider": sch.provider},
                token_count=len(content.split()),
            )
            doc = await self.repo.create(doc)
            self._index_vector(doc)
            count += 1
        return count

    async def _index_static_guides(self) -> int:
        count = 0
        for guide in STATIC_GUIDES:
            await self.repo.delete_by_source(guide["source_type"], guide["source_id"])
            doc = KnowledgeDocument(
                source_type=guide["source_type"],
                source_id=guide["source_id"],
                title=guide["title"],
                content=guide["content"],
                doc_metadata=guide.get("metadata"),
                token_count=len(guide["content"].split()),
            )
            doc = await self.repo.create(doc)
            self._index_vector(doc)
            count += 1
        return count

    def _index_vector(self, doc: KnowledgeDocument) -> None:
        try:
            self.vector_store.upsert(
                document_id=doc.id,
                text=f"{doc.title}\n{doc.content}",
                payload={
                    "source_type": doc.source_type,
                    "source_id": doc.source_id,
                    "title": doc.title,
                    "content": doc.content,
                    "metadata": doc.doc_metadata or {},
                },
            )
        except Exception as exc:
            logger.warning("Vector index failed for %s: %s", doc.id, exc)
