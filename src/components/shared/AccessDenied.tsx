import { ShieldAlert, ArrowRight } from "lucide-react";
import Link from "next/link";

export function AccessDenied() {
  return (
    <div className="flex flex-col items-center justify-center p-6 text-center">
      <div className="mb-4 rounded-full bg-critical/10 p-4 ring-1 ring-critical/20">
        <ShieldAlert className="size-10 text-critical" />
      </div>
      <h1 className="mb-2 text-2xl font-bold tracking-tight text-foreground">
        ACCESS RESTRICTED
      </h1>
      <p className="mb-8 max-w-sm text-sm text-muted-foreground">
        You do not have permission to access this operational module.
      </p>
      <Link
        href="/overview"
        className="inline-flex items-center justify-center gap-2 rounded-md bg-white/10 px-6 py-2.5 text-sm font-medium text-foreground transition-colors hover:bg-white/15"
      >
        Return to Command Center
        <ArrowRight className="size-4" />
      </Link>
    </div>
  );
}
