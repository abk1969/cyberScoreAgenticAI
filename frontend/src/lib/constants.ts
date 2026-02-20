import type { ScoringDomain, Grade, Severity } from "@/types/scoring";

export const API_ROUTES = {
  vendors: "/api/v1/vendors",
  vendor: (id: string) => `/api/v1/vendors/${id}`,
  vendorScore: (id: string) => `/api/v1/scoring/vendors/${id}/latest`,
  vendorDomainScores: (id: string) => `/api/v1/scoring/vendors/${id}/domains`,
  vendorScoreHistory: (id: string) => `/api/v1/scoring/vendors/${id}/history`,
  vendorRescan: (id: string) => `/api/v1/vendors/${id}/rescan`,
  portfolioScores: "/api/v1/scoring/portfolio",
  alerts: "/api/v1/alerts",
  alertMarkRead: (id: string) => `/api/v1/alerts/${id}/read`,
  chat: "/api/v1/chat",
  // VRM
  vrmOnboard: "/api/v1/vrm/onboard",
  vrmDisputes: "/api/v1/vrm/disputes",
  vrmDisputesByVendor: (id: string) => `/api/v1/vrm/vendors/${id}/dispute`,
  vrmDispute: (id: string) => `/api/v1/vrm/disputes/${id}`,
  vrmRemediations: (id: string) => `/api/v1/vrm/vendors/${id}/remediation`,
  // Questionnaires
  questionnaireTemplates: "/api/v1/questionnaires/templates",
  questionnaires: "/api/v1/questionnaires",
  questionnaire: (id: string) => `/api/v1/questionnaires/${id}`,
  questionnaireSend: (id: string) => `/api/v1/questionnaires/${id}/send`,
  questionnaireRespond: (id: string) => `/api/v1/questionnaires/${id}/respond`,
  questionnaireSmartAnswer: (id: string) => `/api/v1/questionnaires/${id}/smart-answer`,
} as const;

export const GRADE_COLORS: Record<Grade, string> = {
  A: "#27AE60",
  B: "#2ECC71",
  C: "#F39C12",
  D: "#E67E22",
  F: "#C0392B",
};

export const DOMAIN_LABELS: Record<ScoringDomain, string> = {
  network_security: "Sécurité Réseau",
  dns_security: "Sécurité DNS",
  web_security: "Sécurité Web",
  email_security: "Sécurité Email",
  patching_cadence: "Cadence Correctifs",
  ip_reputation: "Réputation IP",
  leaks_exposure: "Fuites & Exposition",
  regulatory_presence: "Présence Réglementaire",
};

export const DOMAIN_WEIGHTS: Record<ScoringDomain, number> = {
  network_security: 0.15,
  dns_security: 0.10,
  web_security: 0.15,
  email_security: 0.10,
  patching_cadence: 0.15,
  ip_reputation: 0.10,
  leaks_exposure: 0.15,
  regulatory_presence: 0.10,
};

export const SEVERITY_LABELS: Record<Severity, string> = {
  critical: "Critique",
  high: "Élevé",
  medium: "Moyen",
  low: "Faible",
  info: "Information",
};

export const SEVERITY_ORDER: Record<Severity, number> = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3,
  info: 4,
};

export const TIER_LABELS: Record<number, string> = {
  1: "Tier 1 — Critique",
  2: "Tier 2 — Important",
  3: "Tier 3 — Standard",
};
