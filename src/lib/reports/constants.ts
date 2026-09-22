/** Citizen-selected weather categories — NOT AI classification. */
export const CITIZEN_INCIDENT_TYPES = [
  "Heavy Rainfall",
  "Flood / Waterlogging",
  "Storm / Strong Winds",
  "Lightning",
  "Extreme Heat",
  "Hailstorm",
  "Landslide",
  "Visibility / Dense Fog",
  "Other",
] as const;

export type CitizenIncidentType = (typeof CITIZEN_INCIDENT_TYPES)[number];

export const REPORT_TITLE_MIN = 5;
export const REPORT_TITLE_MAX = 120;
export const REPORT_DESCRIPTION_MIN = 10;
export const REPORT_DESCRIPTION_MAX = 1000;

export const REPORT_IMAGE_MAX_BYTES = 5 * 1024 * 1024;
export const REPORT_IMAGE_ACCEPT = [
  "image/jpeg",
  "image/jpg",
  "image/png",
  "image/webp",
] as const;

/** Neutral demo map center (Pune) when geolocation is unavailable. */
export const DEMO_MAP_CENTER = {
  lat: 18.5204,
  lng: 73.8567,
} as const;

export const CITIZEN_SOURCE_NAME = "Citizen Report";
