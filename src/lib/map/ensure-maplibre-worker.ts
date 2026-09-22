import { setWorkerUrl } from "maplibre-gl";

/**
 * MapLibre v6 workers import a sibling shared chunk. Next/Turbopack breaks that
 * resolution, so we serve both files from /public/maplibre (see scripts/).
 * Must run before the first Map() construction.
 */
let maplibreWorkerConfigured = false;

export function ensureMaplibreWorker(): void {
  if (maplibreWorkerConfigured || typeof window === "undefined") return;
  setWorkerUrl(`${window.location.origin}/maplibre/maplibre-gl-worker.mjs`);
  maplibreWorkerConfigured = true;
}
