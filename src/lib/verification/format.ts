/**
 * Safe display helpers for Verification Center scores.
 * Never render NaN / Infinity / undefined as numeric UI.
 */

export function isFiniteNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

/** Normalize API score fields to `null` when missing or non-finite. */
export function toNullableScore(value: unknown): number | null {
  if (value === null || value === undefined) return null;
  if (typeof value === "string" && value.trim() === "") return null;
  const n = typeof value === "number" ? value : Number(value);
  return Number.isFinite(n) ? n : null;
}

/**
 * Queue / compact score label.
 * Evaluated: "82.6" — Unevaluated: "—"
 */
export function formatEvidenceScoreLabel(score: unknown): string {
  const n = toNullableScore(score);
  if (n === null) return "—";
  return Number.isInteger(n) ? String(n) : n.toFixed(1);
}

/**
 * Detail panel score.
 * Evaluated: "82.6 / 100" — Unevaluated: "Not evaluated"
 */
export function formatEvidenceScoreDetail(score: unknown): string {
  const n = toNullableScore(score);
  if (n === null) return "Not evaluated";
  const label = Number.isInteger(n) ? String(n) : n.toFixed(1);
  return `${label} / 100`;
}

/**
 * Factor card score.
 * Available numeric: "88 / 100" — Unavailable: "Unavailable"
 */
export function formatFactorScore(score: unknown, available: boolean): string {
  if (!available) return "Unavailable";
  const n = toNullableScore(score);
  if (n === null) return "Not available";
  const label = Number.isInteger(n) ? String(n) : n.toFixed(1);
  return `${label} / 100`;
}

export function hasBeenEvaluated(input: {
  evidenceScore: unknown;
  evidenceCount: number;
  recommendation: string | null | undefined;
}): boolean {
  if (isFiniteNumber(toNullableScore(input.evidenceScore))) return true;
  if (input.evidenceCount > 0) return true;
  if (input.recommendation) return true;
  return false;
}
