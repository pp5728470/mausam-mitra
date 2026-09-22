import { OPERATIONAL_STATUSES } from "@/types/status";
import { getNavItem, type AppRoute } from "@/config/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/shared/status-badge";

type CommandPlaceholderProps = {
  href: AppRoute;
};

export function CommandPlaceholder({ href }: CommandPlaceholderProps) {
  const item = getNavItem(href);

  if (!item) {
    return null;
  }

  const Icon = item.icon;

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-6">
      <div className="flex items-start gap-3">
        <span className="mt-0.5 flex size-10 items-center justify-center rounded-xl bg-weather/10 ring-1 ring-weather/20">
          <Icon className="size-4 text-weather-secondary" aria-hidden />
        </span>
        <div>
          <p className="text-label">Module ready</p>
          <h2 className="text-section-title mt-1">{item.label}</h2>
          <p className="text-body mt-2 max-w-2xl text-muted-foreground">
            {item.description}
          </p>
        </div>
      </div>

      <Card className="bg-card/80">
        <CardHeader className="border-b border-white/5">
          <CardTitle>Awaiting data layer</CardTitle>
          <CardDescription>{item.phaseNote}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-5 pt-5">
          <div>
            <p className="text-label mb-3">Operational language</p>
            <div className="flex flex-wrap gap-2">
              {OPERATIONAL_STATUSES.map((status) => (
                <StatusBadge key={status} status={status} />
              ))}
            </div>
          </div>
          <Separator />
          <div className="grid gap-3 sm:grid-cols-3">
            <Skeleton className="h-20 rounded-xl bg-white/5" />
            <Skeleton className="h-20 rounded-xl bg-white/5" />
            <Skeleton className="h-20 rounded-xl bg-white/5" />
          </div>
          <p className="text-caption">
            FastAPI, PostGIS, Redis, Kafka, and model services can connect here
            without changing this layout.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
