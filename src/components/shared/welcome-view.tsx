"use client";

import Link from "next/link";
import { ArrowRight, ArrowUpRight } from "lucide-react";
import { motion } from "motion/react";

import { BrandMark } from "@/components/shared/brand-mark";
import { LiveDot } from "@/components/shared/live-dot";
import { SkipToContent } from "@/components/shared/skip-to-content";
import { WeatherAtmosphere } from "@/components/shared/weather-atmosphere";
import { Button } from "@/components/ui/button";
import { intelligencePipeline } from "@/config/pipeline";
import { siteConfig } from "@/config/site";
import { useSafeReducedMotion } from "@/hooks/use-safe-reduced-motion";
import { fadeUp, staggerContainer, subtleTransition } from "@/lib/motion";

export function WelcomeView() {
  const reduceMotion = useSafeReducedMotion();

  return (
    <div className="relative flex min-h-svh overflow-x-hidden bg-background">
      <WeatherAtmosphere withRadar className="opacity-90" />
      <SkipToContent />

      <div className="relative z-10 flex min-h-svh w-full flex-col">
        <header className="flex items-center justify-between gap-4 px-5 py-5 sm:px-8">
          <BrandMark showMeaning />
          <LiveDot label="Systems online" />
        </header>

        <main
          id="main-content"
          className="mx-auto flex w-full max-w-5xl flex-1 flex-col justify-center px-5 py-10 sm:px-8"
        >
          <motion.div
            initial={reduceMotion ? false : "hidden"}
            animate="visible"
            variants={staggerContainer}
            className="max-w-3xl"
          >
            <motion.p variants={fadeUp} className="text-label text-weather-secondary">
              {siteConfig.presentationLabel}
            </motion.p>

            <motion.h1
              variants={fadeUp}
              className="text-display mt-5"
              transition={subtleTransition}
            >
              {siteConfig.name}
            </motion.h1>

            <motion.p
              variants={fadeUp}
              className="mt-5 max-w-xl text-xl leading-snug font-medium tracking-tight text-foreground/90 sm:text-2xl"
            >
              From scattered weather signals to
              <br className="hidden sm:block" /> actionable incidents.
            </motion.p>

            <motion.p
              variants={fadeUp}
              className="text-body mt-6 max-w-lg text-muted-foreground"
            >
              Weather Incident Intelligence & Decision Support Platform.
            </motion.p>

            <motion.div
              variants={fadeUp}
              className="mt-9 flex flex-col gap-3 sm:flex-row sm:items-center"
            >
              <Button asChild size="xl" className="shadow-[0_0_28px_-10px_rgb(14_165_233_/_70%)]">
                <Link href="/reports">
                  Report an Incident
                  <ArrowRight data-icon="inline-end" />
                </Link>
              </Button>
              <Button
                asChild
                size="xl"
                variant="outline"
                className="border-weather/20 bg-white/2 hover:bg-white/5"
              >
                <Link href="/login">
                  Operational Login
                  <ArrowUpRight data-icon="inline-end" />
                </Link>
              </Button>
            </motion.div>
          </motion.div>

          <motion.ol
            initial={reduceMotion ? false : { opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ ...subtleTransition, delay: 0.28 }}
            className="mt-16 grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3"
          >
            {intelligencePipeline.map((step, index) => (
              <li
                key={step}
                className="flex items-center gap-3 rounded-xl bg-card/60 px-3.5 py-3 ring-1 ring-white/6"
              >
                <span className="font-mono text-xs text-weather-secondary tabular-nums">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <span className="text-sm text-foreground/90">{step}</span>
              </li>
            ))}
          </motion.ol>
        </main>

        <footer className="flex flex-col gap-2 px-5 py-5 text-caption sm:flex-row sm:items-center sm:justify-between sm:px-8">
          <p>
            {siteConfig.name} · {siteConfig.meaning}
          </p>
          <p>{siteConfig.presentationLabel} · Weather Incident Decision Support</p>
        </footer>
      </div>
    </div>
  );
}
