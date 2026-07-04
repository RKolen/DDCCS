import { fetch as undiciFetch, Agent } from 'undici';

/**
 * Fetch helper for long-running sidecar calls (server-side only).
 *
 * A chunked arc analysis of a large story can take many minutes. Node's global
 * fetch (undici) caps a request at ~300s (`headersTimeout`), which drops the
 * connection mid-analysis and surfaces as "fetch failed". This uses undici's
 * own `fetch` with a dedicated dispatcher whose timeouts are disabled so these
 * calls run to completion. (The Agent must come from the same undici instance
 * as this `fetch` — Node's global fetch rejects a foreign dispatcher.)
 */
const noTimeoutDispatcher = new Agent({ headersTimeout: 0, bodyTimeout: 0 });

/** POST/GET the sidecar with no request timeout. */
export function sidecarFetch(
  url: string,
  init: Parameters<typeof undiciFetch>[1],
): ReturnType<typeof undiciFetch> {
  return undiciFetch(url, { ...init, dispatcher: noTimeoutDispatcher });
}
