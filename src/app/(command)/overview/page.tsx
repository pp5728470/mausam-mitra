import type { Metadata } from "next";

import { CommandCenter } from "@/components/command-center/command-center";

export const metadata: Metadata = {
  title: "Overview",
  description:
    "National Weather Intelligence Command Center — simulated operating picture for Mausam Mitra.",
};

export default function OverviewPage() {
  return <CommandCenter />;
}
