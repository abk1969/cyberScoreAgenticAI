"""Scoring constants, domain weights, and grade mappings."""

# --- Global Score Grade Mapping (0-1000) ---
GRADE_THRESHOLDS: dict[str, int] = {
    "A": 800,
    "B": 600,
    "C": 400,
    "D": 200,
    "F": 0,
}

GRADE_LABELS: dict[str, str] = {
    "A": "Excellent",
    "B": "Good",
    "C": "Acceptable",
    "D": "Weak",
    "F": "Critical",
}

# --- Domain Score Grade Mapping (0-100) ---
DOMAIN_GRADE_THRESHOLDS: dict[str, int] = {
    "A": 80,
    "B": 60,
    "C": 40,
    "D": 20,
    "E": 0,
}

# --- 8 Scoring Domains ---
SCORING_DOMAINS: dict[str, str] = {
    "D1": "Network Security",
    "D2": "DNS Security",
    "D3": "Web Security",
    "D4": "Email Security",
    "D5": "Patching Cadence",
    "D6": "IP Reputation",
    "D7": "Leaks & Exposure",
    "D8": "Regulatory Presence",
}

# --- Default Domain Weights (must sum to 1.0) ---
DEFAULT_DOMAIN_WEIGHTS: dict[str, float] = {
    "D1": 0.15,  # Network Security
    "D2": 0.10,  # DNS Security
    "D3": 0.15,  # Web Security
    "D4": 0.10,  # Email Security
    "D5": 0.15,  # Patching Cadence
    "D6": 0.10,  # IP Reputation
    "D7": 0.15,  # Leaks & Exposure
    "D8": 0.10,  # Regulatory Presence
}

# --- Criticality Factors ---
CRITICALITY_FACTORS: dict[str, float] = {
    "critical": 2.0,
    "high": 1.5,
    "medium": 1.0,
    "low": 0.5,
    "info": 0.0,
}

# --- Organization Size Normalization ---
SIZE_NORMALIZATION: dict[str, float] = {
    "micro": 1.15,       # < 10 employees
    "sme": 1.10,         # 10-250
    "midmarket": 1.00,   # 250-5000 (standard)
    "enterprise": 0.90,  # > 5000
}

# --- Vendor Tiers ---
VENDOR_TIERS: dict[int, str] = {
    1: "Critical",
    2: "Important",
    3: "Standard",
}

# --- Finding Statuses ---
FINDING_STATUSES: list[str] = [
    "open",
    "acknowledged",
    "disputed",
    "resolved",
    "false_positive",
]

# --- Vendor Statuses ---
VENDOR_STATUSES: list[str] = [
    "active",
    "inactive",
    "under_review",
]

# --- User Roles ---
USER_ROLES: list[str] = [
    "admin",
    "rssi",
    "analyste_ssi",
    "direction_achats",
    "comex",
    "fournisseur",
]

# --- Report Types ---
REPORT_TYPES: list[str] = [
    "executive",
    "rssi",
    "vendor",
    "dora",
    "benchmark",
]

REPORT_FORMATS: list[str] = [
    "pdf",
    "pptx",
    "xlsx",
]

# --- Alert Types ---
ALERT_TYPES: list[str] = [
    "score_drop",
    "new_vulnerability",
    "breach",
    "certificate_expiry",
    "dns_change",
    "new_finding",
    "compliance_change",
]

# --- Alert Severities ---
ALERT_SEVERITIES: list[str] = [
    "critical",
    "high",
    "medium",
    "low",
    "info",
]
