import { cn } from "@/lib/utils";

type WeatherAtmosphereProps = {
  className?: string;
  withRadar?: boolean;
};

export function WeatherAtmosphere({
  className,
  withRadar = false,
}: WeatherAtmosphereProps) {
  return (
    <div
      aria-hidden
      className={cn("atmosphere-root pointer-events-none absolute inset-0 overflow-hidden", className)}
    >
      <div className="atmosphere-orb atmosphere-orb-a" />
      <div className="atmosphere-orb atmosphere-orb-b" />
      <div className="atmosphere-orb atmosphere-orb-c" />
      {withRadar ? <div className="radar-sweep" /> : null}
      <div className="atmosphere-grain" />
    </div>
  );
}
