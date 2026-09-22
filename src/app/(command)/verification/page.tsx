import type { Metadata } from "next";

import { VerificationCenter } from "@/components/verification/verification-center";

export const metadata: Metadata = {
  title: "Verification",
  description:
    "Review weather signals with explainable evidence. Final verification is a human decision.",
};

export default function VerificationPage() {
  return <VerificationCenter />;
}
