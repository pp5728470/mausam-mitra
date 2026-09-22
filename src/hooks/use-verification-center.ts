"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import {
  isApiReportPage,
  mapApiReportToListItem,
  type ReportListItem,
} from "@/lib/api/adapters/reports";
import {
  ApiError,
  evaluateReport,
  getReportEvidence,
  getReports,
  verifyReport,
  classifyReport,
} from "@/lib/api";
import type {
  ApiEvidence,
  ApiEvaluateResponse,
  ApiVerificationDecision,
  ApiVerifyResponse,
} from "@/lib/api/types";
import { hasBeenEvaluated, toNullableScore } from "@/lib/verification/format";

export type VerificationSummary = {
  awaiting: number;
  corroborated: number;
  needsReview: number;
  verified: number;
};

function isAbortError(err: unknown): boolean {
  return (
    (typeof DOMException !== "undefined" &&
      err instanceof DOMException &&
      err.name === "AbortError") ||
    (err instanceof Error && err.name === "AbortError")
  );
}

export function useVerificationCenter() {
  const [reports, setReports] = useState<ReportListItem[]>([]);
  const [selectedId, setSelectedIdState] = useState<string | null>(null);
  const [evidence, setEvidence] = useState<ApiEvidence[]>([]);
  const [evidenceForId, setEvidenceForId] = useState<string | null>(null);
  const [coverage, setCoverage] = useState<string | null>(null);
  const [recommendation, setRecommendation] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false);
  const [isClassifying, setIsClassifying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [token, setToken] = useState(0);

  const setSelectedId = useCallback((id: string | null) => {
    setSelectedIdState(id);
    // Clear synchronously so a prior report's factors never paint on the next.
    setEvidence([]);
    setEvidenceForId(null);
    setCoverage(null);
    setRecommendation(null);
  }, []);

  const refresh = useCallback(() => {
    setIsLoading(true);
    setError(null);
    setToken((n) => n + 1);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void (async () => {
      try {
        const page = await getReports(
          { limit: 80, offset: 0 },
          { signal: controller.signal },
        );
        if (controller.signal.aborted) return;
        if (!isApiReportPage(page)) {
          throw new ApiError(
            "Unexpected reports response shape",
            200,
            "/api/v1/reports",
          );
        }
        const items = page.items.map(mapApiReportToListItem);
        setReports(items);
        setSelectedIdState((current) => {
          if (current && items.some((r) => r.id === current)) return current;
          return items[0]?.id ?? null;
        });
        setError(null);
      } catch (err) {
        if (controller.signal.aborted || isAbortError(err)) return;
        setError(
          err instanceof ApiError
            ? err.message
            : "Unable to load verification queue.",
        );
        setReports([]);
      } finally {
        if (!controller.signal.aborted) setIsLoading(false);
      }
    })();
    return () => controller.abort();
  }, [token]);

  const selected = useMemo(
    () => reports.find((r) => r.id === selectedId) ?? null,
    [reports, selectedId],
  );

  /** Counters from verification_status only — never infer from evidence_score. */
  const summary: VerificationSummary = useMemo(() => {
    return {
      awaiting: reports.filter(
        (r) =>
          r.verificationStatus === "PENDING" ||
          r.verificationStatus === "UNDER_REVIEW",
      ).length,
      corroborated: reports.filter(
        (r) => r.verificationStatus === "CORROBORATED",
      ).length,
      needsReview: reports.filter(
        (r) => r.verificationStatus === "UNDER_REVIEW",
      ).length,
      verified: reports.filter((r) => r.verificationStatus === "VERIFIED")
        .length,
    };
  }, [reports]);

  const selectedEvidence =
    evidenceForId === selectedId ? evidence : [];

  const evaluated = hasBeenEvaluated({
    evidenceScore: selected?.evidenceScore,
    evidenceCount: selectedEvidence.length,
    recommendation:
      recommendation ?? selected?.verificationRecommendation ?? null,
  });

  // Load stored evidence when selection changes (read-only).
  useEffect(() => {
    if (!selectedId) return;
    const controller = new AbortController();
    const reportId = selectedId;

    void (async () => {
      try {
        const items = await getReportEvidence(reportId, {
          signal: controller.signal,
        });
        if (controller.signal.aborted) return;
        setEvidence(items);
        setEvidenceForId(reportId);
        if (items.length === 0) {
          setCoverage(null);
        } else {
          const available = items.filter(
            (e) =>
              e.metadata?.available !== false &&
              toNullableScore(e.score) !== null,
          ).length;
          setCoverage(`${available} / ${items.length} signals available`);
        }
      } catch (err) {
        if (controller.signal.aborted || isAbortError(err)) return;
        setEvidence([]);
        setEvidenceForId(null);
        setCoverage(null);
      }
    })();
    return () => controller.abort();
  }, [selectedId]);

  const displayRecommendation =
    recommendation ?? selected?.verificationRecommendation ?? null;

  const displayCoverage =
    evidenceForId === selectedId || recommendation ? coverage : null;

  const runEvaluate = useCallback(async (reportId: string) => {
    setIsEvaluating(true);
    setActionError(null);
    try {
      const result: ApiEvaluateResponse = await evaluateReport(reportId);
      const score = toNullableScore(result.evidence_score);
      setEvidence(result.evidence);
      setEvidenceForId(reportId);
      setCoverage(result.evidence_coverage);
      setRecommendation(result.verification_recommendation);
      setReports((prev) =>
        prev.map((r) =>
          r.id === reportId
            ? {
                ...r,
                evidenceScore: score,
                verificationStatus:
                  result.report.verification_status ?? r.verificationStatus,
                verificationRecommendation:
                  result.verification_recommendation,
              }
            : r,
        ),
      );
      return result;
    } catch (err) {
      setActionError(
        err instanceof ApiError
          ? err.message
          : "Evidence evaluation failed.",
      );
      return null;
    } finally {
      setIsEvaluating(false);
    }
  }, []);

  const runVerify = useCallback(
    async (decision: ApiVerificationDecision, notes: string) => {
      if (!selectedId) return null;
      setIsVerifying(true);
      setActionError(null);
      try {
        const result: ApiVerifyResponse = await verifyReport(selectedId, {
          decision,
          notes: notes || null,
          verified_by: "authorized_operator",
        });
        setReports((prev) =>
          prev.map((r) =>
            r.id === selectedId
              ? {
                  ...r,
                  verificationStatus: result.report.verification_status,
                  verificationNotes: result.report.verification_notes,
                  verifiedAt: result.report.verified_at,
                  verifiedBy: result.report.verified_by,
                  status: result.report.status ?? r.status,
                  incidentId: result.report.incident_id,
                  evidenceScore: toNullableScore(
                    result.report.evidence_score ?? r.evidenceScore,
                  ),
                }
              : r,
          ),
        );
        return result;
      } catch (err) {
        setActionError(
          err instanceof ApiError
            ? err.message
            : "Verification request failed. No decision was recorded.",
        );
        return null;
      } finally {
        setIsVerifying(false);
      }
    },
    [selectedId],
  );

  const runClassify = useCallback(async () => {
    if (!selectedId) return null;
    setIsClassifying(true);
    setActionError(null);
    try {
      const result = await classifyReport(selectedId);
      setReports((prev) =>
        prev.map((r) =>
          r.id === selectedId
            ? {
                ...r,
                classifiedCategory: result.classified_category,
                classifierConfidence: result.confidence,
                classificationExplanation: result.explanation,
                classificationSignals: result.signals,
                classifiedAt: result.classifier_version,
                classifierVersion: result.classifier_version,
              }
            : r,
        ),
      );
      return result;
    } catch (err) {
      setActionError(
        err instanceof ApiError
          ? err.message
          : "AI Classification request failed.",
      );
      return null;
    } finally {
      setIsClassifying(false);
    }
  }, [selectedId]);

  return {
    reports,
    selected,
    selectedId,
    setSelectedId,
    evidence: selectedEvidence,
    coverage: displayCoverage,
    recommendation: displayRecommendation,
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
  };
}
