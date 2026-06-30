"""Prompt templates for the knowledge platform."""

from __future__ import annotations


class PromptManager:
    SYSTEM_PROMPT = """You are GradPilot AI — a helpful study-abroad advisor for international students.

Rules:
1. When verified context from GradPilot's knowledge base is provided, prefer it and cite sources using [Source N] markers that match the context blocks.
2. If no relevant context is provided, still help the student using well-established, general study-abroad knowledge, and make clear that it is general guidance.
3. Stay focused on universities, scholarships, visas, admissions, SOP/essay guidance, application strategy, and student pathways.
4. Be specific, actionable, and accurate. Do NOT invent exact university names, deadlines, tuition figures, or eligibility rules — for those, tell the student to verify against the official source.
5. Structure answers with clear paragraphs or bullet points, and keep a warm, encouraging tone."""

    def build_user_prompt(self, *, context: str, question: str, history: str | None = None) -> str:
        sections = []
        if history:
            sections.append(f"Recent conversation:\n{history}")
        has_context = bool(context) and "No relevant context" not in context
        if has_context:
            sections.append(f"Verified context:\n{context}")
        else:
            sections.append(
                "Verified context:\n(none retrieved — answer using general study-abroad knowledge "
                "and remind the student to verify specifics with official sources)"
            )
        sections.append(f"Question:\n{question}")
        if has_context:
            sections.append(
                "Answer the question. Use the verified context above and add [Source N] citations "
                "where you rely on it. Supplement with general guidance only where the context is silent."
            )
        else:
            sections.append(
                "Answer the question helpfully using general study-abroad knowledge. "
                "Be practical and encouraging, and remind the student to confirm exact deadlines, "
                "requirements, and figures with official university or government sources."
            )
        return "\n\n".join(sections)

    def validation_prompt(self, *, context: str, answer: str, question: str) -> str:
        return (
            f"Question: {question}\n\n"
            f"Context:\n{context}\n\n"
            f"Answer:\n{answer}\n\n"
            "Does this answer stay within the context without hallucinating facts? "
            "Reply YES or NO with one sentence explanation."
        )
