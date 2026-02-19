"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { GRADE_COLORS } from "@/lib/constants";
import type { Grade } from "@/types/scoring";

interface GradeDistributionData {
  grade: Grade;
  current: number;
  previous: number;
}

interface GradeDistributionProps {
  data: GradeDistributionData[];
  className?: string;
}

export function GradeDistribution({ data, className }: GradeDistributionProps) {
  const chartData = data.map((d) => ({
    ...d,
    fill: GRADE_COLORS[d.grade],
  }));

  return (
    <div className={className}>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData} barGap={4}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
          <XAxis dataKey="grade" tick={{ fill: "#2C3E50", fontSize: 14 }} />
          <YAxis tick={{ fill: "#94A3B8", fontSize: 12 }} />
          <Tooltip
            contentStyle={{
              backgroundColor: "#fff",
              border: "1px solid #E2E8F0",
              borderRadius: "8px",
              fontSize: "13px",
            }}
            formatter={(value: number, name: string) => [
              value,
              name === "current" ? "Mois actuel" : "Mois précédent (M-1)",
            ]}
          />
          <Legend
            formatter={(value: string) =>
              value === "current" ? "Mois actuel" : "M-1"
            }
          />
          <Bar
            dataKey="current"
            radius={[4, 4, 0, 0]}
            fill="#1B3A5C"
          />
          <Bar
            dataKey="previous"
            radius={[4, 4, 0, 0]}
            fill="#94A3B8"
            opacity={0.5}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
