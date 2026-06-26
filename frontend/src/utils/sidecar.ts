/**
 * Resolve the Python sidecar base URL from the environment.
 *
 * Host and port are configuration and must come from SIDECAR_HOST /
 * SIDECAR_PORT (set authoritatively in the root .env) — there are no
 * hardcoded fallbacks. Returns null when either is missing so callers can
 * fail loudly instead of silently targeting a wrong address.
 */
export function sidecarBaseUrl(): string | null {
  const host = process.env.SIDECAR_HOST;
  const port = process.env.SIDECAR_PORT;
  if (!host || !port) return null;
  return `http://${host}:${port}`;
}
