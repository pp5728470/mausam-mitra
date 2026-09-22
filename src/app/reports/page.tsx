import type { Metadata } from "next";

import { ReportsWorkspace } from "@/components/reports/reports-workspace";

export const metadata: Metadata = {
  title: "Reports",
  description:
    "Submit anonymous citizen weather signals. Reports are raw observations — not verified incidents.",
};

export default function ReportsPage() {
  return <ReportsWorkspace />;
}
