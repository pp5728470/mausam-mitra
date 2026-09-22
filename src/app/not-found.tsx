import Link from "next/link";

import { BrandMark } from "@/components/shared/brand-mark";
import { WeatherAtmosphere } from "@/components/shared/weather-atmosphere";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="relative flex min-h-svh items-center justify-center overflow-x-hidden px-6">
      <WeatherAtmosphere />
      <div className="relative z-10 max-w-md text-center">
        <div className="mb-8 flex justify-center">
          <BrandMark />
        </div>
        <p className="text-label">Not found</p>
        <h1 className="text-page-title mt-3">This route is not on the grid</h1>
        <p className="text-body mt-3 text-muted-foreground">
          The requested view is outside the current command-center map.
        </p>
        <Button asChild className="mt-8" size="lg">
          <Link href="/">Return to Mausam Mitra</Link>
        </Button>
      </div>
    </div>
  );
}
