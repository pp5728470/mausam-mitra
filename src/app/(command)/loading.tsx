import { Skeleton } from "@/components/ui/skeleton";

export default function CommandLoading() {
  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-6">
      <div className="flex items-start gap-3">
        <Skeleton className="size-10 rounded-xl bg-white/5" />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-3 w-24 bg-white/5" />
          <Skeleton className="h-6 w-40 bg-white/5" />
          <Skeleton className="h-4 w-full max-w-md bg-white/5" />
        </div>
      </div>
      <Skeleton className="h-64 rounded-xl bg-white/5" />
    </div>
  );
}
