import { cn } from "@/lib/utils";

type LiveDotProps = {
  label: string;
  className?: string;
};

export function LiveDot({ label, className }: LiveDotProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-2 text-xs text-muted-foreground",
        className,
      )}
    >
      <span className="relative flex size-2" aria-hidden>
        <span className="status-ping absolute inset-0 rounded-full bg-success" />
        <span className="relative size-2 rounded-full bg-success" />
      </span>
      <span>
        <span className="sr-only">Live status: </span>
        {label}
      </span>
    </span>
  );
}
