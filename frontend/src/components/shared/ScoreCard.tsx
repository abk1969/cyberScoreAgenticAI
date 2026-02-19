import { cn } from "@/lib/utils";
import { GradeBadge } from "@/components/ui/badge";
import { gradeToColor, scoreToGrade, formatScore } from "@/lib/scoring-utils";
import type { TrendDirection } from "@/types/scoring";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

interface ScoreCardProps {
  score: number;
  maxScore?: number;
  label?: string;
  trend?: TrendDirection;
  showGrade?: boolean;
  size?: "sm" | "md" | "lg";
  className?: string;
}

const trendIcons: Record<TrendDirection, typeof TrendingUp> = {
  up: TrendingUp,
  down: TrendingDown,
  stable: Minus,
};

const trendColors: Record<TrendDirection, string> = {
  up: "text-score-a",
  down: "text-score-f",
  stable: "text-muted",
};

export function ScoreCard({ score, maxScore = 1000, label, trend, showGrade = true, size = "md", className }: ScoreCardProps) {
  const grade = maxScore === 1000 ? scoreToGrade(score) : scoreToGrade((score / maxScore) * 1000);
  const color = gradeToColor(grade);

  const sizeClasses = {
    sm: "p-3",
    md: "p-4",
    lg: "p-6",
  };

  const scoreSizes = {
    sm: "text-2xl",
    md: "text-3xl",
    lg: "text-5xl",
  };

  return (
    <div className={cn("flex flex-col items-center gap-2 rounded-lg border border-border bg-white", sizeClasses[size], className)}>
      {label && <span className="text-sm font-medium text-muted">{label}</span>}
      <div className="flex items-center gap-3">
        <span className={cn("font-bold font-mono", scoreSizes[size])} style={{ color }}>
          {formatScore(score)}
        </span>
        {showGrade && <GradeBadge grade={grade} />}
      </div>
      {trend && (
        <div className={cn("flex items-center gap-1 text-sm", trendColors[trend])}>
          {(() => {
            const Icon = trendIcons[trend];
            return <Icon className="h-4 w-4" />;
          })()}
          <span>
            {trend === "up" ? "En hausse" : trend === "down" ? "En baisse" : "Stable"}
          </span>
        </div>
      )}
    </div>
  );
}
