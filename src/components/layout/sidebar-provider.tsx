"use client";

import type { ReactNode } from "react";
import { useCallback, useMemo, useState } from "react";

import { useMediaQuery } from "@/hooks/use-media-query";
import { SidebarContext } from "@/hooks/use-sidebar";

type SidebarProviderProps = {
  children: ReactNode;
};

export function SidebarProvider({ children }: SidebarProviderProps) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpenState] = useState(false);
  const isDesktop = useMediaQuery("(min-width: 1024px)");

  const toggleCollapsed = useCallback(() => {
    setCollapsed((current) => !current);
  }, []);

  const setMobileOpen = useCallback(
    (open: boolean) => {
      setMobileOpenState(isDesktop ? false : open);
    },
    [isDesktop],
  );

  const value = useMemo(
    () => ({
      collapsed,
      mobileOpen: isDesktop ? false : mobileOpen,
      setCollapsed,
      setMobileOpen,
      toggleCollapsed,
    }),
    [collapsed, isDesktop, mobileOpen, setMobileOpen, toggleCollapsed],
  );

  return (
    <SidebarContext.Provider value={value}>{children}</SidebarContext.Provider>
  );
}
