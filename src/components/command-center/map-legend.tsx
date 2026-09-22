import { SEVERITY_COLORS } from "@/lib/incidents/utils";

const LEGEND_ITEMS = [
  { label: "Critical", color: SEVERITY_COLORS.critical },
  { label: "High", color: SEVERITY_COLORS.high },
  { label: "Medium", color: SEVERITY_COLORS.medium },
  { label: "Low", color: SEVERITY_COLORS.low },
] as const;

export function MapLegend() {
  return (
    <div
      className="pointer-events-none rounded-lg border border-white/10 bg-background/85 px-2.5 py-2 backdrop-blur-sm"
      aria-hidden
    >
      <p className="text-[10px] font-semibold tracking-[0.12em] text-muted-foreground uppercase">
        Severity
      </p>
      <ul className="mt-1.5 space-y-1">
        {LEGEND_ITEMS.map((item) => (
          <li key={item.label} className="flex items-center gap-2 text-[11px] text-foreground/85">
            <span
              className="size-2.5 rounded-full ring-1 ring-white/40"
              style={{ backgroundColor: item.color }}
            />
            {item.label}
          </li>
        ))}
      </ul>
    </div>
  );
}
