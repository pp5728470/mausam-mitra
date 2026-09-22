"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { Loader2 } from "lucide-react";
import { hasRouteAccess } from "@/lib/auth/roles";
import { AccessDenied } from "@/components/shared/AccessDenied";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { user, isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    return null;
  }

  if (!hasRouteAccess(user.role, pathname)) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <AccessDenied />
      </div>
    );
  }

  return <>{children}</>;
}
