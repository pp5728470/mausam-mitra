"use client";

import { PanelLeftClose, PanelLeftOpen } from "lucide-react";

import { BrandMark } from "@/components/shared/brand-mark";
import { Button } from "@/components/ui/button";
import { SidebarFooter } from "@/components/layout/sidebar-footer";
import { SidebarNav } from "@/components/layout/sidebar-nav";
import { layoutConfig } from "@/config/site";
import { useSidebar } from "@/hooks/use-sidebar";
import { cn } from "@/lib/utils";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

export function Sidebar() {
  const { collapsed, toggleCollapsed } = useSidebar();
  const width = collapsed
    ? layoutConfig.sidebarCollapsed
    : layoutConfig.sidebarExpanded;

  return (
    <aside
      className={cn(
        "hidden h-svh shrink-0 flex-col border-r border-sidebar-border bg-sidebar lg:flex",
        "transition-[width] duration-200 ease-out",
      )}
      style={{ width }}
      aria-label="Primary navigation"
    >
      <div
        className={cn(
          "flex h-16 items-center gap-2 border-b border-sidebar-border px-3",
          collapsed && "justify-center px-2",
        )}
      >
        <BrandMark collapsed={collapsed} href="/overview" className="min-w-0 flex-1" />
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              type="button"
              variant="ghost"
              size="icon-sm"
              onClick={toggleCollapsed}
              aria-pressed={collapsed}
              aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
              className={cn(collapsed && "hidden")}
            >
              <PanelLeftClose />
            </Button>
          </TooltipTrigger>
          <TooltipContent>Collapse sidebar</TooltipContent>
        </Tooltip>
      </div>

      {collapsed ? (
        <div className="flex justify-center py-2">
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                type="button"
                variant="ghost"
                size="icon-sm"
                onClick={toggleCollapsed}
                aria-label="Expand sidebar"
              >
                <PanelLeftOpen />
              </Button>
            </TooltipTrigger>
            <TooltipContent side="right">Expand sidebar</TooltipContent>
          </Tooltip>
        </div>
      ) : null}

      <div className="flex min-h-0 flex-1 flex-col py-3">
        <SidebarNav />
        <SidebarFooter collapsed={collapsed} />
      </div>
    </aside>
  );
}
