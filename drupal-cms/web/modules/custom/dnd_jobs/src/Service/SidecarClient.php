<?php

declare(strict_types=1);

namespace Drupal\dnd_jobs\Service;

use GuzzleHttp\ClientInterface;
use GuzzleHttp\Exception\GuzzleException;

/**
 * Calls the host Python sidecar from a queue worker.
 *
 * All heavy AI runs on the host, never inside DDEV, so every job type reaches
 * its model through this client. The sidecar endpoints stay request/response:
 * the queue - not the HTTP layer - is what makes the work asynchronous, which
 * is why the read timeout is measured in minutes rather than seconds.
 *
 * The base URL and timeout come from the environment (SIDECAR_URL,
 * SIDECAR_JOB_TIMEOUT, injected into the web container by DDEV) with no
 * defaults: a missing value is a configuration error, not something to guess.
 */
final class SidecarClient {

  /**
   * Constructs a SidecarClient.
   *
   * @param \GuzzleHttp\ClientInterface $httpClient
   *   The HTTP client.
   */
  public function __construct(private readonly ClientInterface $httpClient) {}

  /**
   * POST a JSON payload to a sidecar endpoint and decode the JSON response.
   *
   * @param string $path
   *   The endpoint path, leading slash included (e.g. "/character/portrait").
   * @param array<string, mixed> $payload
   *   The request body, JSON-encoded on the way out.
   *
   * @return array<string, mixed>
   *   The decoded response body.
   *
   * @throws \RuntimeException
   *   When the sidecar is unconfigured, unreachable, returns a non-2xx status,
   *   or returns a body that is not a JSON object.
   */
  public function post(string $path, array $payload): array {
    $url = $this->baseUrl() . $path;

    try {
      $response = $this->httpClient->request('POST', $url, [
        'json' => $payload,
        'timeout' => $this->timeout(),
        'headers' => $this->headers(),
      ]);
    }
    catch (GuzzleException $e) {
      throw new \RuntimeException(sprintf('Sidecar request to %s failed: %s', $path, $e->getMessage()), 0, $e);
    }

    $status = $response->getStatusCode();
    $body = (string) $response->getBody();
    if ($status < 200 || $status >= 300) {
      throw new \RuntimeException(sprintf('Sidecar %s returned HTTP %d: %s', $path, $status, $body));
    }

    $decoded = json_decode($body, TRUE);
    if (!is_array($decoded)) {
      throw new \RuntimeException(sprintf('Sidecar %s returned a non-JSON body.', $path));
    }

    return $decoded;
  }

  /**
   * Build the request headers, including the shared secret when one is set.
   *
   * Reaching the sidecar from a container means it listens on more than the
   * loopback interface, so it may be protected by SIDECAR_SECRET. The sidecar
   * treats an unset secret as "no auth", and so does this client.
   *
   * @return array<string, string>
   *   The request headers.
   */
  private function headers(): array {
    $headers = ['Accept' => 'application/json'];
    $secret = getenv('SIDECAR_SECRET');
    if (is_string($secret) && trim($secret) !== '') {
      $headers['X-Sidecar-Secret'] = trim($secret);
    }

    return $headers;
  }

  /**
   * Read the sidecar base URL from the environment.
   *
   * @return string
   *   The base URL, without a trailing slash.
   *
   * @throws \RuntimeException
   *   When SIDECAR_URL is not set in the container environment.
   */
  private function baseUrl(): string {
    $url = getenv('SIDECAR_URL');
    if (!is_string($url) || trim($url) === '') {
      throw new \RuntimeException('SIDECAR_URL is not set for the web container; queued AI jobs cannot reach the host sidecar.');
    }
    return rtrim(trim($url), '/');
  }

  /**
   * Read the per-request timeout, in seconds, from the environment.
   *
   * @return float
   *   The read timeout for a sidecar call.
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
