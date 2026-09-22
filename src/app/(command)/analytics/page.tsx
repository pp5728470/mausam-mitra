import type { Metadata } from "next";

import { AnalyticsWorkspace } from "@/components/analytics/analytics-workspace";

export const metadata: Metadata = {
  title: "Analytics - Command Center",
};

export default function AnalyticsPage() {
  return <AnalyticsWorkspace />;
}
