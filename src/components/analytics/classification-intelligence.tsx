import type { AnalyticsOverview } from "@/lib/api/analytics";

interface ClassificationProps {
  overview: AnalyticsOverview;
}

export function ClassificationIntelligence({ overview }: ClassificationProps) {
  const total = overview.classified_reports + overview.unclassified_reports;
  const classifiedPct = total > 0 ? (overview.classified_reports / total) * 100 : 0;

  return (
    <div className="flex flex-col gap-4">
      <div className="flex justify-between items-center text-sm">
        <span className="text-muted-foreground">AI Classified</span>
        <span className="font-medium">{overview.classified_reports}</span>
      </div>
      
      <div className="h-2 w-full rounded-full bg-white/10 overflow-hidden">
        <div 
          className="h-full bg-indigo-500" 
          style={{ width: `${classifiedPct}%` }}
        />
      </div>

      <div className="mt-4 p-4 rounded-xl bg-indigo-500/10 border border-indigo-500/20">
        <p className="text-xs font-medium text-indigo-400 uppercase tracking-wider mb-2">
          Language Confidence
        </p>
        <div className="flex items-baseline gap-2">
          <span className="text-3xl font-semibold text-indigo-300">
            {overview.average_classifier_confidence 
              ? (overview.average_classifier_confidence * 100).toFixed(1) 
              : "--"}%
          </span>
          <span className="text-xs text-indigo-400/80">
            avg match strength
          </span>
        </div>
        <p className="mt-3 text-xs text-indigo-300/60 leading-relaxed">
          * This metric represents how strongly the report text matches the assigned category. It does NOT indicate truth, authenticity, or model accuracy.
        </p>
      </div>
    </div>
  );
}
