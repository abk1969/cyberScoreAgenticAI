"""Questionnaire service with templates and LLM-powered smart answers."""

import json
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.questionnaire import Answer, Question, Questionnaire, QuestionnaireResponse
from app.schemas.questionnaire import (
    AnswerSubmission,
    QuestionnaireCreateRequest,
    QuestionnaireListItem,
    QuestionnaireResponse as QuestionnaireResponseSchema,
    QuestionnaireSubmitResponse,
    QuestionnaireSendRequest,
    QuestionnaireSendResponse,
    QuestionnaireTemplateInfo,
    SmartAnswerRequest,
    SmartAnswerResponse,
)

logger = logging.getLogger("cyberscore.questionnaire_service")

# ── Built-in questionnaire templates ────────────────────────────────────

TEMPLATES: dict[str, dict[str, Any]] = {
    "RGPD": {
        "title": "Questionnaire RGPD",
        "description": "Evaluation de la conformite au Reglement General sur la Protection des Donnees",
        "category": "rgpd",
        "questions": [
            {"text": "Avez-vous designe un DPO (Delegue a la Protection des Donnees) ?", "type": "single_choice", "options": {"choices": ["Oui", "Non", "En cours"]}, "weight": 2.0, "category": "gouvernance"},
            {"text": "Tenez-vous un registre des traitements de donnees personnelles ?", "type": "single_choice", "options": {"choices": ["Oui", "Non", "Partiel"]}, "weight": 2.0, "category": "registre"},
            {"text": "Avez-vous mis en place des analyses d'impact (AIPD) pour les traitements a risque ?", "type": "single_choice", "options": {"choices": ["Oui", "Non", "En cours"]}, "weight": 1.5, "category": "analyse_impact"},
            {"text": "Comment gerez-vous les droits des personnes concernees (acces, rectification, suppression) ?", "type": "text", "weight": 1.5, "category": "droits"},
            {"text": "Disposez-vous d'une procedure de notification de violation de donnees ?", "type": "single_choice", "options": {"choices": ["Oui", "Non", "En cours"]}, "weight": 2.0, "category": "violation"},
            {"text": "Les transferts de donnees hors UE sont-ils encadres (clauses contractuelles types, adequation) ?", "type": "single_choice", "options": {"choices": ["Oui", "Non", "Non concerne"]}, "weight": 1.5, "category": "transferts"},
            {"text": "Formez-vous regulierement vos collaborateurs a la protection des donnees ?", "type": "single_choice", "options": {"choices": ["Oui", "Non", "Occasionnellement"]}, "weight": 1.0, "category": "formation"},
        ],
    },
    "DORA": {
        "title": "Questionnaire DORA",
        "description": "Evaluation de la conformite au reglement sur la resilience operationnelle numerique (DORA)",
        "category": "dora",
        "questions": [
            {"text": "Disposez-vous d'un cadre de gestion des risques TIC documente et approuve par la direction ?", "type": "single_choice", "options": {"choices": ["Oui", "Non", "En cours"]}, "weight": 2.0, "category": "gouvernance_tic"},
            {"text": "Realisez-vous des tests de resilience operationnelle numerique (TLPT, tests de penetration) ?", "type": "single_choice", "options": {"choices": ["Oui, regulierement", "Oui, ponctuellement", "Non"]}, "weight": 2.0, "category": "tests_resilience"},
            {"text": "Comment gerez-vous les incidents TIC majeurs (detection, classification, notification) ?", "type": "text", "weight": 1.5, "category": "gestion_incidents"},
            {"text": "Disposez-vous d'un plan de continuite d'activite (PCA) et de reprise d'activite (PRA) testes ?", "type": "single_choice", "options": {"choices": ["Oui", "Non", "Partiellement"]}, "weight": 2.0, "category": "continuite"},
            {"text": "Comment evaluez-vous et surveillez-vous les risques lies a vos prestataires TIC tiers ?", "type": "text", "weight": 1.5, "category": "tiers"},
            {"text": "Partagez-vous des informations sur les cybermenaces avec d'autres entites financieres ?", "type": "single_choice", "options": {"choices": ["Oui", "Non", "En cours"]}, "weight": 1.0, "category": "partage_info"},
        ],
    },
    "ISO27001": {
        "title": "Questionnaire ISO 27001",
        "description": "Evaluation de la conformite au systeme de management de la securite de l'information",
        "category": "iso27001",
        "questions": [
            {"text": "Disposez-vous d'une politique de securite de l'information approuvee par la direction ?", "type": "single_choice", "options": {"choices": ["Oui", "Non", "En cours"]}, "weight": 2.0, "category": "politique"},
            {"text": "Avez-vous realise une analyse des risques de securite de l'information ?", "type": "single_choice", "options": {"choices": ["Oui", "Non", "En cours"]}, "weight": 2.0, "category": "analyse_risques"},
            {"text": "Etes-vous certifie ISO 27001 ? Si oui, quelle est la date de validite ?", "type": "text", "weight": 2.0, "category": "certification"},
            {"text": "Comment gerez-vous le controle d'acces aux systemes d'information ?", "type": "text", "weight": 1.5, "category": "controle_acces"},
            {"text": "Disposez-vous d'un processus de gestion des vulnerabilites et des correctifs ?", "type": "single_choice", "options": {"choices": ["Oui", "Non", "Partiel"]}, "weight": 1.5, "category": "vulnerabilites"},
            {"text": "Realisez-vous des audits internes reguliers du SMSI ?", "type": "single_choice", "options": {"choices": ["Oui", "Non", "Occasionnellement"]}, "weight": 1.5, "category": "audit"},
            {"text": "Comment assurez-vous la securite dans vos relations avec les fournisseurs ?", "type": "text", "weight": 1.0, "category": "fournisseurs"},
        ],
    },
    "NIST_CSF": {
        "title": "Questionnaire NIST CSF",
        "description": "Evaluation basee sur le NIST Cybersecurity Framework (Identify, Protect, Detect, Respond, Recover)",
        "category": "nist_csf",
        "questions": [
            {"text": "Avez-vous un inventaire a jour de vos actifs informatiques (materiels, logiciels, donnees) ?", "type": "single_choice", "options": {"choices": ["Oui", "Non", "Partiel"]}, "weight": 1.5, "category": "identify"},
            {"text": "Comment identifiez-vous et evaluez-vous les risques cyber pour votre organisation ?", "type": "text", "weight": 1.5, "category": "identify"},
            {"text": "Quelles mesures de protection avez-vous mises en place (chiffrement, MFA, segmentation) ?", "type": "text", "weight": 2.0, "category": "protect"},
            {"text": "Disposez-vous de capacites de detection des incidents (SIEM, SOC, monitoring) ?", "type": "single_choice", "options": {"choices": ["Oui", "Non", "Externalise"]}, "weight": 2.0, "category": "detect"},
            {"text": "Avez-vous un plan de reponse aux incidents cyber teste et a jour ?", "type": "single_choice", "options": {"choices": ["Oui", "Non", "En cours"]}, "weight": 2.0, "category": "respond"},
            {"text": "Disposez-vous d'un plan de reprise d'activite cyber teste ?", "type": "single_choice", "options": {"choices": ["Oui", "Non", "En cours"]}, "weight": 1.5, "category": "recover"},
        ],
    },
    "HDS": {
        "title": "Questionnaire HDS",
        "description": "Evaluation de la conformite a l'hebergement de donnees de sante (HDS)",
        "category": "hds",
        "questions": [
            {"text": "Etes-vous certifie HDS ? Si oui, pour quels niveaux d'activite ?", "type": "text", "weight": 2.0, "category": "certification"},
            {"text": "Comment assurez-vous la confidentialite des donnees de sante hebergees ?", "type": "text", "weight": 2.0, "category": "confidentialite"},
            {"text": "Disposez-vous d'un systeme de gestion de la securite de l'information (ISO 27001) ?", "type": "single_choice", "options": {"choices": ["Oui", "Non", "En cours"]}, "weight": 1.5, "category": "smsi"},
            {"text": "Comment gerez-vous la tracabilite des acces aux donnees de sante ?", "type": "text", "weight": 1.5, "category": "tracabilite"},
            {"text": "Ou sont localises physiquement vos centres de donnees ?", "type": "text", "weight": 1.0, "category": "localisation"},
            {"text": "Disposez-vous d'un plan de continuite et de reprise d'activite specifique aux donnees de sante ?", "type": "single_choice", "options": {"choices": ["Oui", "Non", "En cours"]}, "weight": 1.5, "category": "continuite"},
        ],
    },
}


class QuestionnaireService:
    """Service layer for questionnaire management and smart answers."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Templates ───────────────────────────────────────────────────

    def list_templates(self) -> list[QuestionnaireTemplateInfo]:
        """Return available questionnaire templates."""
        return [
            QuestionnaireTemplateInfo(
                name=key,
                description=tpl["description"],
                category=tpl["category"],
                question_count=len(tpl["questions"]),
            )
            for key, tpl in TEMPLATES.items()
        ]

    # ── Create from template ────────────────────────────────────────

    async def create_from_template(
        self, data: QuestionnaireCreateRequest
    ) -> QuestionnaireResponseSchema:
        """Create a questionnaire instance from a built-in template.

        Args:
            data: Creation request with template name and vendor ID.

        Returns:
            Created questionnaire with questions.

        Raises:
            ValueError: If the template name is unknown.
        """
        tpl = TEMPLATES.get(data.template_name)
        if not tpl:
            raise ValueError(
                f"Unknown template: {data.template_name!r}. "
                f"Available: {', '.join(TEMPLATES)}"
            )

        questionnaire = Questionnaire(
            title=data.title or tpl["title"],
            description=tpl["description"],
            category=tpl["category"],
        )
        self.db.add(questionnaire)
        await self.db.flush()

        for idx, q_data in enumerate(tpl["questions"]):
            question = Question(
                questionnaire_id=questionnaire.id,
                order=idx + 1,
                text=q_data["text"],
                question_type=q_data.get("type", "text"),
                options=q_data.get("options"),
                weight=q_data.get("weight"),
                category=q_data.get("category"),
            )
            self.db.add(question)

        await self.db.flush()
        await self.db.refresh(questionnaire)
        return QuestionnaireResponseSchema.model_validate(questionnaire)

    # ── List / Get ──────────────────────────────────────────────────

    async def list_questionnaires(self) -> list[QuestionnaireListItem]:
        """List all questionnaires."""
        result = await self.db.execute(
            select(Questionnaire).order_by(Questionnaire.created_at.desc())
        )
        items = result.scalars().all()
        return [QuestionnaireListItem.model_validate(q) for q in items]

    async def get_questionnaire(self, questionnaire_id: str) -> QuestionnaireResponseSchema:
        """Get a questionnaire with its questions.

        Args:
            questionnaire_id: Questionnaire UUID.

        Returns:
            Questionnaire with questions.

        Raises:
            ValueError: If not found.
        """
        result = await self.db.execute(
            select(Questionnaire).where(Questionnaire.id == questionnaire_id)
        )
        questionnaire = result.scalar_one_or_none()
        if not questionnaire:
            raise ValueError(f"Questionnaire not found: {questionnaire_id}")
        return QuestionnaireResponseSchema.model_validate(questionnaire)

    # ── Send ────────────────────────────────────────────────────────

    async def send_questionnaire(
        self, questionnaire_id: str, data: QuestionnaireSendRequest
    ) -> QuestionnaireSendResponse:
        """Create a response record and 'send' the questionnaire to a vendor.

        Args:
            questionnaire_id: Questionnaire UUID.
            data: Send request with vendor ID and recipient email.

        Returns:
            Send response with new response ID.
        """
        result = await self.db.execute(
            select(Questionnaire).where(Questionnaire.id == questionnaire_id)
        )
        questionnaire = result.scalar_one_or_none()
        if not questionnaire:
            raise ValueError(f"Questionnaire not found: {questionnaire_id}")

        response = QuestionnaireResponse(
            questionnaire_id=questionnaire_id,
            vendor_id=data.vendor_id,
            submitted_by=data.recipient_email,
            status="sent",
        )
        self.db.add(response)
        await self.db.flush()
        await self.db.refresh(response)

        return QuestionnaireSendResponse(
            response_id=response.id,
            questionnaire_id=questionnaire_id,
            vendor_id=data.vendor_id,
            status="sent",
            message=f"Questionnaire envoye a {data.recipient_email}",
        )

    # ── Submit response ─────────────────────────────────────────────

    async def submit_response(
        self, questionnaire_id: str, vendor_id: str, answers: list[AnswerSubmission]
    ) -> QuestionnaireSubmitResponse:
        """Submit answers to a questionnaire and compute score.

        Args:
            questionnaire_id: Questionnaire UUID.
            vendor_id: Vendor UUID.
            answers: List of answer submissions.

        Returns:
            Submission response with computed score.
        """
        # Find or create the response record
        result = await self.db.execute(
            select(QuestionnaireResponse).where(
                QuestionnaireResponse.questionnaire_id == questionnaire_id,
                QuestionnaireResponse.vendor_id == vendor_id,
            )
        )
        qr = result.scalar_one_or_none()
        if not qr:
            qr = QuestionnaireResponse(
                questionnaire_id=questionnaire_id,
                vendor_id=vendor_id,
                status="draft",
            )
            self.db.add(qr)
            await self.db.flush()

        # Save answers
        for ans in answers:
            answer = Answer(
                response_id=qr.id,
                question_id=ans.question_id,
                value=ans.value,
            )
            self.db.add(answer)

        qr.status = "submitted"
        qr.submitted_at = datetime.now(timezone.utc)

        # Compute combined score
        score = await self._calculate_combined_score(questionnaire_id, answers)
        qr.score = score

        await self.db.flush()
        await self.db.refresh(qr)

        return QuestionnaireSubmitResponse(
            response_id=qr.id,
            status="submitted",
            score=score,
            message="Reponses soumises avec succes",
        )

    async def _calculate_combined_score(
        self, questionnaire_id: str, answers: list[AnswerSubmission]
    ) -> float:
        """Calculate a weighted score from submitted answers.

        Positive answers ('Oui', 'Oui, regulierement') score 1.0,
        partial answers score 0.5, negative score 0.0.
        Text answers score 0.5 by default.

        Args:
            questionnaire_id: Questionnaire UUID.
            answers: Submitted answers.

        Returns:
            Score between 0.0 and 100.0.
        """
        result = await self.db.execute(
            select(Question).where(Question.questionnaire_id == questionnaire_id)
        )
        questions = {q.id: q for q in result.scalars().all()}

        answer_map = {a.question_id: a.value for a in answers}
        total_weight = 0.0
        weighted_score = 0.0

        positive_keywords = {"oui", "oui, regulierement", "oui, regulièrement"}
        partial_keywords = {"en cours", "partiel", "partiellement", "occasionnellement", "externalise", "externalise"}

        for qid, question in questions.items():
            weight = question.weight or 1.0
            total_weight += weight
            value = (answer_map.get(qid) or "").strip().lower()

            if not value:
                continue

            if question.question_type == "text":
                # Text answers get 0.5 if they have content
                weighted_score += weight * 0.5
            elif value in positive_keywords:
                weighted_score += weight * 1.0
            elif value in partial_keywords:
                weighted_score += weight * 0.5

        if total_weight == 0:
            return 0.0
        return round((weighted_score / total_weight) * 100, 1)

    # ── Smart Answer (LLM) ──────────────────────────────────────────

    async def smart_answer_suggestion(
        self, questionnaire_id: str, data: SmartAnswerRequest
    ) -> SmartAnswerResponse:
        """Generate an AI-powered answer suggestion for a question.

        Args:
            questionnaire_id: Questionnaire UUID.
            data: Smart answer request with question ID and optional context.

        Returns:
            AI-generated answer suggestion.
        """
        result = await self.db.execute(
            select(Question).where(Question.id == data.question_id)
        )
        question = result.scalar_one_or_none()
        if not question:
            raise ValueError(f"Question not found: {data.question_id}")

        # Build prompt
        system_prompt = (
            "Tu es un expert en cybersecurite et conformite reglementaire. "
            "Tu aides a repondre a des questionnaires d'evaluation de securite des fournisseurs. "
            "Reponds en francais de maniere professionnelle et concise."
        )

        user_prompt = f"Question: {question.text}\n"
        if question.options and question.options.get("choices"):
            choices = ", ".join(question.options["choices"])
            user_prompt += f"Choix possibles: {choices}\n"
        if data.vendor_context:
            user_prompt += f"Contexte du fournisseur: {data.vendor_context}\n"
        user_prompt += (
            "\nSuggere une reponse appropriee. "
            "Reponds au format JSON: {\"answer\": \"...\", \"confidence\": 0.0-1.0, \"reasoning\": \"...\"}"
        )

        try:
            llm = await self._get_llm_provider()
            response_text = await llm.chat(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
                max_tokens=1024,
            )

            # Parse LLM response
            parsed = json.loads(response_text)
            return SmartAnswerResponse(
                question_id=data.question_id,
                suggested_answer=parsed.get("answer", response_text),
                confidence=min(max(float(parsed.get("confidence", 0.5)), 0.0), 1.0),
                reasoning=parsed.get("reasoning"),
            )
        except (json.JSONDecodeError, KeyError):
            return SmartAnswerResponse(
                question_id=data.question_id,
                suggested_answer=response_text if "response_text" in dir() else "Suggestion non disponible",
                confidence=0.3,
                reasoning="Reponse brute du modele LLM",
            )
        except Exception as exc:
            logger.warning("Smart answer LLM call failed: %s", exc)
            return SmartAnswerResponse(
                question_id=data.question_id,
                suggested_answer="Suggestion non disponible — verifiez la configuration LLM",
                confidence=0.0,
                reasoning=str(exc),
            )

    async def _get_llm_provider(self):
        """Load the active LLM config from DB and return a provider instance."""
        import base64

        from app.config import settings
        from app.models.llm_config import LLMConfig
        from app.services.llm_provider import LLMProviderConfig, get_llm_provider

        result = await self.db.execute(
            select(LLMConfig).where(LLMConfig.is_active.is_(True)).limit(1)
        )
        cfg = result.scalar_one_or_none()

        if cfg is not None:
            api_key = None
            if cfg.api_key_encrypted and settings.encryption_key:
                from app.utils.crypto import decrypt_data

                enc_key = base64.b64decode(settings.encryption_key)
                api_key = decrypt_data(cfg.api_key_encrypted, enc_key)
            return get_llm_provider(
                LLMProviderConfig(
                    provider=cfg.provider,
                    model_name=cfg.model_name,
                    api_key=api_key,
                    api_base_url=cfg.api_base_url,
                )
            )

        return get_llm_provider(
            LLMProviderConfig(
                provider=settings.llm_default_provider,
                model_name=settings.llm_default_model,
                api_base_url=(
                    settings.ollama_base_url
                    if settings.llm_default_provider == "ollama"
                    else None
                ),
            )
        )
