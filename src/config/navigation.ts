import type { LucideIcon } from "lucide-react";
import {
  Activity,
  BadgeCheck,
  ClipboardList,
  CloudLightning,
  Map,
  Radar,
} from "lucide-react";

import { Role } from "@/contexts/AuthContext";

export const APP_ROUTES = [
  "/overview",
  "/live-map",
  "/incidents",
  "/verification",
  "/reports",
  "/analytics",
] as const;

export type AppRoute = (typeof APP_ROUTES)[number];

export type NavItem = {
  href: AppRoute;
  label: string;
  description: string;
  icon: LucideIcon;
  phaseNote: string;
  allowedRoles: Role[];
};

export const NAV_ITEMS: readonly NavItem[] = [
  {
    href: "/overview",
    label: "Overview",
    description: "National operating picture and command-center health.",
    icon: Radar,
    phaseNote:
      "This workspace will host the live operating picture once weather, incident, and GIS services are connected.",
    allowedRoles: ["VERIFIER", "ANALYST", "ADMIN"],
  },
  {
    href: "/live-map",
    label: "Live Map",
    description: "Geospatial intelligence and incident overlay.",
    icon: Map,
    phaseNote:
      "The map canvas is reserved for PostGIS layers, live incident pins, and radar overlays in a later phase.",
    allowedRoles: ["VERIFIER", "ANALYST", "ADMIN"],
  },
  {
    href: "/incidents",
    label: "Incidents",
    description: "Correlated weather incidents and severity tracking.",
    icon: CloudLightning,
    phaseNote:
      "Incident records will appear here after multi-source signals are normalized, verified, and correlated.",
    allowedRoles: ["VERIFIER", "ANALYST", "ADMIN"],
  },
  {
    href: "/verification",
    label: "Verification",
    description: "Evidence review and human signal confirmation.",
    icon: BadgeCheck,
    phaseNote:
      "Evidence scores assist review. Final verification remains a human decision and does not create incidents.",
    allowedRoles: ["VERIFIER", "ANALYST", "ADMIN"],
  },
  {
    href: "/reports",
    label: "Reports",
    description: "Citizen weather signals and source intake.",
    icon: ClipboardList,
    phaseNote:
      "Citizen reports are raw signals. They are reviewed before any incident correlation.",
    allowedRoles: ["VERIFIER", "ANALYST", "ADMIN"],
  },
  {
    href: "/analytics",
    label: "Analytics",
    description: "Severity trends and disaster-management intelligence.",
    icon: Activity,
    phaseNote:
      "Trend models and severity analytics will land here after the AI/ML services are wired in.",
    allowedRoles: ["ANALYST", "ADMIN"],
  },
];

export function getNavItem(href: string): NavItem | undefined {
  return NAV_ITEMS.find((item) => item.href === href);
}
