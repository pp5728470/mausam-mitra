"use client";

import type { ReactNode } from "react";

import { Header } from "@/components/layout/header";
import { MobileSidebar } from "@/components/layout/mobile-sidebar";
import { Sidebar } from "@/components/layout/sidebar";
import { SidebarProvider } from "@/components/layout/sidebar-provider";
import { PageTransition } from "@/components/shared/page-transition";
import { SkipToContent } from "@/components/shared/skip-to-content";
import { WeatherAtmosphere } from "@/components/shared/weather-atmosphere";

type AppShellProps = {
  children: ReactNode;
};

export function AppShell({ children }: AppShellProps) {
  return (
    <SidebarProvider>
      <div className="relative flex min-h-svh overflow-x-hidden bg-background">
        <WeatherAtmosphere className="opacity-70" />
        <SkipToContent />
        <Sidebar />
        <MobileSidebar />
        <div className="relative flex min-w-0 flex-1 flex-col">
          <Header />
          <main id="main-content" className="min-w-0 flex-1 overflow-x-hidden p-4 sm:p-6">
            <PageTransition>{children}</PageTransition>
          </main>
        </div>
      </div>
    </SidebarProvider>
  );
}
