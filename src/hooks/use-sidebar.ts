"use client";

import { createContext, useContext } from "react";

export type SidebarContextValue = {
  collapsed: boolean;
  mobileOpen: boolean;
  setCollapsed: (collapsed: boolean) => void;
  setMobileOpen: (open: boolean) => void;
  toggleCollapsed: () => void;
};

export const SidebarContext = createContext<SidebarContextValue | null>(null);

export function useSidebar(): SidebarContextValue {
  const context = useContext(SidebarContext);

  if (!context) {
    throw new Error("useSidebar must be used within AppShell");
  }

  return context;
}
