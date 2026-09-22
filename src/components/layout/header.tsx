"use client";

import { MapPin, Menu } from "lucide-react";
import { usePathname } from "next/navigation";

import { LiveDot } from "@/components/shared/live-dot";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { getNavItem } from "@/config/navigation";
import { siteConfig } from "@/config/site";
import { useSidebar } from "@/hooks/use-sidebar";
import { NotificationPopover } from "./NotificationPopover";

export function Header() {
  const pathname = usePathname();
  const { setMobileOpen } = useSidebar();
  const current = getNavItem(pathname);
  const title = current?.label ?? "Command Center";

  return (
    <header className="flex h-16 shrink-0 items-center gap-3 border-b border-border/70 bg-background/80 px-3 backdrop-blur-md sm:px-5">
      <Button
        type="button"
        variant="ghost"
        size="icon"
        className="lg:hidden"
        onClick={() => setMobileOpen(true)}
        aria-label="Open navigation"
      >
        <Menu />
      </Button>

      <div className="min-w-0 flex-1">
        <p className="text-label">Command Center</p>
        <h1 className="truncate text-base font-semibold tracking-tight text-foreground">
          {title}
        </h1>
      </div>

      <div className="hidden items-center gap-2 text-xs text-muted-foreground md:flex">
        <MapPin className="size-3.5 text-weather-secondary" aria-hidden />
        <span>
          {siteConfig.contextLabel}
          <span className="mx-1.5 text-white/20">·</span>
          {siteConfig.contextRegion}
        </span>
      </div>

      <LiveDot label="Live" className="hidden sm:inline-flex" />

      <NotificationPopover />

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            type="button"
            variant="ghost"
            className="h-9 gap-2 px-1.5"
            aria-label="User menu"
          >
            <Avatar size="sm" className="bg-weather/15">
              <AvatarFallback className="bg-weather/15 text-[10px] font-semibold text-weather-secondary">
                DA
              </AvatarFallback>
            </Avatar>
            <span className="hidden text-left sm:block">
              <span className="block text-xs font-medium text-foreground">
                Duty Analyst
              </span>
              <span className="block text-[11px] text-muted-foreground">
                NDMA Desk
              </span>
            </span>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-56">
          <DropdownMenuLabel>Session</DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuItem disabled>Profile — later phase</DropdownMenuItem>
          <DropdownMenuItem disabled>Preferences — later phase</DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </header>
  );
}
