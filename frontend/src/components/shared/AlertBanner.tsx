"use client";

import { cn } from "@/lib/utils";
import { severityToColor } from "@/lib/scoring-utils";
import { SEVERITY_LABELS } from "@/lib/constants";
import { Badge } from "@/components/ui/badge";
import { X } from "lucide-react";
import type { Severity } from "@/types/scoring";
import { format } from "date-fns";
import { fr } from "date-fns/locale";

interface AlertBannerProps {
  id: string;
  title: string;
  description: string;
  severity: Severity;
  vendorName: string;
  vendorId: string;
  timestamp: string;
  onDismiss?: (id: string) => void;
  className?: string;
}

export function AlertBanner({
  id,
  title,
  description,
  severity,
  vendorName,
  vendorId,
  timestamp,
  onDismiss,
  className,
}: AlertBannerProps) {
  const borderColor = severityToColor(severity);
  const severityVariant = severity as "critical" | "high" | "medium" | "low" | "info";

  return (
    <div
      className={cn("relative flex gap-4 rounded-lg border border-border bg-white p-4", className)}
      style={{ borderLeftWidth: "4px", borderLeftColor: borderColor }}
      role="alert"
    >
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <Badge variant={severityVariant}>{SEVERITY_LABELS[severity]}</Badge>
          <span className="text-sm font-medium text-navy truncate">{title}</span>
        </div>
        <p className="text-sm text-muted mb-2 line-clamp-2">{description}</p>
        <div className="flex items-center gap-3 text-xs text-muted">
          <a href={`/vendors/${vendorId}`} className="text-blue hover:underline">
            {vendorName}
          </a>
          <span>{format(new Date(timestamp), "dd MMM yyyy HH:mm", { locale: fr })}</span>
        </div>
      </div>
      {onDismiss && (
        <button
          onClick={() => onDismiss(id)}
          className="flex-shrink-0 rounded-sm p-1 text-muted hover:text-text transition-colors"
          aria-label="Fermer l'alerte"
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  );
}
