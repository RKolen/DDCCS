/**
 * Resolve this site's own origin, for a server-side call to a sibling API route.
 *
 * A queued job runs with no browser, so a function that orchestrates other
 * functions (the arc runner) cannot use relative URLs. Host and port are
 * configuration and must come from GATSBY_HOST / GATSBY_PORT (set
 * authoritatively in the root .env) - there are no hardcoded fallbacks.
 * Returns null when either is missing so callers fail loudly.
 */
export function selfBaseUrl(): string | null {
  const host = process.env.GATSBY_HOST;
  const port = process.env.GATSBY_PORT;
  if (!host || !port) return null;
  return `http://${host}:${port}`;
}
