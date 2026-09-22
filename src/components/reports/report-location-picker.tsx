"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  Map as MapLibreMap,
  Marker,
  NavigationControl,
} from "maplibre-gl";
import type {
  Map as MapLibreMapType,
  Marker as MarkerType,
  StyleSpecification,
} from "maplibre-gl";
import { Crosshair, LocateFixed, MapPin } from "lucide-react";
import "maplibre-gl/dist/maplibre-gl.css";

import { formatCoord } from "@/lib/api/adapters/reports";
import { DEMO_MAP_CENTER } from "@/lib/reports/constants";
import { ensureMaplibreWorker } from "@/lib/map/ensure-maplibre-worker";
import { INDIA_CITY_LABELS, INDIA_OUTLINE } from "@/lib/mock/india-geo";
import { cn } from "@/lib/utils";

import "@/styles/map.css";

export type PickedLocation = {
  lat: number;
  lng: number;
  origin: "geolocation" | "map" | "demo";
};

type ReportLocationPickerProps = {
  value: PickedLocation | null;
  onChange: (location: PickedLocation) => void;
  className?: string;
};

const REMOTE_STYLES = [
  "https://tiles.openfreemap.org/styles/dark",
  "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
] as const;

const LOCAL_DARK_STYLE: StyleSpecification = {
  version: 8,
  name: "Mausam Mitra Report Picker Fallback",
  glyphs: "https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf",
  sources: {
    "india-outline": { type: "geojson", data: INDIA_OUTLINE },
    "india-cities": { type: "geojson", data: INDIA_CITY_LABELS },
  },
  layers: [
    {
      id: "background",
      type: "background",
      paint: { "background-color": "#07111F" },
    },
    {
      id: "india-fill",
      type: "fill",
      source: "india-outline",
      paint: { "fill-color": "#122C44", "fill-opacity": 0.92 },
    },
    {
      id: "india-line",
      type: "line",
      source: "india-outline",
      paint: {
        "line-color": "#38BDF8",
        "line-opacity": 0.55,
        "line-width": 1.4,
      },
    },
  ],
};

async function resolveStyle(): Promise<string | StyleSpecification> {
  for (const url of REMOTE_STYLES) {
    try {
      const res = await fetch(url, { method: "HEAD", mode: "cors" });
      if (res.ok) return url;
    } catch {
      // try next
    }
  }
  return LOCAL_DARK_STYLE;
}

export function ReportLocationPicker({
  value,
  onChange,
  className,
}: ReportLocationPickerProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<MapLibreMapType | null>(null);
  const markerRef = useRef<MarkerType | null>(null);
  const onChangeRef = useRef(onChange);
  const [mapReady, setMapReady] = useState(false);
  const [mapError, setMapError] = useState<string | null>(null);
  const [geoBusy, setGeoBusy] = useState(false);
  const [geoMessage, setGeoMessage] = useState<string | null>(null);

  useEffect(() => {
    onChangeRef.current = onChange;
  }, [onChange]);

  const placeMarker = useCallback(
    (map: MapLibreMapType, lat: number, lng: number, origin: PickedLocation["origin"]) => {
      if (markerRef.current) {
        markerRef.current.setLngLat([lng, lat]);
      } else {
        const marker = new Marker({
          color: "#0EA5E9",
          draggable: true,
        })
          .setLngLat([lng, lat])
          .addTo(map);

        marker.on("dragend", () => {
          const pos = marker.getLngLat();
          onChangeRef.current({
            lat: pos.lat,
            lng: pos.lng,
            origin: "map",
          });
        });
        markerRef.current = marker;
      }
      onChangeRef.current({ lat, lng, origin });
    },
    [],
  );

  useEffect(() => {
    let cancelled = false;
    let map: MapLibreMapType | null = null;

    const boot = async () => {
      if (!containerRef.current) return;
      ensureMaplibreWorker();
      try {
        const style = await resolveStyle();
        if (cancelled || !containerRef.current) return;

        map = new MapLibreMap({
          container: containerRef.current,
          style,
          center: [DEMO_MAP_CENTER.lng, DEMO_MAP_CENTER.lat],
          zoom: 11,
          attributionControl: { compact: true },
        });
        map.addControl(new NavigationControl({ visualizePitch: false }), "top-right");
        mapRef.current = map;

        map.on("load", () => {
          if (cancelled || !map) return;
          map.resize();
          setMapReady(true);

          // Seed demo pin until the user confirms / moves it.
          placeMarker(
            map,
            DEMO_MAP_CENTER.lat,
            DEMO_MAP_CENTER.lng,
            "demo",
          );

          map.on("click", (event) => {
            placeMarker(map!, event.lngLat.lat, event.lngLat.lng, "map");
          });
        });
      } catch {
        if (!cancelled) {
          setMapError("Map could not initialize. Enter coordinates below or retry.");
        }
      }
    };

    void boot();

    return () => {
      cancelled = true;
      markerRef.current?.remove();
      markerRef.current = null;
      map?.remove();
      mapRef.current = null;
    };
  }, [placeMarker]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady || !value) return;
    markerRef.current?.setLngLat([value.lng, value.lat]);
  }, [value, mapReady]);

  const useCurrentLocation = () => {
    if (!navigator.geolocation) {
      setGeoMessage("Geolocation is not available in this browser.");
      return;
    }
    setGeoBusy(true);
    setGeoMessage(null);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setGeoBusy(false);
        const lat = pos.coords.latitude;
        const lng = pos.coords.longitude;
        const map = mapRef.current;
        if (map) {
          map.flyTo({ center: [lng, lat], zoom: 14 });
          placeMarker(map, lat, lng, "geolocation");
        } else {
          onChange({ lat, lng, origin: "geolocation" });
        }
      },
      () => {
        setGeoBusy(false);
        setGeoMessage(
          "Location permission denied. Select a point on the map instead.",
        );
      },
      { enableHighAccuracy: true, timeout: 12_000, maximumAge: 60_000 },
    );
  };

  const confirmed = value && value.origin !== "demo";

  return (
    <div className={cn("space-y-3", className)}>
      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={useCurrentLocation}
          disabled={geoBusy}
          className="inline-flex min-h-11 items-center gap-2 rounded-lg bg-weather/15 px-3.5 py-2 text-sm font-medium text-weather-secondary ring-1 ring-weather/25 transition hover:bg-weather/25 disabled:opacity-60"
        >
          <LocateFixed className="size-4" aria-hidden />
          {geoBusy ? "Locating…" : "Use current location"}
        </button>
        <span className="inline-flex items-center gap-1.5 text-xs text-muted-foreground">
          <Crosshair className="size-3.5" aria-hidden />
          Or tap / drag the map pin
        </span>
      </div>

      {geoMessage ? (
        <p className="text-xs text-warning" role="status">
          {geoMessage}
        </p>
      ) : null}

      <div className="relative overflow-hidden rounded-xl ring-1 ring-white/10">
        <div
          ref={containerRef}
          className="mm-map-container h-56 w-full sm:h-64"
          aria-label="Report location map"
        />
        {mapError ? (
          <div className="absolute inset-0 flex items-center justify-center bg-background/80 p-4 text-center text-sm text-muted-foreground">
            {mapError}
          </div>
        ) : null}
      </div>

      <div className="rounded-lg bg-white/3 px-3 py-2.5 ring-1 ring-white/8">
        <div className="flex items-start gap-2">
          <MapPin
            className={cn(
              "mt-0.5 size-4 shrink-0",
              confirmed ? "text-success" : "text-warning",
            )}
            aria-hidden
          />
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium text-foreground">
              {confirmed ? "Location captured" : "Demo location — select your location"}
            </p>
            {value ? (
              <p className="mt-1 font-mono text-[11px] text-muted-foreground">
                Lat {formatCoord(value.lat)} · Lng {formatCoord(value.lng)}
              </p>
            ) : (
              <p className="mt-1 text-xs text-muted-foreground">
                No coordinates yet
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
