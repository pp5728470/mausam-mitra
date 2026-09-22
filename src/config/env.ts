export const env = {
  apiBaseUrl:
    process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000",
  wsUrl: process.env.NEXT_PUBLIC_WS_URL ?? "ws://127.0.0.1:8000/ws",
} as const;
