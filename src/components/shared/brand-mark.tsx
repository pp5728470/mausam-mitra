import Link from "next/link";
import { Cloud, MapPin } from "lucide-react";

import { siteConfig } from "@/config/site";
import { cn } from "@/lib/utils";

type BrandMarkProps = {
  href?: string;
  collapsed?: boolean;
  showMeaning?: boolean;
  className?: string;
};

export function BrandMark({
  href = "/",
  collapsed = false,
  showMeaning = false,
  className,
}: BrandMarkProps) {
  return (
    <Link
      href={href}
      className={cn(
        "group flex min-w-0 items-center gap-3 rounded-lg focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-weather",
        collapsed && "justify-center",
        className,
      )}
      aria-label={`${siteConfig.name}, ${siteConfig.subtitle}`}
    >
      <span className="relative flex size-9 shrink-0 items-center justify-center rounded-lg bg-weather/10 ring-1 ring-weather/25">
        <Cloud className="size-4 text-weather-secondary" aria-hidden />
        <MapPin
          className="absolute right-1 bottom-1 size-2.5 text-rain"
          aria-hidden
        />
      </span>
      {!collapsed ? (
        <span className="min-w-0">
          <span className="block truncate text-sm font-semibold tracking-tight text-foreground">
            {siteConfig.name}
          </span>
          <span className="block truncate text-[11px] text-muted-foreground">
            {showMeaning ? siteConfig.meaning : "Weather Intelligence"}
          </span>
        </span>
      ) : null}
    </Link>
  );
}
