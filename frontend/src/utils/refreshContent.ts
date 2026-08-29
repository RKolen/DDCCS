/**
 * Push newly written Drupal content into the running dev server.
 *
 * `gatsby develop` sources Drupal once at bootstrap, so a node created through
 * a console mutation is invisible to every static query until the data layer
 * re-sources. `ENABLE_GATSBY_REFRESH_ENDPOINT=true` (set by the develop script)
 * exposes `/__refresh` for exactly that, and `gatsby-config.ts` describes it as
 * the immediate push, with `refetchInterval` only as a fallback poll. Telling
 * an operator to rebuild the frontend is never the answer.
 *
 * A production build has no `/__refresh`, so a failure here is expected and
 * ignored: the content is already saved either way.
 */

/**
 * Ask the dev server to re-source Drupal, then hand back control.
 *
 * @returns True when the dev server accepted the refresh.
 */
export async function refreshContent(): Promise<boolean> {
  try {
    const res = await fetch('/__refresh', { method: 'POST' });
    return res.ok;
  } catch {
    return false;
  }
}

/**
 * Re-source Drupal and reload, so static queries show the new content.
 *
 * The reload is what the existing console screens do after a mutation; the
 * refresh before it is what makes the reload actually show something new.
 *
 * @param delayMs How long to let the re-source settle before reloading.
 */
export async function refreshAndReload(delayMs = 1500): Promise<void> {
  await refreshContent();
  window.setTimeout(() => { window.location.reload(); }, delayMs);
}
