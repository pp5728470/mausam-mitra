"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { NAV_ITEMS } from "@/config/navigation";
import { useSidebar } from "@/hooks/use-sidebar";
import { useAuth } from "@/contexts/AuthContext";
import { cn } from "@/lib/utils";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

type SidebarNavProps = {
  onNavigate?: () => void;
  forceExpanded?: boolean;
};

export function SidebarNav({ onNavigate, forceExpanded = false }: SidebarNavProps) {
  const pathname = usePathname();
  const { collapsed } = useSidebar();
  const { hasAnyRole } = useAuth();
  const isCollapsed = forceExpanded ? false : collapsed;

  const allowedItems = NAV_ITEMS.filter((item) => hasAnyRole(item.allowedRoles));

  return (
    <nav aria-label="Command center" className="flex flex-1 flex-col gap-1 px-2">
      {allowedItems.map((item) => {
        const isActive = pathname === item.href;
        const Icon = item.icon;
        const link = (
          <Link
            href={item.href}
            onClick={onNavigate}
            aria-current={isActive ? "page" : undefined}
            className={cn(
              "flex items-center gap-3 rounded-lg px-2.5 py-2 text-sm transition-colors",
              isCollapsed && "justify-center px-0",
              isActive
                ? "bg-weather/12 text-foreground ring-1 ring-weather/20"
                : "text-muted-foreground hover:bg-white/5 hover:text-foreground",
            )}
          >
            <Icon className="size-4 shrink-0" aria-hidden />
            {!isCollapsed ? <span className="truncate">{item.label}</span> : null}
            {isCollapsed ? <span className="sr-only">{item.label}</span> : null}
          </Link>
        );

        if (!isCollapsed) {
          return <div key={item.href}>{link}</div>;
        }

        return (
          <Tooltip key={item.href}>
            <TooltipTrigger asChild>{link}</TooltipTrigger>
            <TooltipContent side="right">{item.label}</TooltipContent>
          </Tooltip>
        );
      })}
    </nav>
  );
}
