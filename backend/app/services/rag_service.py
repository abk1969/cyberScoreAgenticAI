"""RAG Service — Retrieval Augmented Generation for CyberChat.

Indexes vendor scores, findings, and documents into Qdrant vector DB,
then provides semantic search for chat context retrieval.
"""

import logging
from typing import Any
from uuid import uuid4

from app.services.llm_provider import BaseLLMProvider

logger = logging.getLogger("cyberscore.services.rag")

COLLECTION_SCORES = "cyber_scores"
COLLECTION_FINDINGS = "cyber_findings"
COLLECTION_DOCUMENTS = "cyber_documents"
VECTOR_SIZE = 1024  # Default; adjusted on first embed call


class RAGService:
    """RAG service for semantic search over cyber scoring data."""

    def __init__(
        self,
        qdrant_url: str,
        llm_provider: BaseLLMProvider,
    ) -> None:
        self._qdrant_url = qdrant_url
        self._llm = llm_provider
        self._client: Any = None
        self._vector_size: int | None = None

    def _get_client(self) -> Any:
        """Lazily initialize the Qdrant client."""
        if self._client is None:
            from qdrant_client import QdrantClient

            self._client = QdrantClient(url=self._qdrant_url)
        return self._client

    def _ensure_collection(self, name: str, vector_size: int) -> None:
        """Create a Qdrant collection if it does not exist."""
        from qdrant_client.models import Distance, VectorParams

        client = self._get_client()
        collections = [c.name for c in client.get_collections().collections]
        if name not in collections:
            client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE,
                ),
            )
            logger.info("Created Qdrant collection: %s (dim=%d)", name, vector_size)

    async def _embed(self, text: str) -> list[float]:
        """Embed text using the configured LLM provider."""
        vector = await self._llm.embed(text)
        if self._vector_size is None:
            self._vector_size = len(vector)
        return vector

    async def index_vendor_scores(
        self, scores: list[dict[str, Any]]
    ) -> int:
        """Embed and store vendor scores in the 'scores' collection.

        Args:
            scores: List of dicts with keys like vendor_name, domain, global_score, grade.

        Returns:
            Number of points indexed.
        """
        from qdrant_client.models import PointStruct

        if not scores:
            return 0

        # Determine vector size from first embed
        sample_text = self._score_to_text(scores[0])
        sample_vec = await self._embed(sample_text)
        self._ensure_collection(COLLECTION_SCORES, len(sample_vec))

        points = []
        for sc in scores:
            text = self._score_to_text(sc)
            vector = await self._embed(text)
            points.append(PointStruct(
                id=str(uuid4()),
                vector=vector,
                payload={
                    "text": text,
                    "source": "score",
                    "vendor_id": sc.get("vendor_id", ""),
                    "vendor_name": sc.get("vendor_name", ""),
                    "global_score": sc.get("global_score", 0),
                    "grade": sc.get("grade", ""),
                },
            ))

        client = self._get_client()
        client.upsert(collection_name=COLLECTION_SCORES, points=points)
        logger.info("Indexed %d vendor scores", len(points))
        return len(points)

    async def index_findings(
        self, findings: list[dict[str, Any]]
    ) -> int:
        """Embed and store findings in the 'findings' collection.

        Args:
            findings: List of finding dicts.

        Returns:
            Number of points indexed.
        """
        from qdrant_client.models import PointStruct

        if not findings:
            return 0

        sample_text = self._finding_to_text(findings[0])
        sample_vec = await self._embed(sample_text)
        self._ensure_collection(COLLECTION_FINDINGS, len(sample_vec))

        points = []
        for f in findings:
            text = self._finding_to_text(f)
            vector = await self._embed(text)
            points.append(PointStruct(
                id=str(uuid4()),
                vector=vector,
                payload={
                    "text": text,
                    "source": "finding",
                    "finding_id": f.get("id", ""),
                    "vendor_id": f.get("vendor_id", ""),
                    "severity": f.get("severity", ""),
                    "title": f.get("title", ""),
                    "domain": f.get("domain", ""),
                },
            ))

        client = self._get_client()
        client.upsert(collection_name=COLLECTION_FINDINGS, points=points)
        logger.info("Indexed %d findings", len(points))
        return len(points)

    async def index_documents(
        self, docs: list[dict[str, Any]]
    ) -> int:
        """Embed and store documents (reports, regulations) in 'documents' collection.

        Args:
            docs: List of dicts with 'title', 'content', 'doc_type'.

        Returns:
            Number of points indexed.
        """
        from qdrant_client.models import PointStruct

        if not docs:
            return 0

        sample_vec = await self._embed(docs[0].get("content", "")[:500])
        self._ensure_collection(COLLECTION_DOCUMENTS, len(sample_vec))

        points = []
        for doc in docs:
            text = doc.get("content", "")[:2000]
            vector = await self._embed(text)
            points.append(PointStruct(
                id=str(uuid4()),
                vector=vector,
                payload={
                    "text": text,
                    "source": "document",
                    "doc_id": doc.get("id", ""),
                    "title": doc.get("title", ""),
                    "doc_type": doc.get("doc_type", ""),
                },
            ))

        client = self._get_client()
        client.upsert(collection_name=COLLECTION_DOCUMENTS, points=points)
        logger.info("Indexed %d documents", len(points))
        return len(points)

    async def search(
        self, query: str, top_k: int = 5
    ) -> list[dict[str, Any]]:
        """Semantic search across all collections.

        Args:
            query: User query text.
            top_k: Number of results per collection.

        Returns:
            Combined list of results sorted by relevance score.
        """
        query_vector = await self._embed(query)
        client = self._get_client()

        all_results: list[dict[str, Any]] = []
        collections = [COLLECTION_SCORES, COLLECTION_FINDINGS, COLLECTION_DOCUMENTS]

        for collection_name in collections:
            try:
                hits = client.search(
                    collection_name=collection_name,
                    query_vector=query_vector,
                    limit=top_k,
                    with_payload=True,
                )
                for hit in hits:
                    payload = hit.payload or {}
                    all_results.append({
                        "text": payload.get("text", ""),
                        "source": payload.get("source", collection_name),
                        "score": hit.score,
                        "metadata": payload,
                    })
            except Exception as exc:
                logger.debug(
                    "Search in %s failed (may not exist yet): %s",
                    collection_name, exc,
                )

        # Sort by relevance score descending
        all_results.sort(key=lambda r: r.get("score", 0), reverse=True)
        return all_results[:top_k]

    def build_context(
        self, query: str, results: list[dict[str, Any]]
    ) -> str:
        """Format search results into context for the LLM prompt.

        Args:
            query: Original user query.
            results: Search results from self.search().

        Returns:
            Formatted context string.
        """
        if not results:
            return "Aucune donnee pertinente trouvee dans la base."

        lines = []
        for i, r in enumerate(results, 1):
            source = r.get("source", "inconnu")
            text = r.get("text", "")
            score = r.get("score", 0)
            metadata = r.get("metadata", {})

            source_info = f"[{source}]"
            if metadata.get("vendor_name"):
                source_info += f" Fournisseur: {metadata['vendor_name']}"
            if metadata.get("title"):
                source_info += f" - {metadata['title']}"

            lines.append(f"{i}. {source_info} (pertinence: {score:.2f})\n   {text[:300]}")

        return "\n\n".join(lines)

    @staticmethod
    def _score_to_text(score: dict[str, Any]) -> str:
        """Convert a score dict to a searchable text representation."""
        parts = [
            f"Fournisseur: {score.get('vendor_name', 'inconnu')}",
            f"Score global: {score.get('global_score', 'N/A')}/1000",
            f"Grade: {score.get('grade', 'N/A')}",
        ]
        domain_scores = score.get("domain_scores", {})
        if domain_scores:
            for domain, val in domain_scores.items():
                parts.append(f"  {domain}: {val}")
        return " | ".join(parts)

    @staticmethod
    def _finding_to_text(finding: dict[str, Any]) -> str:
        """Convert a finding dict to a searchable text representation."""
        return (
            f"Finding: {finding.get('title', '')} | "
            f"Severite: {finding.get('severity', '')} | "
            f"Domaine: {finding.get('domain', '')} | "
            f"Description: {finding.get('description', '')[:200]}"
        )
