"use client";

import { useAlerts } from "@/hooks/useAlerts";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Bell, BellRing, Check, Info, Loader2, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";

const ALERT_TYPE_LABELS: Record<string, string> = {
  INCIDENT_CREATED:        "New Correlated Incident",
  INCIDENT_ESCALATED:      "Incident Escalated",
  INCIDENT_STATUS_CHANGED: "Incident Status Changed",
  INCIDENT_TREND_CHANGED:  "Incident Trend Changed",
  VERIFICATION_REQUIRED:   "Verification Required",
  REPORT_VERIFIED:         "Report Verified",
  REPORT_REJECTED:         "Report Rejected",
};

const SCOPE_LABELS: Record<string, string> = {
  ADMIN:            "Admin",
  ANALYST:          "Analyst",
  VERIFIER:         "Verifier",
  CITIZEN_REPORTER: "Citizen",
};

export default function NotificationsPage() {
  const { data, isLoading, isError, markRead, markAcknowledged } = useAlerts({ limit: 100 });

  if (isLoading) {
    return (
      <div className="mx-auto flex w-full max-w-3xl flex-col gap-6 p-4 md:p-8">
        <header>
          <p className="text-xs font-semibold tracking-[0.1em] text-weather-secondary uppercase">
            Alert Centre
          </p>
          <h1 className="mt-1 text-2xl font-bold tracking-tight">Notifications</h1>
        </header>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Loader2 className="size-4 animate-spin" />
          Loading your alerts…
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="mx-auto flex w-full max-w-3xl flex-col gap-6 p-4 md:p-8">
        <header>
          <p className="text-xs font-semibold tracking-[0.1em] text-weather-secondary uppercase">
            Alert Centre
          </p>
          <h1 className="mt-1 text-2xl font-bold tracking-tight">Notifications</h1>
        </header>
        <div className="flex items-center gap-2 rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          <AlertTriangle className="size-4 shrink-0" />
          Unable to load notifications. Please ensure the backend is running.
        </div>
      </div>
    );
  }

  const alerts = data?.items ?? [];
  const unread_count = data?.unread_count ?? 0;

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-col gap-6 p-4 md:p-8">
      <header className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold tracking-[0.1em] text-weather-secondary uppercase">
            Alert Centre
          </p>
          <h1 className="mt-1 text-2xl font-bold tracking-tight">Notifications</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {unread_count > 0
              ? `${unread_count} unread ${unread_count === 1 ? "alert" : "alerts"} — real-time from database`
              : "All alerts from the live database are shown here."}
          </p>
        </div>
        <span className="mt-1 shrink-0 rounded-full border border-white/10 bg-white/4 px-2 py-0.5 text-[10px] font-semibold tracking-[0.1em] text-muted-foreground">
          LIVE DB
        </span>
      </header>

      <div className="grid gap-3">
        {alerts.length === 0 ? (
          <Card className="border-white/10 bg-card/40">
            <CardContent className="flex flex-col items-center justify-center p-16 text-center">
              <Bell className="mb-4 h-12 w-12 text-muted-foreground/30" />
              <p className="text-base font-medium text-foreground">No alerts yet</p>
              <p className="mt-1 max-w-xs text-sm text-muted-foreground">
                Alerts appear here when incidents are correlated, escalated, or when
                reports are verified. Run the demo seed to populate example alerts.
              </p>
            </CardContent>
          </Card>
        ) : (
          alerts.map((alert) => (
            <Card
              key={alert.id}
              className={cn(
                "border-white/10 bg-card/40 transition-colors",
                alert.status === "UNREAD"
                  ? "border-l-4 border-l-weather-secondary bg-weather/4"
                  : "",
              )}
            >
              <CardHeader className="flex flex-row items-start justify-between gap-3 pb-2">
                <div className="min-w-0 flex-1 space-y-1">
                  <div className="flex flex-wrap items-center gap-2">
                    {alert.status === "UNREAD" ? (
                      <BellRing className="size-4 shrink-0 text-weather-secondary" />
                    ) : (
                      <Info className="size-4 shrink-0 text-muted-foreground" />
                    )}
                    <CardTitle className="text-sm font-semibold leading-snug">
                      {alert.title}
                    </CardTitle>
                    {alert.severity && (
                      <Badge
                        variant="outline"
                        className={
                          alert.severity === "CRITICAL"
                            ? "border-red-500/50 text-red-400"
                            : alert.severity === "HIGH"
                              ? "border-orange-500/50 text-orange-400"
                              : alert.severity === "MEDIUM"
                                ? "border-yellow-500/50 text-yellow-400"
                                : "border-green-500/50 text-green-400"
                        }
                      >
                        {alert.severity}
                      </Badge>
                    )}
                  </div>
                  <CardDescription className="text-[11px]">
                    {new Date(alert.created_at).toLocaleString("en-IN", {
                      dateStyle: "medium",
                      timeStyle: "short",
                    })}
                  </CardDescription>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  {alert.status === "UNREAD" && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => markRead.mutate(alert.id)}
                      disabled={markRead.isPending}
                      className="h-7 border-white/12 bg-white/4 px-2 text-xs"
                    >
                      <Check className="mr-1 h-3 w-3" />
                      Read
                    </Button>
                  )}
                  {alert.status !== "ACKNOWLEDGED" && (
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => markAcknowledged.mutate(alert.id)}
                      disabled={markAcknowledged.isPending}
                      className="h-7 bg-white/6 px-2 text-xs"
                    >
                      Acknowledge
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent className="pt-0">
                <p className="text-sm text-foreground/85">{alert.message}</p>
                <div className="mt-3 flex flex-wrap gap-3 text-[11px] text-muted-foreground">
                  <span className="font-mono">
                    {ALERT_TYPE_LABELS[alert.alert_type] ?? alert.alert_type}
                  </span>
                  <span>·</span>
                  <span>
                    Scope: {SCOPE_LABELS[alert.recipient_scope] ?? alert.recipient_scope}
                  </span>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}


