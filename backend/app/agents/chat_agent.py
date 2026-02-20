"""ChatMH Agent — AI chatbot with RAG for cyber scoring Q&A.

Uses Retrieval Augmented Generation:
1. Embed user query
2. Search Qdrant vector DB for relevant context
3. Compose prompt with context + query
4. Call self-hosted LLM (Mistral via vLLM)

Rules:
- Sourced responses: always reference the finding/score source
- No hallucination: if info not available, say so explicitly
- French native, English supported
- Every interaction logged for audit
- SOVEREIGN: self-hosted LLM only, no US API calls
"""

import logging
import time
from typing import Any

from app.agents.base_agent import AgentResult, BaseAgent
from app.agents.celery_app import celery_app
from app.config import settings

logger = logging.getLogger("mh_cyberscore.agents.chat")

SYSTEM_PROMPT = """Tu es ChatMH, l'assistant IA de la plateforme MH-CyberScore
de Malakoff Humanis. Tu réponds aux questions sur les scores de cybersécurité
des fournisseurs, les risques, la conformité DORA, et la gestion des risques
tiers (VRM).

Règles strictes :
1. Réponds TOUJOURS en français sauf si l'utilisateur parle anglais.
2. Source chaque information avec une référence précise (fournisseur, domaine, finding).
3. Si une information n'est pas disponible, dis-le clairement : "Cette information
   n'est pas disponible dans la base de données."
4. Ne fais JAMAIS d'hallucination — ne génère pas de données inventées.
5. Reste concis et professionnel.
"""


class ChatAgent(BaseAgent):
    """ChatMH — RAG-powered AI assistant for cyber scoring."""

    def __init__(self) -> None:
        super().__init__(name="chat", timeout=60.0)

    async def execute(self, vendor_id: str, **kwargs: Any) -> AgentResult:
        """Process a chat query with RAG-powered context.

        Args:
            vendor_id: Not used directly (chat is cross-vendor).
            **kwargs: Must contain 'message' (str), 'user_id' (str),
                     optionally 'conversation_id' (str).

        Returns:
            AgentResult with the AI response and source citations.
        """
        message = kwargs.get("message", "")
        user_id = kwargs.get("user_id", "unknown")
        conversation_id = kwargs.get("conversation_id", "")
        start = time.monotonic()

        self.logger.info(
            "Chat query from user %s: %s",
            user_id,
            message[:100],
        )

        # Step 1: Search relevant context via RAG service
        context = await self._search_context(message)
        sources = self._extract_sources(context)

        # Step 2: Compose prompt with RAG context
        prompt = self._compose_prompt(message, context)

        # Step 3: Call LLM
        try:
            response = await self._call_llm(prompt)
        except Exception as exc:
            self.logger.error("LLM call failed: %s", exc)
            response = (
                "Désolé, je ne suis pas en mesure de répondre pour le moment. "
                "Veuillez réessayer dans quelques instants."
            )

        # Format response: {"answer": "...", "sources": [...]}
        duration = time.monotonic() - start
        return AgentResult(
            agent_name=self.name,
            vendor_id=vendor_id,
            success=True,
            data={
                "response": response,
                "answer": response,
                "sources": sources,
                "user_id": user_id,
                "conversation_id": conversation_id,
                "context_chunks_used": len(context),
            },
            duration_seconds=round(duration, 2),
            api_calls_made=self._api_call_count,
        )

    async def _search_context(
        self, query: str, top_k: int = 5
    ) -> list[dict[str, Any]]:
        """Search for relevant context using the RAG service.

        Uses semantic search across scores, findings, and documents
        collections in Qdrant. Falls back gracefully if unavailable.

        Args:
            query: User query text.
            top_k: Number of results to return.

        Returns:
            List of context chunks with scores and metadata.
        """
        try:
            from app.services.llm_provider import LLMProviderConfig, get_llm_provider
            from app.services.rag_service import RAGService

            qdrant_url = settings.redis_url.replace(
                "redis://", "http://"
            ).replace(":6379", ":6333")

            llm = get_llm_provider(LLMProviderConfig(
                provider=settings.llm_default_provider,
                model_name=settings.llm_default_model,
                api_base_url=(
                    settings.ollama_base_url
                    if settings.llm_default_provider == "ollama"
                    else None
                ),
            ))

            rag = RAGService(qdrant_url=qdrant_url, llm_provider=llm)
            results = await rag.search(query, top_k=top_k)
            return results
        except Exception as exc:
            self.logger.debug("RAG context search unavailable: %s", exc)
            return []

    @staticmethod
    def _extract_sources(context: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Extract structured source citations from RAG context results.

        Args:
            context: Results from RAG search.

        Returns:
            List of source dicts with type, id, title, relevance.
        """
        sources = []
        for chunk in context:
            meta = chunk.get("metadata", {})
            source_type = meta.get("source", "document")
            title = meta.get("title", meta.get("vendor_name", ""))
            source_id = meta.get("finding_id", meta.get("doc_id", meta.get("vendor_id", "")))
            sources.append({
                "type": source_type,
                "id": source_id,
                "title": title or chunk.get("text", "")[:50],
                "relevance": round(chunk.get("score", 0), 2),
            })
        return sources

    def _compose_prompt(
        self, message: str, context: list[dict[str, Any]]
    ) -> str:
        """Compose the full prompt with system message and RAG context.

        Args:
            message: User query.
            context: Retrieved context chunks from RAG service.

        Returns:
            Formatted prompt string.
        """
        if context:
            context_lines = []
            for i, chunk in enumerate(context, 1):
                meta = chunk.get("metadata", {})
                source = meta.get("source", "inconnu")
                vendor = meta.get("vendor_name", "")
                title = meta.get("title", "")
                text = chunk.get("text", "")
                score = chunk.get("score", 0)

                header = f"[{source}]"
                if vendor:
                    header += f" Fournisseur: {vendor}"
                if title:
                    header += f" - {title}"

                context_lines.append(
                    f"{i}. {header} (pertinence: {score:.2f})\n   {text[:300]}"
                )
            context_text = "\n\n".join(context_lines)
        else:
            context_text = "Aucune donnee pertinente trouvee dans la base."

        return (
            f"{SYSTEM_PROMPT}\n\n"
            f"Contexte disponible :\n{context_text}\n\n"
            f"Question de l'utilisateur : {message}\n\n"
            f"Reponds en citant les sources. Si l'information n'est pas dans le contexte, "
            f"dis-le clairement.\n\n"
            f"Reponse :"
        )

    async def _call_llm(self, prompt: str) -> str:
        """Call the configured LLM provider.

        Args:
            prompt: Full prompt with context.

        Returns:
            LLM response text.
        """
        provider = await self._get_llm_provider()
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        return await provider.chat(messages, temperature=0.1, max_tokens=4096)


@celery_app.task(name="app.agents.chat_agent.chat_query")
def chat_query(
    user_id: str,
    message: str,
    conversation_id: str = "",
) -> dict[str, Any]:
    """Celery task: process a chat query."""
    import asyncio

    agent = ChatAgent()
    result = asyncio.run(
        agent.execute(
            vendor_id="",
            message=message,
            user_id=user_id,
            conversation_id=conversation_id,
        )
    )
    return result.data
