"use client";

import { useEffect, useState } from "react";
import { PieChart, Pie, Cell } from "recharts";
import { scoreToGrade, gradeToColor, formatScore } from "@/lib/scoring-utils";

interface ScoreGaugeProps {
  score: number;
  maxScore?: number;
  size?: number;
  className?: string;
}

const GAUGE_ZONES = [
  { min: 0, max: 200, color: "#C0392B" },
  { min: 200, max: 400, color: "#E67E22" },
  { min: 400, max: 600, color: "#F39C12" },
  { min: 600, max: 800, color: "#2ECC71" },
  { min: 800, max: 1000, color: "#27AE60" },
];

export function ScoreGauge({ score, maxScore = 1000, size = 240, className }: ScoreGaugeProps) {
  const [animatedScore, setAnimatedScore] = useState(0);

  useEffect(() => {
    const duration = 1000;
    const steps = 60;
    const increment = score / steps;
    let current = 0;
    let step = 0;

    const timer = setInterval(() => {
      step++;
      current = Math.min(score, increment * step);
      setAnimatedScore(Math.round(current));
      if (step >= steps) clearInterval(timer);
    }, duration / steps);

    return () => clearInterval(timer);
  }, [score]);

  const grade = scoreToGrade(score);
  const gradeColor = gradeToColor(grade);

  const filledValue = (animatedScore / maxScore) * 180;
  const emptyValue = 180 - filledValue;

  const data = [
    { value: filledValue, color: gradeColor },
    { value: emptyValue, color: "#E2E8F0" },
    { value: 180, color: "transparent" },
  ];

  return (
    <div className={className} style={{ position: "relative", width: size, height: size * 0.65 }}>
      <PieChart width={size} height={size * 0.65}>
        <Pie
          data={data}
          cx={size / 2}
          cy={size * 0.6}
          startAngle={180}
          endAngle={0}
          innerRadius={size * 0.3}
          outerRadius={size * 0.45}
          dataKey="value"
          stroke="none"
          isAnimationActive={false}
        >
          {data.map((entry, index) => (
            <Cell key={index} fill={entry.color} />
          ))}
        </Pie>
      </PieChart>
      <div
        style={{
          position: "absolute",
          left: "50%",
          top: "60%",
          transform: "translate(-50%, -50%)",
          textAlign: "center",
        }}
      >
        <div className="font-mono font-bold text-3xl" style={{ color: gradeColor }}>
          {formatScore(animatedScore)}
        </div>
        <div className="text-lg font-bold" style={{ color: gradeColor }}>
          {grade}
        </div>
      </div>
    </div>
  );
}
