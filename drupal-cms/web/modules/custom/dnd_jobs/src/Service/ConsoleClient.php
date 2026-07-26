<?php

declare(strict_types=1);

namespace Drupal\dnd_jobs\Service;

use GuzzleHttp\ClientInterface;
use GuzzleHttp\Exception\GuzzleException;

/**
 * Calls the console's own server-side API routes from a queue worker.
 *
 * Portrait generation is a single sidecar call, so its job talks to the sidecar
 * directly. Arc analysis, story generation, and session summaries are
 * orchestrations - chunking, per-passage model calls, prompt assembly, Drupal
 * writes - that already exist as console API routes. The worker calls those
 * rather than growing a second copy of the same logic in PHP; what the queue
 * adds is serialization, persistence, and tracking, not new AI code.
 *
 * The base URL and timeout come from the environment (GATSBY_SERVER_URL,
 * SIDECAR_JOB_TIMEOUT, injected into the web container by DDEV) with no
 * defaults.
 */
final class ConsoleClient {

  /**
   * Constructs a ConsoleClient.
   *
   * @param \GuzzleHttp\ClientInterface $httpClient
   *   The HTTP client.
   */
  public function __construct(private readonly ClientInterface $httpClient) {}

  /**
   * POST a JSON payload to a console API route and decode the response.
   *
   * @param string $route
   *   The route name under /api (e.g. "run-arc-analysis").
   * @param array<string, mixed> $payload
   *   The request body.
   *
   * @return array<string, mixed>
   *   The decoded response body.
   *
   * @throws \RuntimeException
   *   When the console is unconfigured or unreachable, returns a non-2xx
   *   status, or returns a body that is not a JSON object.
   */
  public function post(string $route, array $payload): array {
    $url = $this->baseUrl() . '/api/' . ltrim($route, '/');

    try {
      $response = $this->httpClient->request('POST', $url, [
        'json' => $payload,
        'timeout' => $this->timeout(),
        'headers' => ['Accept' => 'application/json'],
      ]);
    }
    catch (GuzzleException $e) {
      throw new \RuntimeException(sprintf('Console request to %s failed: %s', $route, $e->getMessage()), 0, $e);
    }

    $status = $response->getStatusCode();
    $body = (string) $response->getBody();
    if ($status < 200 || $status >= 300) {
      throw new \RuntimeException(sprintf('Console %s returned HTTP %d: %s', $route, $status, $body));
    }

    $decoded = json_decode($body, TRUE);
    if (!is_array($decoded)) {
      throw new \RuntimeException(sprintf('Console %s returned a non-JSON body.', $route));
    }

    return $decoded;
  }

  /**
   * Read the console base URL from the environment.
   *
   * @return string
   *   The base URL, without a trailing slash.
   *
   * @throws \RuntimeException
   *   When GATSBY_SERVER_URL is not set in the container environment.
   */
  private function baseUrl(): string {
    $url = getenv('GATSBY_SERVER_URL');
    if (!is_string($url) || trim($url) === '') {
      throw new \RuntimeException('GATSBY_SERVER_URL is not set for the web container; queued jobs cannot reach the console API.');
    }

    return rtrim(trim($url), '/');
  }

  /**
   * Read the per-request timeout, in seconds, from the environment.
   *
   * @return float
   *   The read timeout for a console call.
   *
   * @throws \RuntimeException
   *   When SIDECAR_JOB_TIMEOUT is not set or is not a positive number.
   */
  private function timeout(): float {
    $raw = getenv('SIDECAR_JOB_TIMEOUT');
    if (!is_string($raw) || !is_numeric(trim($raw)) || (float) $raw <= 0) {
      throw new \RuntimeException('SIDECAR_JOB_TIMEOUT must be set to a positive number of seconds for the web container.');
    }

    return (float) $raw;
  }

}
