import type { Metadata } from "next";

import { LiveMapWorkspace } from "@/components/incidents/live-map-workspace";

export const metadata: Metadata = {
  title: "Live Map",
  description: "Live map of correlated weather incidents.",
};

export default function LiveMapPage() {
  return <LiveMapWorkspace />;
}
