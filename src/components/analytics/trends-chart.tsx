"use client";

import { useMemo } from "react";
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { AnalyticsTrends } from "@/lib/api/analytics";

interface TrendsChartProps {
  trends: AnalyticsTrends;
  timeRange: 1 | 7 | 30;
}

export function TrendsChart({ trends, timeRange }: TrendsChartProps) {
  const data = useMemo(() => {
    if (timeRange === 1) return trends.reports_24h;
    if (timeRange === 7) return trends.reports_7d;
    return trends.reports_30d;
  }, [trends, timeRange]);

  const formattedData = useMemo(() => {
    return data.map((pt) => {
      const date = new Date(pt.timestamp);
      return {
        ...pt,
        label: timeRange === 1 
          ? date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) 
          : date.toLocaleDateString([], { month: 'short', day: 'numeric' })
      };
    });
  }, [data, timeRange]);

  return (
    <div className="h-[300px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={formattedData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="colorReports" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#38bdf8" stopOpacity={0} />
            </linearGradient>
          </defs>
          <XAxis 
            dataKey="label" 
            stroke="#52525b" 
            fontSize={12} 
            tickLine={false} 
            axisLine={false} 
            minTickGap={20}
          />
          <YAxis 
            stroke="#52525b" 
            fontSize={12} 
            tickLine={false} 
            axisLine={false} 
            tickFormatter={(value) => `${value}`} 
          />
          <Tooltip
            contentStyle={{ backgroundColor: "#18181b", border: "1px solid #27272a", borderRadius: "8px" }}
            itemStyle={{ color: "#e4e4e7" }}
            labelStyle={{ color: "#a1a1aa", marginBottom: "4px" }}
          />
          <Area
            type="monotone"
            dataKey="value"
            name="Reports"
            stroke="#38bdf8"
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#colorReports)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
