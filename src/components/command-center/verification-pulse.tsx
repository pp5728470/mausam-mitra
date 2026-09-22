"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { getReports } from "@/lib/api";

type Counts = {
  pending: number;
  corroborated: number;
  underReview: number;
  verified: number;
};

/**
 * Compact Command Center indicators — reports are signals, not incidents.
 */
export function VerificationPulse() {
  const [counts, setCounts] = useState<Counts | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    void (async () => {
      try {
        const page = await getReports(
          { limit: 200 },
          { signal: controller.signal },
        );
        if (controller.signal.aborted) return;
        const items = page.items;
        setCounts({
          pending: items.filter(
            (r) =>
              r.verification_status === "PENDING" ||
              r.status === "NEW",
          ).length,
          corroborated: items.filter(
            (r) => r.verification_status === "CORROBORATED",
          ).length,
          underReview: items.filter(
            (r) => r.verification_status === "UNDER_REVIEW",
          ).length,
          verified: items.filter(
            (r) => r.verification_status === "VERIFIED",
          ).length,
        });
      } catch {
        if (!controller.signal.aborted) setCounts(null);
      }
    })();
    return () => controller.abort();
  }, []);

  if (!counts) return null;

  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-muted-foreground">
      <span>
        Reports NEW/pending:{" "}
        <span className="font-mono text-foreground/90">{counts.pending}</span>
      </span>
      <span>
        Corroborated:{" "}
        <span className="font-mono text-weather-secondary">
          {counts.corroborated}
        </span>
      </span>
      <span>
        Under review:{" "}
        <span className="font-mono text-warning">{counts.underReview}</span>
      </span>
      <span>
        Verified:{" "}
        <span className="font-mono text-success">{counts.verified}</span>
      </span>
      <Link
        href="/verification"
        className="font-semibold tracking-[0.08em] text-weather-secondary hover:underline"
      >
        OPEN VERIFICATION
      </Link>
    </div>
  );
}
