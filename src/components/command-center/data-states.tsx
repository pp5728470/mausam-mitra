"use client";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type DataStateProps = {
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
};

export function CommandLoadingState({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "flex min-h-40 items-center justify-center rounded-xl bg-card/60 ring-1 ring-white/6",
        className,
      )}
      role="status"
      aria-live="polite"
    >
      <div className="text-center">
        <div className="mx-auto mb-3 size-5 animate-spin rounded-full border-2 border-weather/30 border-t-weather" />
        <p className="text-sm text-muted-foreground">
          Loading incident intelligence…
        </p>
      </div>
    </div>
  );
}

export function CommandEmptyState({
  title,
  description,
  className,
}: DataStateProps) {
  return (
    <div
      className={cn(
        "flex min-h-40 flex-col items-center justify-center rounded-xl bg-card/60 px-6 text-center ring-1 ring-white/6",
        className,
      )}
    >
      <p className="text-sm font-medium text-foreground">{title}</p>
      <p className="mt-1 max-w-sm text-xs text-muted-foreground">{description}</p>
    </div>
  );
}

export function CommandErrorState({
  title = "Unable to load incident intelligence.",
  description = "The intelligence feed could not be retrieved. Try again shortly.",
  actionLabel = "Retry",
  onAction,
  className,
}: DataStateProps) {
  return (
    <div
      className={cn(
        "flex min-h-40 flex-col items-center justify-center rounded-xl bg-card/60 px-6 text-center ring-1 ring-critical/20",
        className,
      )}
      role="alert"
    >
      <p className="text-sm font-medium text-foreground">{title}</p>
      <p className="mt-1 max-w-sm text-xs text-muted-foreground">{description}</p>
      {onAction ? (
        <Button type="button" size="sm" className="mt-4" onClick={onAction}>
          {actionLabel}
        </Button>
      ) : null}
    </div>
  );
}
