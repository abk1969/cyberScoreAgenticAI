"use client";

import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

interface DomainRadarData {
  domain: string;
  label: string;
  score: number;
}

interface RiskRadarProps {
  data: DomainRadarData[];
  color?: string;
  height?: number;
  className?: string;
}

const DOMAIN_SHORT_LABELS: Record<string, string> = {
  D1: "Réseau",
  D2: "DNS",
  D3: "Web",
  D4: "Email",
  D5: "Patching",
  D6: "IP Rep.",
  D7: "Fuites",
  D8: "Réglementaire",
};

export function RiskRadar({
  data,
  color = "#2E75B6",
  height = 350,
  className,
}: RiskRadarProps) {
  const chartData = data.map((d) => ({
    ...d,
    shortLabel: DOMAIN_SHORT_LABELS[d.domain] ?? d.label,
  }));

  return (
    <div className={className}>
      <ResponsiveContainer width="100%" height={height}>
        <RadarChart data={chartData} cx="50%" cy="50%" outerRadius="70%">
          <PolarGrid stroke="#E2E8F0" />
          <PolarAngleAxis
            dataKey="shortLabel"
            tick={{ fill: "#2C3E50", fontSize: 11 }}
          />
          <PolarRadiusAxis
            angle={90}
            domain={[0, 100]}
            tick={{ fill: "#94A3B8", fontSize: 10 }}
            tickCount={5}
          />
          <Radar
            name="Score"
            dataKey="score"
            stroke={color}
            fill={color}
            fillOpacity={0.2}
            strokeWidth={2}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#fff",
              border: "1px solid #E2E8F0",
              borderRadius: "8px",
              fontSize: "12px",
            }}
            formatter={(value: number) => [`${value}/100`, "Score"]}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
