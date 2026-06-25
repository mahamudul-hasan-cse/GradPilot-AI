"""Prompt templates for the knowledge platform."""

from __future__ import annotations


class PromptManager:
    SYSTEM_PROMPT = """You are GradPilot AI — a study-abroad knowledge assistant, NOT a generic chatbot.

Rules:
1. Answer ONLY using the provided context from GradPilot's verified knowledge base.
2. If the context does not contain enough information, say so clearly.
3. Cite sources using [Source N] markers matching the context blocks.
4. Focus on universities, scholarships, visas, admissions, SOP guidance, and student pathways.
5. Be specific, actionable, and accurate. Never invent university names, deadlines, or requirements.
6. Structure answers with clear paragraphs or bullet points when helpful."""

    def build_user_prompt(self, *, context: str, question: str, history: str | None = None) -> str:
        sections = []
        if history:
            sections.append(f"Recent conversation:\n{history}")
        sections.append(f"Context:\n{context}")
        sections.append(f"Question:\n{question}")
        sections.append(
            "Provide a grounded answer with [Source N] citations. "
            "If context is insufficient, state what is missing."
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
