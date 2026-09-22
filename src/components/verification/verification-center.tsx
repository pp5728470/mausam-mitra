"use client";

import {
  AlertTriangle,
  CheckCircle2,
  ClipboardCheck,
  Loader2,
  MapPin,
  RefreshCw,
  ShieldAlert,
  BrainCircuit,
} from "lucide-react";
import { useMemo, useState } from "react";

import { useVerificationCenter } from "@/hooks/use-verification-center";
import { formatCoord, formatReceivedLabel } from "@/lib/api/adapters/reports";
import type { ApiEvidence } from "@/lib/api/types";
import {
  formatEvidenceScoreDetail,
  formatEvidenceScoreLabel,
  formatFactorScore,
  toNullableScore,
} from "@/lib/verification/format";
import { cn } from "@/lib/utils";

function scoreBar(score: unknown) {
  const n = toNullableScore(score);
  if (n === null) return 0;
  return Math.max(0, Math.min(100, n));
}

function EvidenceCard({ item }: { item: ApiEvidence }) {
  const available = item.metadata?.available !== false;
  const hasScore = toNullableScore(item.score) !== null;
  const width = scoreBar(item.score);

  return (
    <article className="rounded-lg bg-white/3 px-3 py-3 ring-1 ring-white/8">
      <div className="flex items-start justify-between gap-2">
        <p className="text-[11px] font-semibold tracking-[0.1em] text-weather-secondary">
          {item.evidence_type.replaceAll("_", " ")}
        </p>
        <span className="font-mono text-xs text-foreground">
          {formatFactorScore(item.score, available)}
        </span>
      </div>
      <p className="mt-1 text-sm font-medium text-foreground">{item.title}</p>
      <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-white/8">
        <div
          className={cn(
            "h-full rounded-full",
            available && hasScore ? "bg-weather" : "bg-white/15",
          )}
          style={{ width: `${hasScore ? width : 8}%` }}
        />
      </div>
      <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
        {item.description}
      </p>
      {item.evidence_type === "WEATHER_CORRELATION" && Boolean(item.metadata?.live_weather) && (
        <div className="mt-3 grid grid-cols-2 gap-2 rounded-md bg-white/5 p-2 text-[10px] text-muted-foreground">
          {Boolean(item.metadata?.provider) && (
            <div>
              <span className="block font-semibold">PROVIDER</span>
              <span className="text-foreground">{String(item.metadata?.provider)}</span>
            </div>
          )}
          {item.metadata?.distance_km !== undefined && (
            <div>
              <span className="block font-semibold">DISTANCE</span>
              <span className="text-foreground">{String(item.metadata?.distance_km)} km</span>
            </div>
          )}
          {item.metadata?.temperature !== undefined && (
            <div>
              <span className="block font-semibold">TEMPERATURE</span>
              <span className="text-foreground">{String(item.metadata?.temperature)}°C</span>
            </div>
          )}
          {item.metadata?.rainfall !== undefined && (
            <div>
              <span className="block font-semibold">PRECIPITATION</span>
              <span className="text-foreground">{String(item.metadata?.rainfall)} mm</span>
            </div>
          )}
          {item.metadata?.wind_speed !== undefined && (
            <div>
              <span className="block font-semibold">WIND</span>
              <span className="text-foreground">{String(item.metadata?.wind_speed)} m/s</span>
            </div>
          )}
        </div>
      )}
    </article>
  );
}

export function VerificationCenter() {
  const {
    reports,
    selected,
    selectedId,
    setSelectedId,
    evidence,
    coverage,
    recommendation,
    evaluated,
    summary,
    isLoading,
    isEvaluating,
    isVerifying,
    isClassifying,
    error,
    actionError,
    refresh,
    runEvaluate,
    runVerify,
    runClassify,
  } = useVerificationCenter();

  const [notes, setNotes] = useState("");

  const queue = useMemo(() => {
    return [...reports].sort((a, b) => {
      const rank = (s: string) =>
        s === "PENDING" || s === "UNDER_REVIEW" || s === "CORROBORATED"
          ? 0
          : 1;
      const d = rank(a.verificationStatus) - rank(b.verificationStatus);
      if (d !== 0) return d;
      return Date.parse(b.receivedAt) - Date.parse(a.receivedAt);
    });
  }, [reports]);

  return (
    <div className="mx-auto flex w-full max-w-[1600px] flex-col gap-5">
      <header className="rounded-xl bg-surface/80 px-4 py-5 ring-1 ring-white/6 sm:px-6">
        <p className="text-label text-weather-secondary">Evidence intelligence</p>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
          Verification Center
        </h1>
        <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
          Review weather signals using explainable evidence. Evidence assists
          review — final verification is a human decision. Reports are not
          automatically verified or converted into incidents.
        </p>
      </header>

      <section className="grid grid-cols-2 gap-3 xl:grid-cols-4">
        {[
          {
            label: "Awaiting review",
            value: summary.awaiting,
            tone: "text-warning",
          },
          {
            label: "Corroborated signals",
            value: summary.corroborated,
            tone: "text-weather-secondary",
          },
          {
            label: "Needs review",
            value: summary.needsReview,
            tone: "text-amber-300",
          },
          {
            label: "Verified",
            value: summary.verified,
            tone: "text-success",
          },
        ].map((card) => (
          <div
            key={card.label}
            className="rounded-xl bg-card/60 px-3.5 py-3 ring-1 ring-white/6"
          >
            <p className="text-label">{card.label}</p>
            <p className={cn("text-metric mt-2 text-[1.75rem]", card.tone)}>
              {String(card.value).padStart(2, "0")}
            </p>
          </div>
        ))}
      </section>

      {error ? (
        <p className="rounded-lg border border-critical/25 bg-critical/10 px-3 py-2 text-sm">
          {error}
        </p>
      ) : null}

      <div className="grid gap-4 xl:grid-cols-[22rem_minmax(0,1fr)]">
        <section className="rounded-xl bg-card/60 px-3 py-3 ring-1 ring-white/6">
          <div className="mb-2 flex items-center justify-between gap-2 px-1">
            <h2 className="text-section-title">Report queue</h2>
            <button
              type="button"
              onClick={refresh}
              className="inline-flex items-center gap-1 rounded-full border border-white/10 px-2 py-0.5 text-[10px] font-semibold tracking-[0.1em] text-muted-foreground"
            >
              <RefreshCw
                className={cn("size-3", isLoading && "animate-spin")}
              />
              REFRESH
            </button>
          </div>
          <ul className="max-h-[42rem] space-y-2 overflow-y-auto pr-1">
            {queue.map((report) => (
              <li key={report.id}>
                <button
                  type="button"
                  onClick={() => setSelectedId(report.id)}
                  className={cn(
                    "w-full rounded-lg px-3 py-2.5 text-left transition",
                    selectedId === report.id
                      ? "bg-weather/12 ring-1 ring-weather/30"
                      : "bg-white/3 hover:bg-white/5",
                  )}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-[10px] font-semibold tracking-[0.12em] text-muted-foreground">
                      {report.status}
                    </span>
                    <span className="font-mono text-[11px] text-weather-secondary">
                      Evidence {formatEvidenceScoreLabel(report.evidenceScore)}
                    </span>
                  </div>
                  <p className="mt-1 text-sm font-medium text-foreground">
                    {report.title}
                  </p>
                  <p className="mt-0.5 text-[11px] text-muted-foreground">
                    {report.locationLabel} · {report.sourceType} ·{" "}
                    {report.receivedLabel}
                  </p>
                  <p className="mt-1 text-[10px] font-semibold tracking-[0.1em] text-muted-foreground">
                    {report.verificationStatus}
                  </p>
                </button>
              </li>
            ))}
            {!isLoading && queue.length === 0 ? (
              <li className="px-2 py-6 text-sm text-muted-foreground">
                No reports available for review.
              </li>
            ) : null}
          </ul>
        </section>

        <section className="rounded-xl bg-card/60 px-4 py-4 ring-1 ring-white/6 sm:px-5">
          {!selected ? (
            <p className="text-sm text-muted-foreground">
              Select a report to inspect evidence.
            </p>
          ) : (
            <div className="space-y-5">
              <div>
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="text-label text-weather-secondary">
                      Selected signal
                    </p>
                    <h2 className="mt-1 text-xl font-semibold text-foreground">
                      {selected.title}
                    </h2>
                    <p className="mt-1 flex items-center gap-1.5 text-sm text-muted-foreground">
                      <MapPin className="size-3.5" />
                      {formatCoord(selected.latitude)},{" "}
                      {formatCoord(selected.longitude)}
                    </p>
                  </div>
                  <button
                    type="button"
                    disabled={isEvaluating}
                    onClick={() => void runEvaluate(selected.id)}
                    className="inline-flex min-h-10 items-center gap-2 rounded-lg border border-white/12 bg-white/4 px-3 text-xs font-semibold tracking-[0.08em] text-foreground"
                  >
                    {isEvaluating ? (
                      <Loader2 className="size-3.5 animate-spin" />
                    ) : (
                      <ClipboardCheck className="size-3.5" />
                    )}
                    {evaluated ? "RE-EVALUATE" : "EVALUATE EVIDENCE"}
                  </button>
                </div>
                <p className="mt-3 text-sm leading-relaxed text-foreground/85">
                  {selected.description}
                </p>
              </div>

              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                <div className="rounded-lg bg-white/3 px-3 py-2 ring-1 ring-white/8">
                  <p className="text-[10px] tracking-[0.12em] text-muted-foreground">
                    STATUS
                  </p>
                  <p className="mt-1 text-sm font-semibold">{selected.status}</p>
                </div>
                <div className="rounded-lg bg-white/3 px-3 py-2 ring-1 ring-white/8">
                  <p className="text-[10px] tracking-[0.12em] text-muted-foreground">
                    VERIFICATION
                  </p>
                  <p className="mt-1 text-sm font-semibold">
                    {selected.verificationStatus}
                  </p>
                </div>
                <div className="rounded-lg bg-white/3 px-3 py-2 ring-1 ring-white/8">
                  <p className="text-[10px] tracking-[0.12em] text-muted-foreground">
                    EVIDENCE SCORE
                  </p>
                  <p className="mt-1 font-mono text-lg text-weather-secondary">
                    {formatEvidenceScoreDetail(selected.evidenceScore)}
                  </p>
                </div>
                <div className="rounded-lg bg-white/3 px-3 py-2 ring-1 ring-white/8">
                  <p className="text-[10px] tracking-[0.12em] text-muted-foreground">
                    COVERAGE
                  </p>
                  <p className="mt-1 text-sm font-semibold">
                    {evaluated && coverage ? coverage : "Not available"}
                  </p>
                </div>
              </div>

              {!evaluated ? (
                <div className="rounded-lg border border-warning/25 bg-warning/8 px-4 py-4">
                  <p className="text-label text-warning">Evidence</p>
                  <p className="mt-1 text-sm font-semibold text-foreground">
                    Not evaluated
                  </p>
                  <p className="mt-2 text-sm text-muted-foreground">
                    Evidence evaluation has not been run for this report.
                  </p>
                  <button
                    type="button"
                    disabled={isEvaluating}
                    onClick={() => void runEvaluate(selected.id)}
                    className="mt-3 inline-flex min-h-10 items-center gap-2 rounded-lg bg-weather px-4 text-sm font-semibold text-slate-950 disabled:opacity-60"
                  >
                    {isEvaluating ? (
                      <Loader2 className="size-3.5 animate-spin" />
                    ) : (
                      <ClipboardCheck className="size-3.5" />
                    )}
                    Evaluate Evidence
                  </button>
                </div>
              ) : (
                <>
                  {recommendation ? (
                    <p className="rounded-lg border border-weather/20 bg-weather/8 px-3 py-2 text-sm">
                      Recommendation:{" "}
                      <span className="font-semibold text-weather-secondary">
                        {recommendation}
                      </span>
                      <span className="mt-1 block text-xs text-muted-foreground">
                        Available evidence supports further human review. This
                        is not a truth claim.
                      </span>
                    </p>
                  ) : null}

                  <div>
                    <h3 className="text-section-title">Evidence factors</h3>
                    {evidence.length === 0 ? (
                      <div className="mt-3 rounded-lg border border-white/10 bg-white/3 px-4 py-4">
                        <p className="text-sm font-semibold tracking-[0.08em] text-muted-foreground">
                          NO SUPPORTING EVIDENCE AVAILABLE
                        </p>
                        <p className="mt-2 text-sm text-muted-foreground">
                          Available evidence is currently insufficient for
                          automated corroboration. Human review is still
                          required.
                        </p>
                      </div>
                    ) : (
                      <div className="mt-3 grid gap-3 md:grid-cols-2">
                        {evidence.map((item) => (
                          <EvidenceCard
                            key={item.id || item.evidence_type}
                            item={item}
                          />
                        ))}
                      </div>
                    )}
                  </div>
                </>
              )}

              <div className="rounded-xl border border-white/10 bg-white/3 px-4 py-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-2">
                    <BrainCircuit className="mt-0.5 size-4 text-weather" />
                    <div>
                      <h3 className="text-sm font-semibold text-foreground">
                        AI-Assisted Classification
                      </h3>
                      <p className="mt-1 text-xs text-muted-foreground">
                        Phase 10 intelligent signal classification. Assesses category and confidence from raw report text.
                      </p>
                    </div>
                  </div>
                  <button
                    type="button"
                    disabled={isClassifying}
                    onClick={() => void runClassify()}
                    className="inline-flex min-h-9 items-center gap-2 rounded-lg bg-weather/10 px-3 text-xs font-semibold tracking-[0.08em] text-weather transition hover:bg-weather/20 disabled:opacity-60"
                  >
                    {isClassifying ? (
                      <Loader2 className="size-3.5 animate-spin" />
                    ) : (
                      <BrainCircuit className="size-3.5" />
                    )}
                    {selected.classifiedCategory ? "RE-CLASSIFY" : "CLASSIFY SIGNAL"}
                  </button>
                </div>

                {selected.classifiedCategory ? (
                  <div className="mt-4 rounded-lg bg-white/5 px-3 py-3 ring-1 ring-white/10">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="rounded bg-weather/20 px-2 py-0.5 text-xs font-bold text-weather">
                          {selected.classifiedCategory}
                        </span>
                        <span className="text-xs font-medium text-foreground">
                          {selected.classifierConfidence !== null
                            ? `${Math.round(selected.classifierConfidence * 100)}% Confidence`
                            : ""}
                        </span>
                      </div>
                      <span className="text-[10px] uppercase tracking-wider text-muted-foreground">
                        {selected.classifierVersion}
                      </span>
                    </div>
                    {selected.classificationExplanation && (
                      <p className="mt-2 text-sm text-foreground/90">
                        {selected.classificationExplanation}
                      </p>
                    )}
                    {selected.classificationSignals && selected.classificationSignals.length > 0 && (
                      <div className="mt-3 space-y-1.5">
                        <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                          Detected Signals
                        </p>
                        <div className="flex flex-wrap gap-2">
                          {selected.classificationSignals.map((sig, i) => (
                            <div
                              key={i}
                              className="flex items-center gap-1.5 rounded-full bg-white/5 px-2 py-0.5 text-xs text-foreground ring-1 ring-white/10"
                            >
                              <span>&quot;{sig.phrase}&quot;</span>
                              <span className="text-muted-foreground">
                                (w: {sig.weight})
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ) : null}
              </div>

              <div className="rounded-xl border border-white/10 bg-white/3 px-4 py-4">
                <div className="flex items-start gap-2">
                  <ShieldAlert className="mt-0.5 size-4 text-warning" />
                  <div>
                    <h3 className="text-sm font-semibold text-foreground">
                      Final review
                    </h3>
                    <p className="mt-1 text-xs text-muted-foreground">
                      Evidence assists review. Final verification is performed
                      by an authorized human. Verification does not create an
                      incident.
                    </p>
                  </div>
                </div>

                {selected.verificationStatus === "VERIFIED" ||
                selected.verificationStatus === "REJECTED" ? (
                  <div
                    className={cn(
                      "mt-4 rounded-lg px-3 py-3 ring-1",
                      selected.verificationStatus === "VERIFIED"
                        ? "bg-success/8 ring-success/20"
                        : "bg-critical/8 ring-critical/20",
                    )}
                  >
                    <p
                      className={cn(
                        "flex items-center gap-2 text-sm font-semibold",
                        selected.verificationStatus === "VERIFIED"
                          ? "text-success"
                          : "text-critical",
                      )}
                    >
                      <CheckCircle2 className="size-4" />
                      {selected.verificationStatus}
                    </p>
                    <p className="mt-2 text-xs text-muted-foreground">
                      Verified at:{" "}
                      {selected.verifiedAt
                        ? formatReceivedLabel(selected.verifiedAt)
                        : "—"}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Verified by: {selected.verifiedBy ?? "—"}
                    </p>
                    <p className="mt-1 text-xs text-foreground/85">
                      {selected.verificationNotes ?? "No notes."}
                    </p>
                    {toNullableScore(selected.evidenceScore) !== null ? (
                      <p className="mt-2 font-mono text-xs text-weather-secondary">
                        Evidence score remains{" "}
                        {formatEvidenceScoreDetail(selected.evidenceScore)}
                      </p>
                    ) : null}
                  </div>
                ) : (
                  <>
                    <label className="mt-4 block text-label" htmlFor="v-notes">
                      Reviewer notes
                    </label>
                    <textarea
                      id="v-notes"
                      value={notes}
                      onChange={(e) => setNotes(e.target.value)}
                      rows={3}
                      className="mt-1.5 w-full rounded-lg border border-white/10 bg-white/4 px-3 py-2 text-sm outline-none ring-weather/30 focus:ring-2"
                      placeholder="Evidence reviewed by authorized operator."
                    />
                    <div className="mt-3 flex flex-wrap gap-2">
                      <button
                        type="button"
                        disabled={isVerifying}
                        onClick={() => void runVerify("VERIFIED", notes)}
                        className="inline-flex min-h-11 items-center rounded-lg bg-success/90 px-4 text-sm font-semibold text-slate-950 disabled:opacity-60"
                      >
                        Verify Report
                      </button>
                      <button
                        type="button"
                        disabled={isVerifying}
                        onClick={() => void runVerify("REJECTED", notes)}
                        className="inline-flex min-h-11 items-center rounded-lg bg-critical/90 px-4 text-sm font-semibold text-white disabled:opacity-60"
                      >
                        Reject Report
                      </button>
                      <button
                        type="button"
                        disabled={isVerifying}
                        onClick={() => void runVerify("NEEDS_REVIEW", notes)}
                        className="inline-flex min-h-11 items-center rounded-lg border border-warning/40 bg-warning/15 px-4 text-sm font-semibold text-warning disabled:opacity-60"
                      >
                        Needs Review
                      </button>
                    </div>
                  </>
                )}

                {actionError ? (
                  <p
                    className="mt-3 flex items-start gap-2 text-sm text-critical"
                    role="alert"
                  >
                    <AlertTriangle className="mt-0.5 size-4 shrink-0" />
                    {actionError}
                  </p>
                ) : null}
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
