#!/usr/bin/env python3
"""
CyberScore Database Seed Script.

Seeds the database with 50 sample vendors (realistic French companies),
sample scores, and sample findings for development and testing.

Usage:
    python scripts/seed_db.py
"""

import asyncio
import random
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql+asyncpg://csadmin:changeme_db_password@localhost:5432/cyberscore"

# --- Sample French Companies ---

TIER_1_CRITICAL = [
    ("Atos SE", "atos.net", "Infogérance & Cloud", "France"),
    ("Capgemini", "capgemini.com", "Conseil IT & Intégration", "France"),
    ("OVHcloud", "ovhcloud.com", "Hébergement Cloud Souverain", "France"),
    ("Thales", "thalesgroup.com", "Cybersécurité & Défense", "France"),
    ("Sopra Steria", "soprasteria.com", "Services Numériques", "France"),
    ("Dassault Systèmes", "3ds.com", "Logiciels Industriels", "France"),
    ("Orange Business", "orange-business.com", "Télécommunications", "France"),
    ("Worldline", "worldline.com", "Paiements & Transactions", "France"),
    ("Docaposte", "docaposte.com", "Confiance Numérique", "France"),
    ("Outscale", "outscale.com", "Cloud Souverain", "France"),
    ("Scaleway", "scaleway.com", "Cloud Européen", "France"),
    ("Bull (Eviden)", "eviden.com", "HPC & Cybersécurité", "France"),
    ("Stormshield", "stormshield.com", "Pare-feu & Sécurité Réseau", "France"),
    ("Wallix", "wallix.com", "PAM & Gestion Accès Privilégiés", "France"),
    ("Systancia", "systancia.com", "Virtualisation & Zero Trust", "France"),
]

TIER_2_IMPORTANT = [
    ("Almond", "almond.eu", "Audit Sécurité", "France"),
    ("Sekoia.io", "sekoia.io", "Threat Intelligence", "France"),
    ("Tehtris", "tehtris.com", "XDR & EDR Souverain", "France"),
    ("HarfangLab", "harfanglab.io", "EDR Français", "France"),
    ("GitGuardian", "gitguardian.com", "Secret Detection", "France"),
    ("Pradeo", "pradeo.com", "Sécurité Mobile", "France"),
    ("YesWeHack", "yeswehack.com", "Bug Bounty Européen", "France"),
    ("Alsid (Tenable)", "alsid.com", "Sécurité Active Directory", "France"),
    ("Vade Secure", "vadesecure.com", "Sécurité Email", "France"),
    ("CybelAngel", "cybelangel.com", "Détection Fuites Données", "France"),
    ("Gatewatcher", "gatewatcher.com", "NDR Souverain", "France"),
    ("Cegid", "cegid.com", "ERP & Gestion", "France"),
    ("Talend", "talend.com", "Intégration Données", "France"),
    ("ContentSquare", "contentsquare.com", "Analyse UX", "France"),
    ("Shift Technology", "shift-technology.com", "IA pour Assurance", "France"),
    ("Dataiku", "dataiku.com", "Plateforme Data Science", "France"),
    ("Algolia", "algolia.com", "Moteur de Recherche API", "France"),
    ("Mirakl", "mirakl.com", "Plateforme Marketplace", "France"),
    ("Sendinblue (Brevo)", "brevo.com", "Marketing Automation", "France"),
    ("Qonto", "qonto.com", "Services Bancaires B2B", "France"),
]

TIER_3_STANDARD = [
    ("AB Tasty", "abtasty.com", "A/B Testing", "France"),
    ("Aircall", "aircall.io", "Téléphonie Cloud", "France"),
    ("iAdvize", "iadvize.com", "Commerce Conversationnel", "France"),
    ("Ivalua", "ivalua.com", "Gestion Achats", "France"),
    ("Jahia", "jahia.com", "CMS & DXP", "France"),
    ("Kameleoon", "kameleoon.com", "Personnalisation Web", "France"),
    ("Lifen", "lifen.fr", "Santé Numérique", "France"),
    ("Lucca", "lucca.fr", "RH & Paie SaaS", "France"),
    ("Mailjet", "mailjet.com", "Envoi Email Transactionnel", "France"),
    ("Meero", "meero.com", "Production Photo IA", "France"),
    ("PayFit", "payfit.com", "Paie & RH", "France"),
    ("Planisware", "planisware.com", "Gestion de Portefeuille Projet", "France"),
    ("Saagie", "saagie.com", "DataOps Platform", "France"),
    ("Tinuiti (ex-3W)", "tinuiti.com", "Marketing Digital", "France"),
    ("Yousign", "yousign.com", "Signature Electronique", "France"),
]

FINDING_CATEGORIES = [
    "ssl_certificate_weak",
    "open_ports_critical",
    "cve_high_severity",
    "dns_misconfiguration",
    "email_spoofing_possible",
    "data_leak_detected",
    "outdated_software",
    "missing_security_headers",
    "exposed_admin_panel",
    "weak_cipher_suites",
]

SEVERITY_LEVELS = ["critical", "high", "medium", "low", "info"]


def generate_vendor_id() -> str:
    return str(uuid.uuid4())


def random_score() -> float:
    return round(random.uniform(20.0, 95.0), 1)


def random_date_within(days: int) -> datetime:
    offset = random.randint(0, days)
    return datetime.now(timezone.utc) - timedelta(days=offset)


async def seed_vendors(session: AsyncSession) -> list[dict]:
    """Insert 50 sample vendors."""
    vendors = []
    all_companies = [
        (TIER_1_CRITICAL, "critical"),
        (TIER_2_IMPORTANT, "important"),
        (TIER_3_STANDARD, "standard"),
    ]

    for companies, tier in all_companies:
        for name, domain, service_type, country in companies:
            vendor_id = generate_vendor_id()
            vendors.append({
                "id": vendor_id,
                "name": name,
                "domain": domain,
                "tier": tier,
                "service_type": service_type,
                "country": country,
            })
            await session.execute(
                text("""
                    INSERT INTO vendors (id, name, domain, tier, service_type, country, created_at, updated_at)
                    VALUES (:id, :name, :domain, :tier, :service_type, :country, NOW(), NOW())
                    ON CONFLICT (id) DO NOTHING
                """),
                {
                    "id": vendor_id,
                    "name": name,
                    "domain": domain,
                    "tier": tier,
                    "service_type": service_type,
                    "country": country,
                },
            )

    await session.flush()
    print(f"  Seeded {len(vendors)} vendors")
    return vendors


async def seed_scores(session: AsyncSession, vendors: list[dict]) -> None:
    """Insert sample scores for each vendor."""
    count = 0
    for vendor in vendors:
        score_id = generate_vendor_id()
        overall = random_score()
        await session.execute(
            text("""
                INSERT INTO vendor_scores (
                    id, vendor_id, overall_score, infra_score, app_score,
                    governance_score, data_leak_score, reputation_score,
                    calculated_at
                )
                VALUES (
                    :id, :vendor_id, :overall, :infra, :app,
                    :governance, :data_leak, :reputation,
                    :calculated_at
                )
                ON CONFLICT (id) DO NOTHING
            """),
            {
                "id": score_id,
                "vendor_id": vendor["id"],
                "overall": overall,
                "infra": random_score(),
                "app": random_score(),
                "governance": random_score(),
                "data_leak": random_score(),
                "reputation": random_score(),
                "calculated_at": random_date_within(30),
            },
        )
        count += 1

    await session.flush()
    print(f"  Seeded {count} vendor scores")


async def seed_findings(session: AsyncSession, vendors: list[dict]) -> None:
    """Insert sample findings for each vendor."""
    count = 0
    for vendor in vendors:
        num_findings = random.randint(1, 8)
        for _ in range(num_findings):
            finding_id = generate_vendor_id()
            category = random.choice(FINDING_CATEGORIES)
            severity = random.choice(SEVERITY_LEVELS)
            await session.execute(
                text("""
                    INSERT INTO findings (
                        id, vendor_id, category, severity, title,
                        description, source, detected_at, status
                    )
                    VALUES (
                        :id, :vendor_id, :category, :severity, :title,
                        :description, :source, :detected_at, :status
                    )
                    ON CONFLICT (id) DO NOTHING
                """),
                {
                    "id": finding_id,
                    "vendor_id": vendor["id"],
                    "category": category,
                    "severity": severity,
                    "title": f"{category.replace('_', ' ').title()} - {vendor['domain']}",
                    "description": f"Automated finding: {category} detected on {vendor['domain']}",
                    "source": random.choice(["osint_agent", "darkweb_agent", "manual_audit"]),
                    "detected_at": random_date_within(90),
                    "status": random.choice(["open", "acknowledged", "resolved", "false_positive"]),
                },
            )
            count += 1

    await session.flush()
    print(f"  Seeded {count} findings")


async def main() -> None:
    print("CyberScore Database Seeder")
    print("=" * 40)

    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        async with session.begin():
            print("Seeding vendors...")
            vendors = await seed_vendors(session)

            print("Seeding scores...")
            await seed_scores(session, vendors)

            print("Seeding findings...")
            await seed_findings(session, vendors)

        await session.commit()

    await engine.dispose()
    print("=" * 40)
    print("Seeding complete.")


if __name__ == "__main__":
    asyncio.run(main())
