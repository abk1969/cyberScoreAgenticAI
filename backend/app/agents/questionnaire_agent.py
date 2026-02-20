"""Celery agent for questionnaire smart-answer suggestions using LLM."""

import asyncio
import json
import logging
from typing import Any

from app.agents.base_agent import AgentResult, BaseAgent
from app.agents.celery_app import celery_app

logger = logging.getLogger("cyberscore.agents.questionnaire")


class QuestionnaireAgent(BaseAgent):
    """Agent that generates smart answer suggestions for questionnaire questions."""

    def __init__(self) -> None:
        super().__init__(name="questionnaire", timeout=60.0)

    async def execute(self, vendor_id: str, **kwargs: Any) -> AgentResult:
        """Generate smart answer suggestions for a set of questions.

        Uses RAG to search past answers and vendor scan data for context,
        then generates answer suggestions with confidence scores.

        Args:
            vendor_id: The vendor ID for context.
            **kwargs:
                questions: List of question dicts with 'id' and 'text'.
                vendor_context: Optional context about the vendor.

        Returns:
            AgentResult with suggested answers and confidence scores.
        """
        import time

        start = time.monotonic()
        questions = kwargs.get("questions", [])
        vendor_context = kwargs.get("vendor_context", "")

        if not questions:
            return AgentResult(
                agent_name=self.name,
                vendor_id=vendor_id,
                success=False,
                errors=["No questions provided"],
            )

        try:
            llm = await self._get_llm_provider()
            suggestions = {}

            # Initialize RAG service for context enrichment
            rag_context = await self._get_rag_context(vendor_id, llm)

            for q in questions:
                # Search RAG for question-specific context
                question_context = await self._search_rag_for_question(
                    q.get("text", ""), llm
                )

                # Combine vendor context with RAG context
                enriched_context = vendor_context
                if rag_context:
                    enriched_context += f"\n\nDonnees du fournisseur:\n{rag_context}"
                if question_context:
                    enriched_context += f"\n\nContexte pertinent:\n{question_context}"

                prompt = self._build_prompt(q, enriched_context)
                response_text = await self._rate_limited_call(
                    llm.chat(
                        messages=[
                            {"role": "system", "content": self._system_prompt()},
                            {"role": "user", "content": prompt},
                        ],
                        temperature=0.2,
                        max_tokens=1024,
                    ),
                    source="llm_smart_answer",
                    question_id=q.get("id"),
                )

                try:
                    parsed = json.loads(response_text)
                    # Boost confidence if RAG context was available
                    base_confidence = float(parsed.get("confidence", 0.5))
                    if question_context:
                        base_confidence = min(base_confidence + 0.15, 1.0)

                    suggestions[q["id"]] = {
                        "answer": parsed.get("answer", response_text),
                        "confidence": min(max(base_confidence, 0.0), 1.0),
                        "reasoning": parsed.get("reasoning"),
                        "rag_enhanced": bool(question_context),
                    }
                except (json.JSONDecodeError, KeyError):
                    suggestions[q["id"]] = {
                        "answer": response_text,
                        "confidence": 0.3,
                        "reasoning": "Reponse brute du modele",
                        "rag_enhanced": False,
                    }

            duration = time.monotonic() - start
            return AgentResult(
                agent_name=self.name,
                vendor_id=vendor_id,
                success=True,
                data={"suggestions": suggestions},
                duration_seconds=round(duration, 2),
                api_calls_made=self._api_call_count,
            )

        except Exception as exc:
            duration = time.monotonic() - start
            logger.error("QuestionnaireAgent failed: %s", exc)
            return AgentResult(
                agent_name=self.name,
                vendor_id=vendor_id,
                success=False,
                errors=[str(exc)],
                duration_seconds=round(duration, 2),
                api_calls_made=self._api_call_count,
            )

    async def _get_rag_context(self, vendor_id: str, llm: Any) -> str:
        """Fetch vendor-specific context from RAG for smart answers.

        Args:
            vendor_id: Vendor UUID.
            llm: LLM provider instance.

        Returns:
            Context string or empty string if unavailable.
        """
        try:
            from app.config import settings
            from app.services.rag_service import RAGService

            qdrant_url = settings.redis_url.replace(
                "redis://", "http://"
            ).replace(":6379", ":6333")
            rag = RAGService(qdrant_url=qdrant_url, llm_provider=llm)

            results = await rag.search(f"vendor {vendor_id} score findings", top_k=3)
            if results:
                return rag.build_context(f"vendor {vendor_id}", results)
        except Exception as exc:
            logger.debug("RAG context unavailable for smart answers: %s", exc)
        return ""

    async def _search_rag_for_question(self, question_text: str, llm: Any) -> str:
        """Search RAG for context relevant to a specific question.

        Args:
            question_text: The question text to search for.
            llm: LLM provider instance.

        Returns:
            Context string or empty string.
        """
        try:
            from app.config import settings
            from app.services.rag_service import RAGService

            qdrant_url = settings.redis_url.replace(
                "redis://", "http://"
            ).replace(":6379", ":6333")
            rag = RAGService(qdrant_url=qdrant_url, llm_provider=llm)

            results = await rag.search(question_text, top_k=3)
            if results:
                return rag.build_context(question_text, results)
        except Exception as exc:
            logger.debug("RAG question search unavailable: %s", exc)
        return ""

    @staticmethod
    def _system_prompt() -> str:
        return (
            "Tu es un expert en cybersecurite et conformite reglementaire. "
            "Tu aides a repondre a des questionnaires d'evaluation de securite des fournisseurs. "
            "Reponds en francais de maniere professionnelle et concise. "
            "Reponds au format JSON: {\"answer\": \"...\", \"confidence\": 0.0-1.0, \"reasoning\": \"...\"}"
        )

    @staticmethod
    def _build_prompt(question: dict, vendor_context: str) -> str:
        prompt = f"Question: {question.get('text', '')}\n"
        options = question.get("options")
        if options and isinstance(options, dict) and options.get("choices"):
            prompt += f"Choix possibles: {', '.join(options['choices'])}\n"
        if vendor_context:
            prompt += f"Contexte du fournisseur: {vendor_context}\n"
        prompt += "\nSuggere une reponse appropriee au format JSON demande."
        return prompt


# ── Celery task ─────────────────────────────────────────────────────────

@celery_app.task(name="app.agents.questionnaire_agent.generate_smart_answers", bind=True)
def generate_smart_answers(self, vendor_id: str, questions: list[dict], vendor_context: str = "") -> dict:
    """Celery task to generate smart answer suggestions.

    Args:
        vendor_id: Vendor UUID.
        questions: List of question dicts.
        vendor_context: Optional vendor context.

    Returns:
        AgentResult as dict.
    """
    agent = QuestionnaireAgent()
    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(
            agent.execute(vendor_id, questions=questions, vendor_context=vendor_context)
        )
        return {
            "agent_name": result.agent_name,
            "vendor_id": result.vendor_id,
            "success": result.success,
            "data": result.data,
            "errors": result.errors,
            "duration_seconds": result.duration_seconds,
            "api_calls_made": result.api_calls_made,
        }
    finally:
        loop.close()
