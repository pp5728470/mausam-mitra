"use client";

import type { ReactNode } from "react";

import { TooltipProvider } from "@/components/ui/tooltip";

type ProvidersProps = {
  children: ReactNode;
};

import { AuthProvider } from "@/contexts/AuthContext";

export function Providers({ children }: ProvidersProps) {
  return (
    <AuthProvider>
      <TooltipProvider delayDuration={200}>{children}</TooltipProvider>
    </AuthProvider>
  );
}
