const DRUPAL_BASE_URL = process.env.GATSBY_DRUPAL_BASE_URL?.replace(/\/$/, '') ?? '';

export function drupalAdminUrl(path: string): string {
  if (!DRUPAL_BASE_URL) {
    return '#';
  }

  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${DRUPAL_BASE_URL}${normalizedPath}`;
}
