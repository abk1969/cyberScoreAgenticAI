export type Grade = "A" | "B" | "C" | "D" | "F";

export type DomainGrade = "A" | "B" | "C" | "D" | "E";

export type Severity = "critical" | "high" | "medium" | "low" | "info";

export type ScoringDomain =
  | "network_security"
  | "dns_security"
  | "web_security"
  | "email_security"
  | "patching_cadence"
  | "ip_reputation"
  | "leaks_exposure"
  | "regulatory_presence";

export type FindingStatus =
  | "open"
  | "acknowledged"
  | "disputed"
  | "resolved"
  | "false_positive";

export interface Finding {
  id: string;
  domain: ScoringDomain;
  title: string;
  description: string;
  severity: Severity;
  cvssScore: number | null;
  source: string;
  evidence: string;
  recommendation: string;
  status: FindingStatus;
  detectedAt: string;
}

export interface DomainScore {
  domain: ScoringDomain;
  score: number; // 0-100
  grade: DomainGrade;
  findings: Finding[];
  confidence: number; // 0-1
}

export interface VendorScore {
  vendorId: string;
  globalScore: number; // 0-1000
  grade: Grade;
  domainScores: DomainScore[];
  previousScore: number | null;
  scanDate: string;
  scanId: string;
}

export interface ScoreHistoryEntry {
  date: string;
  score: number;
  grade: Grade;
}

export type TrendDirection = "up" | "down" | "stable";
