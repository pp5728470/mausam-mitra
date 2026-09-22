import { cn } from "@/lib/utils";

type SkipToContentProps = {
  href?: string;
  className?: string;
};

/**
 * In-page skip link — must be a native anchor.
 * Next.js <Link> is for route transitions; hash-only targets should not go
 * through the App Router link layer (avoids href/prefetch attribute drift).
 */
export function SkipToContent({
  href = "#main-content",
  className,
}: SkipToContentProps) {
  return (
    <a
      href={href}
      className={cn(
        "sr-only focus:not-sr-only focus:absolute focus:top-3 focus:left-3 focus:z-80 focus:rounded-md focus:bg-card focus:px-3 focus:py-2 focus:text-sm focus:text-foreground",
        className,
      )}
    >
      Skip to content
    </a>
  );
}
