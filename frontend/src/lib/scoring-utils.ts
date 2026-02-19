import type { Grade, DomainGrade, Severity, TrendDirection } from "@/types/scoring";

const GRADE_COLORS: Record<Grade, string> = {
  A: "#27AE60",
  B: "#2ECC71",
  C: "#F39C12",
  D: "#E67E22",
  F: "#C0392B",
};

const DOMAIN_GRADE_COLORS: Record<DomainGrade, string> = {
  A: "#27AE60",
  B: "#2ECC71",
  C: "#F39C12",
  D: "#E67E22",
  E: "#C0392B",
};

const SEVERITY_COLORS: Record<Severity, string> = {
  critical: "#C0392B",
  high: "#E67E22",
  medium: "#F39C12",
  low: "#2ECC71",
  info: "#94A3B8",
};

export function gradeToColor(grade: Grade): string {
  return GRADE_COLORS[grade] ?? "#94A3B8";
}

export function domainGradeToColor(grade: DomainGrade): string {
  return DOMAIN_GRADE_COLORS[grade] ?? "#94A3B8";
}

export function scoreToGrade(score: number): Grade {
  if (score >= 800) return "A";
  if (score >= 600) return "B";
  if (score >= 400) return "C";
  if (score >= 200) return "D";
  return "F";
}

export function domainScoreToGrade(score: number): DomainGrade {
  if (score >= 80) return "A";
  if (score >= 60) return "B";
  if (score >= 40) return "C";
  if (score >= 20) return "D";
  return "E";
}

export function severityToColor(severity: Severity): string {
  return SEVERITY_COLORS[severity] ?? "#94A3B8";
}

export function formatScore(score: number): string {
  return Math.round(score).toLocaleString("fr-FR");
}

export function getTrendDirection(current: number, previous: number | null): TrendDirection {
  if (previous === null) return "stable";
  const delta = current - previous;
  if (delta > 10) return "up";
  if (delta < -10) return "down";
  return "stable";
}

export function scoreToHeatmapColor(score: number): string {
  if (score >= 80) return "#27AE60";
  if (score >= 60) return "#2ECC71";
  if (score >= 40) return "#F39C12";
  if (score >= 20) return "#E67E22";
  return "#C0392B";
}
