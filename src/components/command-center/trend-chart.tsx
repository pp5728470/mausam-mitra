"use client";

import { motion } from "motion/react";
import { useSafeReducedMotion } from "@/hooks/use-safe-reduced-motion";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { mockAnalytics } from "@/lib/mock/analytics";
import { fadeUp, subtleTransition } from "@/lib/motion";

export function TrendChart() {
  const reduceMotion = useSafeReducedMotion();

  return (
    <motion.section
      initial={reduceMotion ? false : "hidden"}
      animate="visible"
      variants={fadeUp}
      transition={{ ...subtleTransition, delay: 0.12 }}
      aria-labelledby="trend-chart-heading"
      className="rounded-xl bg-card/60 px-4 py-3.5 ring-1 ring-white/6"
    >
      <div className="mb-3 flex flex-wrap items-end justify-between gap-2">
        <div>
          <p className="text-label">Analytics Snapshot</p>
          <h2 id="trend-chart-heading" className="text-section-title mt-0.5">
            Incident Activity — Last 24 Hours
          </h2>
        </div>
        <span className="rounded-full border border-white/10 bg-white/4 px-2 py-0.5 text-[10px] font-semibold tracking-[0.1em] text-muted-foreground">
          DEMO ANALYTICS
        </span>
      </div>

      <div className="h-52 w-full min-w-0 sm:h-56">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={mockAnalytics}
            margin={{ top: 8, right: 8, left: -12, bottom: 0 }}
          >
            <defs>
              <linearGradient id="signalsFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#0EA5E9" stopOpacity={0.28} />
                <stop offset="100%" stopColor="#0EA5E9" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="verifiedFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#22C55E" stopOpacity={0.22} />
                <stop offset="100%" stopColor="#22C55E" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="emergingFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#F59E0B" stopOpacity={0.22} />
                <stop offset="100%" stopColor="#F59E0B" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="rgba(148,163,184,0.12)" vertical={false} />
            <XAxis
              dataKey="hour"
              tick={{ fill: "#93A4B8", fontSize: 11 }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              tick={{ fill: "#93A4B8", fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              width={36}
            />
            <Tooltip
              contentStyle={{
                background: "#122C44",
                border: "1px solid rgba(56,189,248,0.16)",
                borderRadius: 10,
                color: "#F4F7FB",
                fontSize: 12,
              }}
              labelStyle={{ color: "#93A4B8" }}
            />
            <Legend
              wrapperStyle={{ fontSize: 11, color: "#93A4B8", paddingTop: 8 }}
            />
            <Area
              type="monotone"
              dataKey="signals"
              name="Incident signals"
              stroke="#0EA5E9"
              fill="url(#signalsFill)"
              strokeWidth={2}
              isAnimationActive={!reduceMotion}
            />
            <Area
              type="monotone"
              dataKey="verified"
              name="Verified incidents"
              stroke="#22C55E"
              fill="url(#verifiedFill)"
              strokeWidth={1.5}
              isAnimationActive={!reduceMotion}
            />
            <Area
              type="monotone"
              dataKey="emerging"
              name="Emerging signals"
              stroke="#F59E0B"
              fill="url(#emergingFill)"
              strokeWidth={1.5}
              isAnimationActive={!reduceMotion}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </motion.section>
  );
}
