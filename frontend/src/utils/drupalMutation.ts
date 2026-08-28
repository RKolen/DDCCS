/**
 * Drupal GraphQL transport for the `src/api/` arc endpoints: read credentials,
 * POST a mutation, unwrap `errors`.
 */

export interface DrupalCredentials {
  drupalUrl: string;
  token:     string;
}

/** Returns null when either value is missing; there is no default to fall back to. */
export function drupalCredentials(): DrupalCredentials | null {
  const drupalUrl = (
    process.env.GATSBY_DRUPAL_BASE_URL ??
    process.env.DRUPAL_BASE_URL ??
    ''
  ).replace(/\/$/, '');
  const token = process.env.DRUPAL_GRAPHQL_TOKEN ?? '';
  if (!drupalUrl || !token) {
    return null;
  }
  return { drupalUrl, token };
}

/**
 * Run one GraphQL operation and return its `data`.
 *
 * Throws with the first GraphQL error message verbatim — the arc mutations
 * raise readable UserErrors ("Story arc not found.") worth showing as-is.
 */
export async function runDrupalMutation<T>(
  creds: DrupalCredentials,
  query: string,
  variables: Record<string, unknown>,
): Promise<T> {
  const res = await fetch(`${creds.drupalUrl}/graphql`, {
    method:  'POST',
    headers: {
      Authorization:  `Bearer ${creds.token}`,
      'Content-Type': 'application/json',
      Accept:         'application/json',
    },
    body: JSON.stringify({ query, variables }),
  });

  if (!res.ok) {
    throw new Error(`Drupal returned ${res.status}: ${await res.text()}`);
  }

  const payload = (await res.json()) as {
    data?:   T;
    errors?: Array<{ message: string }>;
  };

  if (payload.errors && payload.errors.length > 0) {
    throw new Error(payload.errors[0].message);
  }
  if (!payload.data) {
    throw new Error('Drupal returned no data.');
  }
  return payload.data;
}
