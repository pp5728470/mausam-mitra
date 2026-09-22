import { Role } from "@/contexts/AuthContext";

export const PUBLIC_ROUTES = [
  "/",
  "/reports",
  "/login",
];

export const PROTECTED_ROUTES = [
  "/overview",
  "/live-map",
  "/incidents",
  "/verification",
  "/analytics",
  "/admin",
];

export const ROLE_ACCESS: Record<Role, string[]> = {
  CITIZEN: [], // CITIZEN has no access to operational modules
  VERIFIER: [
    "/overview",
    "/live-map",
    "/incidents",
    "/verification",
  ],
  ANALYST: [
    "/overview",
    "/live-map",
    "/incidents",
    "/verification",
    "/analytics",
  ],
  ADMIN: [
    "/overview",
    "/live-map",
    "/incidents",
    "/verification",
    "/analytics",
    "/admin",
  ],
};

/**
 * Checks if a user role has access to a specific path.
 * Paths like /incidents/123 will be checked against /incidents.
 */
export function hasRouteAccess(role: Role, pathname: string): boolean {
  // If it's a public route, everyone has access. Exact match for /
  if (pathname === "/") return true;
  if (PUBLIC_ROUTES.some((route) => route !== "/" && (pathname === route || pathname.startsWith(route + "/")))) {
    return true;
  }

  // Find the base protected route
  const allowedRoutes = ROLE_ACCESS[role];
  return allowedRoutes.some((route) => pathname === route || pathname.startsWith(route + "/"));
}
