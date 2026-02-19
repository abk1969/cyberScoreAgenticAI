# MH-CyberScore AI Agents Skill

## Description
Guide for building the MH-CyberScore multi-agent system — Celery workers piloted by LLM (Mistral/LLaMA self-hosted). Use when creating OSINT agents, dark web monitors, Nth-party detection, chat agents, report generators, or any agentic AI component.

## Architecture Overview

```
ORCHESTRATOR AGENT (Chef d'orchestre)
├── OSINT Agent (Public data collection)
├── Dark Web Agent (Legal leak monitoring)
├── Nth-Party Agent (Supply chain mapping)
├── Questionnaire Agent (Smart Answer)
├── Report Agent (PDF/PPTX/Excel generation)
├── Chat Agent (ChatMH - RAG chatbot)
├── Alert Agent (Anomaly detection)
└── Compliance Agent (DORA/NIS2 mapping)
```

Each agent = Celery worker + LLM reasoning + specialized MCP tools.

## Agent Base Pattern

```python
from abc import ABC, abstractmethod
from celery import Task
from typing import Any
import logging
import httpx

logger = logging.getLogger(__name__)

class BaseAgent(Task, ABC):
    """Base class for all MH-CyberScore AI agents."""

    abstract = True
    max_retries = 3
    default_retry_delay = 60
    rate_limit = "1/s"  # Max 1 request per second per API
    soft_time_limit = 300  # 5 minutes soft limit
    time_limit = 600  # 10 minutes hard limit

    @abstractmethod
    async def execute(self, **kwargs) -> dict[str, Any]:
        """Main agent execution logic."""
        ...

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"Agent {self.name} failed: {exc}", exc_info=einfo)

    def on_success(self, retval, task_id, args, kwargs):
        logger.info(f"Agent {self.name} completed successfully: {task_id}")
```

## OSINT Agent

### Mission
Legally collect all publicly available data on a target vendor to feed the scoring engine.

### Available MCP Tools
- `shodan_search(domain)` → open ports, services, banners
- `censys_search(domain)` → certificates, exposed services
- `dns_resolve(domain)` → A, AAAA, MX, NS, TXT, SPF, DKIM, DMARC, DNSSEC
- `ssl_check(domain)` → TLS grade, certificate, chain, expiration
- `http_headers(url)` → security headers (CSP, HSTS, X-Frame, etc.)
- `cve_search(cpe_string)` → known vulnerabilities (NVD + EUVD)
- `hibp_check(domain)` → breaches associated with domain
- `whois_lookup(domain)` → registrant, dates, registrar
- `reputation_check(ip)` → AbuseIPDB, VirusTotal, blacklists
- `ct_logs_search(domain)` → issued certificates (Certificate Transparency)

### Tool Implementation Pattern
```python
import httpx
from functools import wraps
from tenacity import retry, stop_after_attempt, wait_exponential

class OsintTool:
    """Base pattern for OSINT tools."""

    def __init__(self, api_key: str, base_url: str, timeout: float = 30.0):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            timeout=timeout,
            headers={"Authorization": f"Bearer {api_key}"},
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=30))
    async def query(self, endpoint: str, params: dict) -> dict:
        response = await self.client.get(endpoint, params=params)
        response.raise_for_status()
        return response.json()

    async def close(self):
        await self.client.aclose()
```

### OSINT Legal Rules (STRICT)
```
1. PUBLICLY accessible data only (no scraping behind login)
2. Respect robots.txt of each site
3. Rate limiting: max 1 req/sec per domain
4. No active intrusive scanning (no aggressive nmap -sV)
5. Use official APIs with registered keys
6. No personal data collection (individual emails, etc.)
7. Legal basis: legitimate interest (art. 6.1.f GDPR) for supply chain security (DORA art. 28)
8. Processing register updated for each OSINT source
9. Retention: raw data 90 days, aggregated scores 3 years
10. Vendor right of opposition (documented process)
```

## Dark Web Monitor Agent

### Mission
Monitor data leaks and mentions related to evaluated vendors on legal public/semi-public sources.

### Legal Sources ONLY
- Have I Been Pwned API (breaches by domain)
- Dehashed API (credential leaks — legitimate paid API)
- IntelX API (indexed paste sites)
- GitHub/GitLab public repos (exposed secrets via regex patterns)
- Automated Google Dorks (publicly exposed documents)
- CERT-FR / ANSSI security bulletins
- Security RSS feeds (BleepingComputer, SecurityWeek, etc.)

### PROHIBITED
- Direct dark web access (.onion) without legal authorization
- Purchase of stolen data
- Use of leaked credentials for testing
- Any access requiring authentication bypass

## Nth-Party Detection Agent

### Mission
Map vendor subcontracting chain to identify concentration risks (DORA art. 28).

### Method
1. DNS/MX/headers analysis to identify cloud providers (AWS, Azure, GCP, OVH)
2. TLS certificate analysis to identify CDNs and hosters
3. Legal scraping of public pages ("privacy policy" / "subcontractors")
4. Cross-reference with internal MH vendor database
5. Build N-1, N-2, N-3 dependency graph

### Output
- Dependency graph (NetworkX format exportable to D3.js)
- Concentration risk score: % of portfolio dependent on each N-2 provider
- Alert if > 30% concentration on a single provider
- Visualization: treemap or sankey diagram

## Chat Agent (ChatMH)

### Architecture
- RAG (Retrieval Augmented Generation) on Qdrant vector DB
- Indexed: scores, findings, reports, questionnaires, PSSI, regulatory frameworks
- LLM: Mistral Large self-hosted via vLLM

### Constraints
- Responses sourced with link to finding/score source
- No hallucination: if info doesn't exist, say "not available"
- Traceability: every interaction logged for audit
- Language: native French, English supported

## Report Agent

### Capabilities
- PDF generation via WeasyPrint (HTML templates → PDF)
- PPTX generation via python-pptx (branded PowerPoint templates)
- Excel generation via openpyxl (tabular data)
- Customization: MH logo, brand guidelines, templates by audience

### Pre-built Templates
1. Executive COMEX Report (5 slides max)
2. Detailed RSSI Report (PDF 20-50 pages)
3. Vendor Scorecard (1 page)
4. DORA Register Report (structured Excel for ACPR)
5. Sectoral Benchmark Report

## Celery Configuration

```python
from celery import Celery
from app.config import settings

celery_app = Celery(
    "mh_cyberscore",
    broker=settings.celery_broker_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Europe/Paris",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,
    task_soft_time_limit=300,
    worker_prefetch_multiplier=1,
    task_routes={
        "agents.osint.*": {"queue": "osint"},
        "agents.darkweb.*": {"queue": "darkweb"},
        "agents.nthparty.*": {"queue": "nthparty"},
        "agents.report.*": {"queue": "reports"},
        "agents.chat.*": {"queue": "chat"},
    },
)
```

## Agent System Prompts
Each agent must have a system prompt in `agents/prompts/{agent_name}.md` that defines:
- Mission statement
- Available tools and their usage
- Output format specification
- Legal constraints and boundaries
- Error handling instructions
