"use client";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { LiveDot } from "@/components/shared/live-dot";
import { cn } from "@/lib/utils";

type SidebarFooterProps = {
  collapsed?: boolean;
};

export function SidebarFooter({ collapsed = false }: SidebarFooterProps) {
  return (
    <div className={cn("mt-auto space-y-3 border-t border-sidebar-border p-3", collapsed && "px-2")}>
      <div
        className={cn(
          "rounded-lg bg-white/3 px-2.5 py-2 ring-1 ring-white/5",
          collapsed && "flex justify-center px-0",
        )}
      >
        {collapsed ? (
          <LiveDot label="Foundation online" className="sr-only" />
        ) : (
          <div>
            <p className="text-label">System status</p>
            <LiveDot label="Foundation online" className="mt-1" />
          </div>
        )}
        {collapsed ? (
          <span className="relative flex size-2" aria-label="Foundation online">
            <span className="status-ping absolute inset-0 rounded-full bg-success" />
            <span className="relative size-2 rounded-full bg-success" />
          </span>
        ) : null}
      </div>

      <div
        className={cn(
          "flex items-center gap-2.5 rounded-lg px-1.5 py-1",
          collapsed && "justify-center px-0",
        )}
      >
        <Avatar size="sm" className="bg-weather/15">
          <AvatarFallback className="bg-weather/15 text-[10px] font-semibold text-weather-secondary">
            DA
          </AvatarFallback>
        </Avatar>
        {!collapsed ? (
          <div className="min-w-0">
            <p className="truncate text-xs font-medium text-foreground">Duty Analyst</p>
            <p className="truncate text-[11px] text-muted-foreground">NDMA Command Desk</p>
          </div>
        ) : (
          <span className="sr-only">Duty Analyst, NDMA Command Desk</span>
        )}
      </div>
    </div>
  );
}
