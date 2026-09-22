import type { Metadata } from "next";

import { IncidentIntelligence } from "@/components/incidents/incident-intelligence";

export const metadata: Metadata = {
  title: "Incidents",
  description:
    "Correlated weather incident intelligence. Correlation strength is not a truth claim.",
};

export default function IncidentsPage() {
  return <IncidentIntelligence />;
}
