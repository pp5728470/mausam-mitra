import type { ReactNode } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { AuthGuard } from "@/components/layout/AuthGuard";

export default function CommandLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <AuthGuard>
      <AppShell>{children}</AppShell>
    </AuthGuard>
  );
}
