"use client";

import { useMemo, useState, type FormEvent } from "react";
import Link from "next/link";
import {
  AlertTriangle,
  CheckCircle2,
  ImagePlus,
  Loader2,
  Send,
  ShieldAlert,
} from "lucide-react";

import {
  ReportLocationPicker,
  type PickedLocation,
} from "@/components/reports/report-location-picker";
import { ApiError, createReport } from "@/lib/api";
import {
  buildCitizenReportPayload,
  formatCoord,
  formatReceivedLabel,
  toPublicReportId,
} from "@/lib/api/adapters/reports";
import type { ApiReport } from "@/lib/api/types";
import {
  CITIZEN_INCIDENT_TYPES,
  REPORT_DESCRIPTION_MAX,
  REPORT_DESCRIPTION_MIN,
  REPORT_IMAGE_ACCEPT,
  REPORT_IMAGE_MAX_BYTES,
  REPORT_TITLE_MAX,
  REPORT_TITLE_MIN,
  type CitizenIncidentType,
} from "@/lib/reports/constants";
import { cn } from "@/lib/utils";

type SubmitPhase = "idle" | "validating" | "submitting" | "success" | "error";

type ReportIncidentFormProps = {
  onSubmitted?: (report: ApiReport) => void;
};

function validateImage(file: File | null): string | null {
  if (!file) return null;
  if (
    !(REPORT_IMAGE_ACCEPT as readonly string[]).includes(file.type) &&
    !/\.(jpe?g|png|webp)$/i.test(file.name)
  ) {
    return "Image must be JPG, PNG, or WEBP.";
  }
  if (file.size > REPORT_IMAGE_MAX_BYTES) {
    return "Image must be 5 MB or smaller.";
  }
  return null;
}

export function ReportIncidentForm({ onSubmitted }: ReportIncidentFormProps) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [incidentType, setIncidentType] = useState<CitizenIncidentType | "">(
    "",
  );
  const [location, setLocation] = useState<PickedLocation | null>(null);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [phase, setPhase] = useState<SubmitPhase>("idle");
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [created, setCreated] = useState<ApiReport | null>(null);

  const titleLen = title.trim().length;
  const descriptionLen = description.trim().length;

  const statusLabel = useMemo(() => {
    switch (phase) {
      case "validating":
        return "Validating…";
      case "submitting":
        return "Submitting…";
      default:
        return "Submit report";
    }
  }, [phase]);

  const resetForm = () => {
    setTitle("");
    setDescription("");
    setIncidentType("");
    setImageFile(null);
    setFieldErrors({});
    setSubmitError(null);
    setCreated(null);
    setPhase("idle");
    // Keep map location so citizens can submit another nearby report quickly.
  };

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setSubmitError(null);
    setPhase("validating");

    const errors: Record<string, string> = {};
    if (titleLen < REPORT_TITLE_MIN || titleLen > REPORT_TITLE_MAX) {
      errors.title = `Title must be ${REPORT_TITLE_MIN}–${REPORT_TITLE_MAX} characters.`;
    }
    if (
      descriptionLen < REPORT_DESCRIPTION_MIN ||
      descriptionLen > REPORT_DESCRIPTION_MAX
    ) {
      errors.description = `Description must be ${REPORT_DESCRIPTION_MIN}–${REPORT_DESCRIPTION_MAX} characters.`;
    }
    if (!location || location.origin === "demo") {
      errors.location =
        "Confirm your location — use current location or select a point on the map.";
    } else if (
      location.lat < -90 ||
      location.lat > 90 ||
      location.lng < -180 ||
      location.lng > 180
    ) {
      errors.location = "Coordinates are out of range.";
    }
    const imageError = validateImage(imageFile);
    if (imageError) errors.image = imageError;

    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors);
      setPhase("idle");
      return;
    }

    setFieldErrors({});
    setPhase("submitting");

    // Metadata-only image reference — no binary in PostgreSQL (S3 later).
    const mediaUrl = imageFile
      ? `demo://local/${encodeURIComponent(imageFile.name)}`
      : null;

    const payload = buildCitizenReportPayload({
      title,
      description,
      latitude: location!.lat,
      longitude: location!.lng,
      classification: incidentType || null,
      mediaUrl,
    });

    try {
      const report = await createReport(payload);
      setCreated(report);
      setPhase("success");
      onSubmitted?.(report);
    } catch (err) {
      setPhase("error");
      if (err instanceof ApiError) {
        setSubmitError(
          err.status >= 500
            ? "Unable to reach the weather intelligence service. Your report was not submitted."
            : err.message ||
                "Unable to reach the weather intelligence service. Your report was not submitted.",
        );
      } else {
        setSubmitError(
          "Unable to reach the weather intelligence service. Your report was not submitted.",
        );
      }
      if (process.env.NODE_ENV === "development") {
        console.warn("[ReportIncidentForm] submit failed", err);
      }
    }
  };

  if (phase === "success" && created) {
    return (
      <div
        className="rounded-xl bg-success/8 px-4 py-5 ring-1 ring-success/25 sm:px-5"
        role="status"
      >
        <div className="flex items-start gap-3">
          <CheckCircle2 className="mt-0.5 size-6 text-success" aria-hidden />
          <div className="min-w-0 flex-1">
            <p className="text-label text-success">Report received</p>
            <h3 className="mt-1 text-lg font-semibold text-foreground">
              Your report has been received.
            </h3>
            <p className="mt-2 text-sm text-muted-foreground">
              Reports may be reviewed and correlated with other observations.
            </p>

            <dl className="mt-4 grid gap-2 text-sm sm:grid-cols-2">
              <div>
                <dt className="text-xs text-muted-foreground">Report ID</dt>
                <dd className="font-mono text-foreground">
                  {toPublicReportId(created.id)}
                </dd>
              </div>
              <div>
                <dt className="text-xs text-muted-foreground">Status</dt>
                <dd className="font-semibold text-weather-secondary">NEW</dd>
              </div>
              <div>
                <dt className="text-xs text-muted-foreground">Location</dt>
                <dd className="font-mono text-foreground">
                  {formatCoord(created.latitude)}, {formatCoord(created.longitude)}
                </dd>
              </div>
              <div>
                <dt className="text-xs text-muted-foreground">Received</dt>
                <dd className="text-foreground">
                  {formatReceivedLabel(created.received_at)}
                </dd>
              </div>
            </dl>

            <div className="mt-5 flex flex-wrap gap-2">
              <Link
                href="/overview"
                className="inline-flex min-h-11 items-center justify-center rounded-lg bg-weather px-4 text-sm font-semibold text-slate-950 transition hover:bg-weather/90"
              >
                View Command Center
              </Link>
              <button
                type="button"
                onClick={resetForm}
                className="inline-flex min-h-11 items-center justify-center rounded-lg border border-white/12 bg-white/4 px-4 text-sm font-medium text-foreground transition hover:bg-white/8"
              >
                Submit another report
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <form onSubmit={onSubmit} className="space-y-5" noValidate>
      <div className="rounded-lg border border-warning/20 bg-warning/8 px-3 py-2.5 text-sm text-foreground/90">
        <p className="flex items-start gap-2">
          <ShieldAlert className="mt-0.5 size-4 shrink-0 text-warning" aria-hidden />
          <span>
            Reports are reviewed and analyzed before becoming verified
            incidents. Submitting does not create an incident automatically.
          </span>
        </p>
      </div>

      <div>
        <label htmlFor="report-title" className="text-label text-foreground">
          Title <span className="text-critical">*</span>
        </label>
        <input
          id="report-title"
          name="title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          maxLength={REPORT_TITLE_MAX}
          className="mt-1.5 min-h-11 w-full rounded-lg border border-white/10 bg-white/4 px-3 text-sm text-foreground outline-none ring-weather/30 placeholder:text-muted-foreground focus:ring-2"
          placeholder="Brief headline of what you observed"
          autoComplete="off"
        />
        <div className="mt-1 flex justify-between text-[11px] text-muted-foreground">
          <span>{fieldErrors.title ?? " "}</span>
          <span className={cn(titleLen > REPORT_TITLE_MAX && "text-critical")}>
            {titleLen}/{REPORT_TITLE_MAX}
          </span>
        </div>
      </div>

      <div>
        <label
          htmlFor="report-description"
          className="text-label text-foreground"
        >
          Description <span className="text-critical">*</span>
        </label>
        <textarea
          id="report-description"
          name="description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          maxLength={REPORT_DESCRIPTION_MAX}
          rows={5}
          className="mt-1.5 w-full resize-y rounded-lg border border-white/10 bg-white/4 px-3 py-2.5 text-sm text-foreground outline-none ring-weather/30 placeholder:text-muted-foreground focus:ring-2"
          placeholder="Describe what you observed. For example: water has reached the road and vehicles are having difficulty passing."
        />
        <div className="mt-1 flex justify-between text-[11px] text-muted-foreground">
          <span className="text-critical">{fieldErrors.description ?? " "}</span>
          <span
            className={cn(
              descriptionLen > REPORT_DESCRIPTION_MAX && "text-critical",
            )}
          >
            {descriptionLen}/{REPORT_DESCRIPTION_MAX}
          </span>
        </div>
      </div>

      <div>
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <label htmlFor="report-type" className="text-label text-foreground">
            Incident type{" "}
            <span className="font-normal text-muted-foreground">(optional)</span>
          </label>
          <span className="text-[10px] font-semibold tracking-[0.12em] text-muted-foreground">
            CITIZEN SELECTED
          </span>
        </div>
        <select
          id="report-type"
          name="incidentType"
          value={incidentType}
          onChange={(e) =>
            setIncidentType(e.target.value as CitizenIncidentType | "")
          }
          className="mt-1.5 min-h-11 w-full rounded-lg border border-white/10 bg-[#0B1624] px-3 text-sm text-foreground outline-none ring-weather/30 focus:ring-2"
        >
          <option value="">Select a category</option>
          {CITIZEN_INCIDENT_TYPES.map((type) => (
            <option key={type} value={type}>
              {type}
            </option>
          ))}
        </select>
        <p className="mt-1 text-[11px] text-muted-foreground">
          Your selection is a label only — not AI classification.
        </p>
      </div>

      <div>
        <p className="text-label text-foreground">
          Location <span className="text-critical">*</span>
        </p>
        <p className="mt-1 text-xs text-muted-foreground">
          Location is required for weather intelligence. We do not collect your
          name, phone, or email.
        </p>
        <div className="mt-2">
          <ReportLocationPicker value={location} onChange={setLocation} />
        </div>
        {fieldErrors.location ? (
          <p className="mt-1 text-xs text-critical">{fieldErrors.location}</p>
        ) : null}
      </div>

      <div>
        <label htmlFor="report-image" className="text-label text-foreground">
          Image{" "}
          <span className="font-normal text-muted-foreground">(optional)</span>
        </label>
        <label
          htmlFor="report-image"
          className="mt-1.5 flex min-h-11 cursor-pointer items-center gap-2 rounded-lg border border-dashed border-white/15 bg-white/3 px-3 py-2.5 text-sm text-muted-foreground transition hover:bg-white/5"
        >
          <ImagePlus className="size-4 text-weather-secondary" aria-hidden />
          <span className="truncate">
            {imageFile
              ? `${imageFile.name} (${Math.round(imageFile.size / 1024)} KB)`
              : "Add JPG, PNG, or WEBP · max 5 MB"}
          </span>
        </label>
        <input
          id="report-image"
          name="image"
          type="file"
          accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp"
          className="sr-only"
          onChange={(e) => {
            const file = e.target.files?.[0] ?? null;
            setImageFile(file);
          }}
        />
        <p className="mt-1 text-[11px] text-muted-foreground">
          Image metadata only for this phase — object storage (S3) comes later.
          Binary files are not stored in the database.
        </p>
        {fieldErrors.image ? (
          <p className="mt-1 text-xs text-critical">{fieldErrors.image}</p>
        ) : null}
      </div>

      {(phase === "error" || submitError) && (
        <div
          className="flex items-start gap-2 rounded-lg border border-critical/30 bg-critical/10 px-3 py-2.5 text-sm text-foreground"
          role="alert"
        >
          <AlertTriangle className="mt-0.5 size-4 shrink-0 text-critical" />
          <div className="min-w-0 flex-1">
            <p>{submitError}</p>
            <button
              type="button"
              className="mt-2 text-sm font-semibold text-weather-secondary underline-offset-2 hover:underline"
              onClick={() => {
                setPhase("idle");
                setSubmitError(null);
              }}
            >
              Retry
            </button>
          </div>
        </div>
      )}

      <button
        type="submit"
        disabled={phase === "validating" || phase === "submitting"}
        className="inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-xl bg-weather px-4 text-sm font-semibold text-slate-950 transition hover:bg-weather/90 disabled:opacity-70 sm:w-auto sm:min-w-[12rem]"
      >
        {phase === "submitting" || phase === "validating" ? (
          <Loader2 className="size-4 animate-spin" aria-hidden />
        ) : (
          <Send className="size-4" aria-hidden />
        )}
        {statusLabel}
      </button>
    </form>
  );
}
