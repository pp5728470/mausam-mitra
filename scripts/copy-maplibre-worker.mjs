import { copyFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

/**
 * MapLibre GL JS v6 workers import a sibling shared chunk by relative path.
 * Next.js / Turbopack does not emit that sibling next to the hashed worker,
 * so the map mounts but never paints tiles. Serve both files from /public.
 */
const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const dist = join(root, "node_modules", "maplibre-gl", "dist");
const outDir = join(root, "public", "maplibre");

mkdirSync(outDir, { recursive: true });

for (const file of [
  "maplibre-gl-worker.mjs",
  "maplibre-gl-shared.mjs",
]) {
  copyFileSync(join(dist, file), join(outDir, file));
}

console.log("Copied MapLibre worker assets to public/maplibre/");
