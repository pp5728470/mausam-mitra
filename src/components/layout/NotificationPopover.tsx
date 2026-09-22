"use client";

import { Bell } from "lucide-react";
import Link from "next/link";
import { useAlerts } from "@/hooks/useAlerts";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";

export function NotificationPopover() {
  const { data, markRead } = useAlerts({ limit: 5 });

  const alerts = data?.items || [];
  const unread_count = data?.unread_count || 0;

  return (
    <DropdownMenu onOpenChange={(open) => {
      if (open) {
        // We could invalidate or refetch here if we wanted
      }
    }}>
      <DropdownMenuTrigger asChild>
        <Button
          type="button"
          variant="ghost"
          size="icon"
          aria-label="Notifications"
          className="relative"
        >
          <Bell />
          {unread_count > 0 && (
            <span className="absolute top-2 right-2 flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-weather-secondary opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-weather-secondary"></span>
            </span>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-80 max-h-[85vh] overflow-y-auto">
        <DropdownMenuLabel className="flex justify-between items-center">
          <span>Notifications</span>
          {unread_count > 0 && (
            <span className="text-xs bg-muted px-2 py-0.5 rounded-full">
              {unread_count} new
            </span>
          )}
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        
        {alerts.length === 0 ? (
          <p className="px-4 py-6 text-sm text-center text-muted-foreground">
            No new notifications.
          </p>
        ) : (
          <div className="flex flex-col gap-1 p-1">
            {alerts.map((alert) => (
              <DropdownMenuItem 
                key={alert.id} 
                className={cn(
                  "flex flex-col items-start gap-1 p-3 cursor-pointer",
                  alert.status === 'UNREAD' ? "bg-muted/50" : ""
                )}
                onSelect={(e) => {
                  e.preventDefault();
                  if (alert.status === 'UNREAD') {
                    markRead.mutate(alert.id);
                  }
                }}
              >
                <div className="flex justify-between items-start w-full gap-2">
                  <span className="font-medium text-sm leading-none">
                    {alert.title}
                  </span>
                  <span className="text-[10px] text-muted-foreground whitespace-nowrap">
                    {new Date(alert.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
                <span className="text-xs text-muted-foreground line-clamp-2">
                  {alert.message}
                </span>
              </DropdownMenuItem>
            ))}
          </div>
        )}
        
        <DropdownMenuSeparator />
        <div className="p-2">
          <Button variant="ghost" size="sm" className="w-full text-xs" asChild>
            <Link href="/notifications">
              View all notifications
            </Link>
          </Button>
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
