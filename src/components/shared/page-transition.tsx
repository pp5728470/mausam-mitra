"use client";

import type { ReactNode } from "react";
import { usePathname } from "next/navigation";
import { motion } from "motion/react";

import { useSafeReducedMotion } from "@/hooks/use-safe-reduced-motion";
import { subtleTransition } from "@/lib/motion";

type PageTransitionProps = {
  children: ReactNode;
};

export function PageTransition({ children }: PageTransitionProps) {
  const pathname = usePathname();
  const reduceMotion = useSafeReducedMotion();

  return (
    <motion.div
      key={pathname}
      initial={reduceMotion ? false : { opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={subtleTransition}
      className="min-h-full"
    >
      {children}
    </motion.div>
  );
}
