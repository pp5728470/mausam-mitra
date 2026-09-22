import { env } from "@/config/env";
import type { ApiErrorBody } from "@/types/api";

export class ApiError extends Error {
  readonly status: number;
  readonly path: string;
  readonly body: ApiErrorBody | null;

  constructor(
    message: string,
    status: number,
    path: string,
    body: ApiErrorBody | null = null,
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.path = path;
    this.body = body;
  }
}

type ApiRequestOptions = Omit<RequestInit, "body"> & {
  body?: unknown;
};

export async function apiRequest<T>(
  path: string,
  options: ApiRequestOptions = {},
): Promise<T> {
  const { body, headers, ...rest } = options;
  
  let token = null;
  if (typeof window !== "undefined") {
    token = localStorage.getItem("mausam_token");
  }

  const response = await fetch(`${env.apiBaseUrl}${path}`, {
    ...rest,
    headers: {
      Accept: "application/json",
      ...(body === undefined ? {} : { "Content-Type": "application/json" }),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });

  if (!response.ok) {
    let parsed: ApiErrorBody | null = null;
    try {
      parsed = (await response.json()) as ApiErrorBody;
    } catch {
      parsed = null;
    }

    throw new ApiError(
      typeof parsed?.detail === "string"
        ? parsed.detail
        : Array.isArray(parsed?.detail)
          ? "Validation failed"
          : `Request failed with status ${response.status}`,
      response.status,
      path,
      parsed,
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}
