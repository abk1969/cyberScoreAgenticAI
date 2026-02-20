"use client";

import { useState, useEffect } from "react";
import { LineChart, Line, ResponsiveContainer, Tooltip } from "recharts";

interface TrendSparklineProps {
  data: { date: string; score: number }[];
  color?: string;
  height?: number;
  width?: number;
  className?: string;
}

export function TrendSparkline({
  data,
  color = "#2E75B6",
  height = 40,
  width = 120,
  className,
}: TrendSparklineProps) {
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  if (!mounted || data.length < 2) return null;

  const scores = data.map((d) => d.score);
  const min = Math.min(...scores);
  const max = Math.max(...scores);
  const latest = scores[scores.length - 1];
  const previous = scores[scores.length - 2];
  const trendColor = latest >= previous ? "#27AE60" : "#C0392B";

  return (
    <div className={className} style={{ width, height }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <Tooltip
            contentStyle={{
              backgroundColor: "#fff",
              border: "1px solid #E2E8F0",
              borderRadius: "6px",
              fontSize: "11px",
              padding: "4px 8px",
            }}
            formatter={(value: number) => [`${value}`, "Score"]}
            labelFormatter={(label: string) => label}
          />
          <Line
            type="monotone"
            dataKey="score"
            stroke={trendColor}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 3, fill: trendColor }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
