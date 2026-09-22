"use client";

import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { AnalyticsCategories } from "@/lib/api/analytics";

interface CategoryChartProps {
  categories: AnalyticsCategories;
}

export function CategoryChart({ categories }: CategoryChartProps) {
  // Take top 6 categories for cleaner UI
  const data = categories.distribution.slice(0, 6);

  return (
    <div className="h-[250px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ top: 0, right: 20, left: 40, bottom: 0 }}>
          <XAxis type="number" hide />
          <YAxis 
            type="category" 
            dataKey="category" 
            stroke="#a1a1aa" 
            fontSize={12} 
            tickLine={false} 
            axisLine={false}
            width={120}
          />
          <Tooltip
            contentStyle={{ backgroundColor: "#18181b", border: "1px solid #27272a", borderRadius: "8px" }}
            itemStyle={{ color: "#e4e4e7" }}
            cursor={{ fill: "#27272a", opacity: 0.4 }}
          />
          <Bar dataKey="count" fill="#8b5cf6" radius={[0, 4, 4, 0]} barSize={20} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
