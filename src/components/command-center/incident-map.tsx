"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Map as MapLibreMap,
  NavigationControl,
  setWorkerUrl,
} from "maplibre-gl";
import type {
  GeoJSONSource as GeoJSONSourceType,
  Map as MapLibreMapType,
  MapLayerMouseEvent,
  StyleSpecification,
} from "maplibre-gl";
import type { FeatureCollection } from "geojson";
import "maplibre-gl/dist/maplibre-gl.css";

import {
  IncidentPreview,
  IncidentPreviewCard,
} from "@/components/command-center/incident-preview";
import {
  MapControls,
  type MapControlsState,
} from "@/components/command-center/map-controls";
import { MapLegend } from "@/components/command-center/map-legend";
import { CommandErrorState } from "@/components/command-center/data-states";
import { filterIncidents, SEVERITY_COLORS } from "@/lib/incidents/utils";
import { INDIA_CITY_LABELS, INDIA_OUTLINE } from "@/lib/mock/india-geo";
import { cn } from "@/lib/utils";
import type { Incident } from "@/types/incident";

import "@/styles/map.css";

/**
 * MapLibre v6 workers import a sibling shared chunk. Next/Turbopack breaks that
 * resolution, so we serve both files from /public/maplibre (see scripts/).
 * Must run before the first Map() construction.
 */
let maplibreWorkerConfigured = false;
function ensureMaplibreWorker() {
  if (maplibreWorkerConfigured || typeof window === "undefined") return;
  setWorkerUrl(`${window.location.origin}/maplibre/maplibre-gl-worker.mjs`);
  maplibreWorkerConfigured = true;
}

const INDIA_CENTER: [number, number] = [79.0, 22.5];
const INITIAL_ZOOM = 4.7;

/**
 * Remote dark styles — probed before use.
 * OpenFreeMap first; Carto Dark Matter as secondary.
 */
const REMOTE_STYLES = [
  "https://tiles.openfreemap.org/styles/dark",
  "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
] as const;

const LOCAL_DARK_STYLE: StyleSpecification = {
  version: 8,
  name: "Mausam Mitra India Fallback",
  glyphs: "https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf",
  sources: {
    "india-outline": {
      type: "geojson",
      data: INDIA_OUTLINE,
    },
    "india-cities": {
      type: "geojson",
      data: INDIA_CITY_LABELS,
    },
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
      paint: {
        "fill-color": "#122C44",
        "fill-opacity": 0.92,
      },
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
    {
      id: "india-glow",
      type: "line",
      source: "india-outline",
      paint: {
        "line-color": "#0EA5E9",
        "line-opacity": 0.18,
        "line-width": 6,
        "line-blur": 4,
      },
    },
    {
      id: "india-city-dots",
      type: "circle",
      source: "india-cities",
      paint: {
        "circle-radius": 2.2,
        "circle-color": "#93A4B8",
        "circle-opacity": 0.8,
      },
    },
    {
      id: "india-city-labels",
      type: "symbol",
      source: "india-cities",
      layout: {
        "text-field": ["get", "name"],
        "text-size": 11,
        "text-offset": [0, 1.1],
        "text-anchor": "top",
        "text-font": ["Open Sans Regular", "Arial Unicode MS Regular"],
      },
      paint: {
        "text-color": "#93A4B8",
        "text-halo-color": "#07111F",
        "text-halo-width": 1.2,
      },
    },
  ],
};

const SOURCE_ID = "mm-incidents";
const LAYER_PULSE = "mm-incidents-pulse";
const LAYER_CORE = "mm-incidents-core";
const LAYER_SELECTED = "mm-incidents-selected";
const LAYER_HEAT = "mm-weather-heat";

const DEFAULT_CONTROLS: MapControlsState = {
  layers: {
    incidents: true,
    weather: false,
    reports: false,
    verified: true,
    emerging: true,
  },
  severity: "all",
};

type IncidentMapProps = {
  incidents: Incident[];
  selectedId: string | null;
  onSelect: (id: string | null) => void;
  className?: string;
};

function toFeatureCollection(list: Incident[]): FeatureCollection {
  return {
    type: "FeatureCollection",
    features: list.map((incident) => ({
      type: "Feature",
      id: incident.id,
      properties: {
        id: incident.id,
        title: incident.title,
        severity: incident.severity,
        status: incident.status,
        color: SEVERITY_COLORS[incident.severity],
        pulse:
          incident.status === "emerging" ||
          incident.status === "active" ||
          incident.status === "detected"
            ? 1
            : 0,
      },
      geometry: {
        type: "Point",
        coordinates: [incident.coordinates.lng, incident.coordinates.lat],
      },
    })),
  };
}

function ensureIncidentLayers(map: MapLibreMapType) {
  if (!map.getSource(SOURCE_ID)) {
    map.addSource(SOURCE_ID, {
      type: "geojson",
      data: { type: "FeatureCollection", features: [] },
      promoteId: "id",
    });
  }

  if (!map.getLayer(LAYER_HEAT)) {
    map.addLayer({
      id: LAYER_HEAT,
      type: "circle",
      source: SOURCE_ID,
      paint: {
        "circle-radius": 34,
        "circle-color": "#38BDF8",
        "circle-opacity": 0.08,
        "circle-blur": 0.85,
      },
      layout: { visibility: "none" },
    });
  }

  if (!map.getLayer(LAYER_PULSE)) {
    map.addLayer({
      id: LAYER_PULSE,
      type: "circle",
      source: SOURCE_ID,
      filter: ["==", ["get", "pulse"], 1],
      paint: {
        "circle-radius": 16,
        "circle-color": ["get", "color"],
        "circle-opacity": 0.22,
        "circle-blur": 0.4,
      },
    });
  }

  if (!map.getLayer(LAYER_CORE)) {
    map.addLayer({
      id: LAYER_CORE,
      type: "circle",
      source: SOURCE_ID,
      paint: {
        "circle-radius": ["interpolate", ["linear"], ["zoom"], 3, 5.5, 7, 9],
        "circle-color": ["get", "color"],
        "circle-stroke-width": 2,
        "circle-stroke-color": "#F8FAFC",
        "circle-opacity": 0.96,
      },
    });
  }

  if (!map.getLayer(LAYER_SELECTED)) {
    map.addLayer({
      id: LAYER_SELECTED,
      type: "circle",
      source: SOURCE_ID,
      filter: ["==", ["get", "id"], ""],
      paint: {
        "circle-radius": ["interpolate", ["linear"], ["zoom"], 3, 11, 7, 15],
        "circle-color": "transparent",
        "circle-stroke-width": 2.5,
        "circle-stroke-color": "#38BDF8",
        "circle-opacity": 1,
      },
    });
  }
}

async function probeStyle(url: string): Promise<boolean> {
  try {
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 3000);
    const response = await fetch(url, {
      method: "GET",
      mode: "cors",
      signal: controller.signal,
    });
    window.clearTimeout(timeout);
    if (!response.ok) return false;
    const contentType = response.headers.get("content-type") ?? "";
    if (!contentType.includes("json") && !contentType.includes("javascript")) {
      // Some CDNs omit content-type; still try parse.
      const text = await response.clone().text();
      return text.trim().startsWith("{");
    }
    return true;
  } catch {
    return false;
  }
}

async function resolveInitialStyle(): Promise<{
  style: string | StyleSpecification;
  fallback: boolean;
  label: string;
}> {
  for (const styleUrl of REMOTE_STYLES) {
    if (await probeStyle(styleUrl)) {
      return {
        style: styleUrl,
        fallback: false,
        label: styleUrl.includes("openfreemap") ? "OpenFreeMap" : "Carto Dark",
      };
    }
  }
  return {
    style: LOCAL_DARK_STYLE,
    fallback: true,
    label: "Local India outline",
  };
}

export function IncidentMap({
  incidents,
  selectedId,
  onSelect,
  className,
}: IncidentMapProps) {
  const shellRef = useRef<HTMLDivElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<MapLibreMapType | null>(null);
  const onSelectRef = useRef(onSelect);
  const visibleRef = useRef<Incident[]>([]);
  const selectedIdRef = useRef(selectedId);
  const readyHandledRef = useRef(false);

  const [controls, setControls] = useState<MapControlsState>(DEFAULT_CONTROLS);
  const [mapReady, setMapReady] = useState(false);
  const [mapError, setMapError] = useState(false);
  const [usingFallbackBasemap, setUsingFallbackBasemap] = useState(false);
  const [basemapLabel, setBasemapLabel] = useState("Resolving basemap…");
  const [previewOpen, setPreviewOpen] = useState(false);
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  useEffect(() => {
    onSelectRef.current = onSelect;
  }, [onSelect]);

  useEffect(() => {
    selectedIdRef.current = selectedId;
  }, [selectedId]);

  const visibleIncidents = useMemo(
    () =>
      filterIncidents(incidents, {
        severity: controls.severity,
        layers: {
          incidents: controls.layers.incidents,
          verified: controls.layers.verified,
          emerging: controls.layers.emerging,
        },
      }),
    [incidents, controls],
  );

  useEffect(() => {
    visibleRef.current = visibleIncidents;
  }, [visibleIncidents]);

  const selectedIncident =
    incidents.find((incident) => incident.id === selectedId) ?? null;

  const hoverIncident =
    incidents.find((incident) => incident.id === hoveredId) ?? null;

  const syncIncidentData = useCallback(
    (map: MapLibreMapType, list: Incident[], selected: string | null) => {
      const source = map.getSource(SOURCE_ID) as GeoJSONSourceType | undefined;
      if (source) {
        source.setData(toFeatureCollection(list));
      }
      if (map.getLayer(LAYER_SELECTED)) {
        map.setFilter(LAYER_SELECTED, ["==", ["get", "id"], selected ?? ""]);
      }
    },
    [],
  );

  useEffect(() => {
    const container = containerRef.current;
    const shell = shellRef.current;
    if (!container || !shell || mapRef.current) return;

    let cancelled = false;
    let pulseFrame = 0;
    let map: MapLibreMapType | null = null;
    let resizeObserver: ResizeObserver | null = null;
    let tileFailTimer: number | undefined;
    let dataEventCount = 0;
    let hasFallenBack = false;
    let listenersBound = false;

    const onClick = (event: MapLayerMouseEvent) => {
      const feature = event.features?.[0];
      const id = feature?.properties?.id;
      if (typeof id === "string") {
        onSelectRef.current(id);
        setPreviewOpen(true);
      }
    };

    const onMove = (event: MapLayerMouseEvent) => {
      const feature = event.features?.[0];
      const id = feature?.properties?.id;
      setHoveredId(typeof id === "string" ? id : null);
      if (map) map.getCanvas().style.cursor = id ? "pointer" : "";
    };

    const onLeave = () => {
      setHoveredId(null);
      if (map) map.getCanvas().style.cursor = "";
    };

    const startPulse = (activeMap: MapLibreMapType) => {
      const prefersReduced = window.matchMedia(
        "(prefers-reduced-motion: reduce)",
      ).matches;
      if (prefersReduced || !activeMap.getLayer(LAYER_PULSE)) return;

      window.cancelAnimationFrame(pulseFrame);
      const tick = (time: number) => {
        if (cancelled || !activeMap.getLayer(LAYER_PULSE)) return;
        const wave = (Math.sin(time / 750) + 1) / 2;
        activeMap.setPaintProperty(
          LAYER_PULSE,
          "circle-opacity",
          0.1 + wave * 0.2,
        );
        activeMap.setPaintProperty(LAYER_PULSE, "circle-radius", 12 + wave * 10);
        pulseFrame = window.requestAnimationFrame(tick);
      };
      pulseFrame = window.requestAnimationFrame(tick);
    };

    const applyFallbackStyle = (reason: string) => {
      if (!map || cancelled || hasFallenBack) return;
      hasFallenBack = true;
      setUsingFallbackBasemap(true);
      setBasemapLabel(`Local India outline (${reason})`);
      readyHandledRef.current = false;
      map.setStyle(LOCAL_DARK_STYLE);
    };

    const handleReady = () => {
      if (cancelled || !map || readyHandledRef.current) return;
      readyHandledRef.current = true;

      // Critical: MapLibre may have measured a zero-size box; force layout sync.
      map.resize();

      ensureIncidentLayers(map);
      syncIncidentData(map, visibleRef.current, selectedIdRef.current);

      if (!listenersBound) {
        map.on("click", LAYER_CORE, onClick);
        map.on("mousemove", LAYER_CORE, onMove);
        map.on("mouseleave", LAYER_CORE, onLeave);
        listenersBound = true;
      }

      setMapReady(true);
      startPulse(map);

      // Second resize after paint — covers late flex/grid layout.
      window.requestAnimationFrame(() => {
        if (!cancelled && map) map.resize();
      });
    };

    const mountMap = async () => {
      try {
        ensureMaplibreWorker();

        const resolved = await resolveInitialStyle();
        if (cancelled) return;

        // Wait until the shell has a real box — MapLibre skips tile requests
        // when constructed against a zero-size container.
        const readyBox = await new Promise<boolean>((resolveWait) => {
          const start = performance.now();
          const tick = () => {
            if (cancelled) {
              resolveWait(false);
              return;
            }
            if (shell.clientHeight > 40 && container.clientWidth > 40) {
              resolveWait(true);
              return;
            }
            if (performance.now() - start > 4000) {
              resolveWait(shell.clientHeight > 0);
              return;
            }
            window.requestAnimationFrame(tick);
          };
          tick();
        });
        if (cancelled || !readyBox) return;

        setUsingFallbackBasemap(resolved.fallback);
        setBasemapLabel(resolved.label);

        map = new MapLibreMap({
          container,
          style: resolved.style,
          center: INDIA_CENTER,
          zoom: INITIAL_ZOOM,
          attributionControl: { compact: true },
          // Avoid cooperative-gesture friction for the command-center hero map.
          cooperativeGestures: false,
          canvasContextAttributes: {
            preserveDrawingBuffer: true,
            antialias: false,
            powerPreference: "high-performance",
          },
        });

        mapRef.current = map;

        map.addControl(
          new NavigationControl({ visualizePitch: false, showCompass: true }),
          "bottom-right",
        );

        // style.load covers initial mount and setStyle(fallback) — avoid also
        // binding `load`, which would double-run layer setup / pulse loops.
        map.on("style.load", handleReady);

        // If remote style URL was accepted but vector tiles never arrive,
        // switch to the local India outline so the map is never a blank void.
        if (!resolved.fallback) {
          map.on("data", (event) => {
            if (event.dataType === "source") {
              dataEventCount += 1;
            }
          });

          tileFailTimer = window.setTimeout(() => {
            if (cancelled || hasFallenBack) return;
            // Very few source data events usually means tiles never streamed.
            if (dataEventCount < 2 && map) {
              applyFallbackStyle("tiles unavailable");
            }
          }, 4500);
        }

        map.on("error", (event) => {
          const message = String(event.error ?? "");
          // Ignore benign tile 404 noise after fallback is active.
          if (cancelled || !map) return;
          if (
            !resolved.fallback &&
            /tile|source|ajax|fetch|network|failed/i.test(message)
          ) {
            // Defer to the tileFailTimer / explicit fallback path.
          }
        });

        resizeObserver = new ResizeObserver(() => {
          if (map && !cancelled) {
            map.resize();
          }
        });
        resizeObserver.observe(shell);
        resizeObserver.observe(container);
      } catch {
        if (!cancelled) setMapError(true);
      }
    };

    void mountMap();

    return () => {
      cancelled = true;
      window.cancelAnimationFrame(pulseFrame);
      if (tileFailTimer) window.clearTimeout(tileFailTimer);
      resizeObserver?.disconnect();
      if (map) {
        map.off("click", LAYER_CORE, onClick);
        map.off("mousemove", LAYER_CORE, onMove);
        map.off("mouseleave", LAYER_CORE, onLeave);
        map.remove();
      }
      mapRef.current = null;
      readyHandledRef.current = false;
    };
  }, [syncIncidentData]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady) return;

    syncIncidentData(map, visibleIncidents, selectedId);

    if (map.getLayer(LAYER_HEAT)) {
      // Weather heat remains a demo affordance — not a live weather product.
      map.setLayoutProperty(LAYER_HEAT, "visibility", "none");
    }
  }, [mapReady, selectedId, syncIncidentData, visibleIncidents]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady || !selectedIncident) return;

    map.easeTo({
      center: [
        selectedIncident.coordinates.lng,
        selectedIncident.coordinates.lat,
      ],
      zoom: Math.max(map.getZoom(), 5.5),
      duration: 650,
    });
  }, [selectedIncident, mapReady]);

  const handleControlsChange = useCallback((next: MapControlsState) => {
    setControls(next);
  }, []);

  if (mapError) {
    return (
      <div className={cn("relative overflow-hidden rounded-xl", className)}>
        <CommandErrorState
          title="Interactive map unavailable"
          description="MapLibre could not initialize. Incident intelligence remains available in the side panels."
          className="min-h-[28rem]"
        />
        <div className="absolute top-3 left-3 z-10">
          <MapControls value={controls} onChange={handleControlsChange} />
        </div>
        <div className="grid gap-2 p-4 sm:grid-cols-2 lg:grid-cols-3">
          {visibleIncidents.map((incident) => (
            <button
              key={incident.id}
              type="button"
              onClick={() => {
                onSelect(incident.id);
                setPreviewOpen(true);
              }}
              className="rounded-lg bg-card/80 px-3 py-2 text-left ring-1 ring-white/8 transition-colors hover:bg-card"
            >
              <p className="text-sm font-medium text-foreground">
                {incident.title}
              </p>
              <p className="text-xs text-muted-foreground">
                {incident.locationLabel}
              </p>
            </button>
          ))}
        </div>
        <IncidentPreview
          incident={selectedIncident}
          open={previewOpen}
          onOpenChange={setPreviewOpen}
        />
      </div>
    );
  }

  return (
    <div
      ref={shellRef}
      className={cn(
        // Explicit height — do NOT use absolute-fill for the MapLibre container.
        // MapLibre CSS forces position:relative on .maplibregl-map, which collapses
        // absolute inset-0 boxes to height:0 and clips the canvas.
        "relative h-[min(58vh,560px)] min-h-[400px] overflow-hidden rounded-xl ring-1 ring-white/8 sm:h-[min(62vh,600px)] sm:min-h-[480px] xl:h-[min(64vh,620px)]",
        className,
      )}
    >
      <div
        ref={containerRef}
        className="mm-map-container h-full w-full bg-[#07111F]"
        aria-label="India incident map"
        role="application"
      />

      <div className="pointer-events-none absolute inset-0 z-[1] bg-[radial-gradient(ellipse_at_top,rgb(14_165_233_/_0.06),transparent_55%)]" />

      <div className="absolute top-3 left-3 z-10">
        <MapControls value={controls} onChange={handleControlsChange} />
      </div>

      <div className="absolute top-3 right-3 z-10 flex flex-col items-end gap-1.5">
        <div className="rounded-full border border-white/10 bg-background/80 px-2.5 py-1 text-[10px] font-semibold tracking-[0.12em] text-muted-foreground backdrop-blur-sm">
          DEMO INTELLIGENCE FEED
        </div>
        {usingFallbackBasemap ? (
          <div className="max-w-[14rem] rounded-full border border-warning/25 bg-background/85 px-2.5 py-1 text-[10px] text-warning/90 backdrop-blur-sm">
            Offline basemap · India outline
          </div>
        ) : null}
      </div>

      <div className="absolute bottom-3 left-3 z-10">
        <MapLegend />
      </div>

      <p className="pointer-events-none absolute right-3 bottom-3 z-10 rounded bg-background/70 px-1.5 py-0.5 text-[9px] tracking-wide text-muted-foreground/80 backdrop-blur-sm">
        {basemapLabel}
      </p>

      {hoverIncident && hoverIncident.id !== selectedId ? (
        <div className="pointer-events-none absolute right-3 bottom-16 z-10 hidden w-64 md:block">
          <div className="rounded-xl bg-popover/95 p-3 shadow-lg ring-1 ring-white/10 backdrop-blur-sm">
            <p className="text-[11px] font-semibold tracking-[0.12em] text-foreground uppercase">
              {hoverIncident.title}
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              {hoverIncident.locationLabel}
            </p>
          </div>
        </div>
      ) : null}

      {selectedIncident ? (
        <div className="absolute right-3 bottom-16 z-20 hidden w-72 lg:block">
          <IncidentPreviewCard
            incident={selectedIncident}
            onView={() => setPreviewOpen(true)}
          />
        </div>
      ) : null}

      <IncidentPreview
        incident={selectedIncident}
        open={previewOpen}
        onOpenChange={setPreviewOpen}
      />
    </div>
  );
}
