# MH-CyberScore Scoring Engine Skill

## Description
Guide for implementing the MH-CyberScore scoring methodology — the core algorithm that rates vendor cybersecurity posture. Use when building the scoring engine, domain analyzers, grading logic, or any scoring-related code.

## Scoring Overview

### Score Structure
- **Global Score**: 0-1000 + Grade A-F
- **Domain Score**: 0-100 + Grade A-E per domain
- **8 Scoring Domains** (fusion SecurityScorecard + Board of Cyber enriched)

### The 8 Domains

| # | Domain | OSINT Sources | Default Weight |
|---|--------|--------------|----------------|
| D1 | Network Security | Shodan API, Censys, CT logs | 15% |
| D2 | DNS Security | DNS passive (DNSDB), SPF/DKIM/DMARC, DNSSEC | 10% |
| D3 | Web Security | HTTP headers, TLS/SSL Labs, CSP, HSTS, cookies | 15% |
| D4 | Email Security | SPF, DKIM, DMARC, MTA-STS, BIMI, DANE, blacklists | 10% |
| D5 | Patching Cadence | CVE matching NVD/EUVD, version fingerprinting | 15% |
| D6 | IP Reputation | AbuseIPDB, VirusTotal, blacklists, sinkhole feeds | 10% |
| D7 | Leaks & Exposure | HIBP, Dehashed, paste sites | 15% |
| D8 | Regulatory Presence | Legal notices, privacy policy, published certifications | 10% |

### Scoring Algorithm

```python
"""
GLOBAL SCORING FORMULA:
  score_global = sum(score_domain_i * weight_i * criticality_factor_i)

Where:
  - score_domain_i in [0, 100]: normalized domain score
  - weight_i in [0, 1]: configurable weighting (defaults above)
  - criticality_factor_i: multiplier based on findings criticality
    - Critical (CVSS >= 9.0): x2.0
    - High (CVSS 7.0-8.9): x1.5
    - Medium (CVSS 4.0-6.9): x1.0
    - Low (CVSS < 4.0): x0.5

GRADE MAPPING:
  A: 800-1000 (Excellent)
  B: 600-799  (Good)
  C: 400-599  (Acceptable)
  D: 200-399  (Weak)
  F: 0-199    (Critical)

ORGANIZATION SIZE NORMALIZATION:
  - Micro (< 10 employees): tolerance +15%
  - SME (10-250): tolerance +10%
  - Mid-market (250-5000): standard
  - Enterprise (> 5000): requirement +10%
"""
```

## Implementation Guide

### Scoring Engine Service
```python
from enum import Enum
from dataclasses import dataclass

class Grade(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    F = "F"

class CriticalityLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

CRITICALITY_FACTORS = {
    CriticalityLevel.CRITICAL: 2.0,
    CriticalityLevel.HIGH: 1.5,
    CriticalityLevel.MEDIUM: 1.0,
    CriticalityLevel.LOW: 0.5,
    CriticalityLevel.INFO: 0.0,
}

DEFAULT_DOMAIN_WEIGHTS = {
    "network_security": 0.15,
    "dns_security": 0.10,
    "web_security": 0.15,
    "email_security": 0.10,
    "patching_cadence": 0.15,
    "ip_reputation": 0.10,
    "leaks_exposure": 0.15,
    "regulatory_presence": 0.10,
}

SIZE_NORMALIZATION = {
    "micro": 1.15,      # < 10 employees
    "sme": 1.10,        # 10-250
    "midmarket": 1.00,  # 250-5000 (standard)
    "enterprise": 0.90, # > 5000
}

def score_to_grade(score: int) -> Grade:
    if score >= 800: return Grade.A
    if score >= 600: return Grade.B
    if score >= 400: return Grade.C
    if score >= 200: return Grade.D
    return Grade.F

def domain_score_to_grade(score: float) -> str:
    if score >= 80: return "A"
    if score >= 60: return "B"
    if score >= 40: return "C"
    if score >= 20: return "D"
    return "E"
```

### Domain Analyzer Pattern
Each domain has its own analyzer class:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class Finding:
    domain: str
    title: str
    description: str
    severity: CriticalityLevel
    cvss_score: float | None = None
    source: str = ""
    evidence: str = ""
    recommendation: str = ""
    status: str = "open"  # open, acknowledged, disputed, resolved, false_positive

@dataclass
class DomainResult:
    domain: str
    score: float  # 0-100
    grade: str    # A-E
    findings: list[Finding]
    confidence: float  # 0-1, how confident we are in this score
    raw_data: dict

class BaseDomainAnalyzer(ABC):
    @abstractmethod
    async def analyze(self, domain: str) -> DomainResult:
        """Analyze a single domain aspect and return scored result."""
        ...

    def calculate_domain_score(self, findings: list[Finding]) -> float:
        """Calculate domain score from findings. 100 = no issues, 0 = critical."""
        if not findings:
            return 50.0  # No data = neutral score

        deductions = 0.0
        for f in findings:
            factor = CRITICALITY_FACTORS.get(f.severity, 0)
            deductions += factor * 10  # Each finding deducts based on severity

        return max(0.0, min(100.0, 100.0 - deductions))
```

### Scoring Engine (Aggregator)
```python
class ScoringEngine:
    def __init__(self, weights: dict[str, float] | None = None):
        self.weights = weights or DEFAULT_DOMAIN_WEIGHTS

    async def score_vendor(
        self,
        domain_results: dict[str, DomainResult],
        org_size: str = "midmarket",
    ) -> VendorScore:
        weighted_sum = 0.0
        total_weight = 0.0

        for domain_key, result in domain_results.items():
            weight = self.weights.get(domain_key, 0.10)
            max_criticality = self._max_criticality(result.findings)
            factor = CRITICALITY_FACTORS.get(max_criticality, 1.0)

            weighted_sum += result.score * weight * factor
            total_weight += weight

        raw_score = (weighted_sum / total_weight) * 10 if total_weight > 0 else 500

        # Apply size normalization
        size_factor = SIZE_NORMALIZATION.get(org_size, 1.0)
        final_score = int(min(1000, raw_score * size_factor))

        return VendorScore(
            score=final_score,
            grade=score_to_grade(final_score),
            domain_scores=domain_results,
            org_size=org_size,
        )
```

### Finding Status Workflow
```
open → acknowledged → resolved
open → disputed → (arbitration) → resolved | false_positive
```
- Each finding has a status tracked with full audit trail
- Vendors can dispute via portal with evidence upload
- SLA: 48h business hours (configurable)
- History retained 3 years for audit

### Scoring Cycle
```
Collection (OSINT Agents)
  → Normalization
  → Domain Scoring
  → Weighted Aggregation
  → Global Score + Grade
  → Store in TimescaleDB
  → Emit Event (Celery)
  → Alert if threshold breached
  → Compare M-1
  → Trend
  → Real-time Dashboard
```

### TimescaleDB Storage
Scores are time-series data stored in TimescaleDB hypertables for efficient temporal queries:

```sql
CREATE TABLE vendor_scores (
    time TIMESTAMPTZ NOT NULL,
    vendor_id TEXT NOT NULL,
    global_score INTEGER NOT NULL,
    grade VARCHAR(1) NOT NULL,
    domain_scores JSONB NOT NULL,
    scan_id TEXT NOT NULL,
    PRIMARY KEY (time, vendor_id)
);

SELECT create_hypertable('vendor_scores', 'time');
```

### Key Principles
1. **Total Transparency**: every scoring point traceable to source data (AI Act art. 13)
2. **Explainability**: user can understand why a score is what it is
3. **Contestability**: documented dispute process with SLA (AI Act art. 14)
4. **Non-discrimination**: no bias based on size, sector, or nationality
5. **Configurability**: weights and factors configurable by admin
