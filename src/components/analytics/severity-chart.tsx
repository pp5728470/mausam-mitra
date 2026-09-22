"use client";

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip, Legend } from "recharts";
import type { AnalyticsSeverity } from "@/lib/api/analytics";

interface SeverityChartProps {
  severity: AnalyticsSeverity;
}

const COLORS = {
  CRITICAL: "#ef4444", // red-500
  HIGH: "#f97316", // orange-500
  MEDIUM: "#eab308", // yellow-500
  LOW: "#3b82f6", // blue-500
  UNKNOWN: "#71717a", // zinc-500
};

export function SeverityChart({ severity }: SeverityChartProps) {
  const data = severity.distribution;

  return (
    <div className="h-[250px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={80}
            paddingAngle={5}
            dataKey="count"
            nameKey="severity"
          >
            {data.map((entry, index) => (
              <Cell 
                key={`cell-${index}`} 
                fill={COLORS[entry.severity as keyof typeof COLORS] || COLORS.UNKNOWN} 
              />
            ))}
          </Pie>
          <Tooltip 
            contentStyle={{ backgroundColor: "#18181b", border: "1px solid #27272a", borderRadius: "8px" }}
            itemStyle={{ color: "#e4e4e7" }}
          />
          <Legend verticalAlign="bottom" height={36} iconType="circle" />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
