<?php

declare(strict_types=1);

namespace Drupal\dnd_jobs\Plugin\AdvancedQueue\JobType;

use Drupal\advancedqueue\Job;
use Drupal\advancedqueue\Plugin\AdvancedQueue\JobType\JobTypeBase;
use Drupal\Core\Entity\EntityTypeManagerInterface;
use Drupal\Core\Logger\LoggerChannelInterface;
use Drupal\Core\Plugin\ContainerFactoryPluginInterface;
use Drupal\dnd_jobs\Service\ConsoleClient;
use Drupal\dnd_jobs\Service\SidecarClient;
use Drupal\node\NodeInterface;
use Symfony\Component\DependencyInjection\ContainerInterface;

/**
 * Shared plumbing for the D&D AI job types.
 *
 * Every job type follows the same shape: read a payload the console enqueued,
 * run the model work on the host, store the outcome in Drupal, and write a
 * small result back onto the payload for the console to pick up on its next
 * poll. Single sidecar calls go through $sidecar; multi-step orchestrations
 * that already exist as console routes go through $console rather than being
 * reimplemented here.
 *
 * @phpstan-consistent-constructor
 */
abstract class AiJobTypeBase extends JobTypeBase implements ContainerFactoryPluginInterface {

  /**
   * The entity type manager.
   *
   * @var \Drupal\Core\Entity\EntityTypeManagerInterface
   */
  protected EntityTypeManagerInterface $entityTypeManager;

  /**
   * The logger channel.
   *
   * @var \Drupal\Core\Logger\LoggerChannelInterface
   */
  protected LoggerChannelInterface $logger;

  /**
   * The console API client.
   *
   * @var \Drupal\dnd_jobs\Service\ConsoleClient
   */
  protected ConsoleClient $console;

  /**
   * The host sidecar client.
   *
   * @var \Drupal\dnd_jobs\Service\SidecarClient
   */
  protected SidecarClient $sidecar;

  /**
   * {@inheritdoc}
   *
   * @param \Symfony\Component\DependencyInjection\ContainerInterface $container
   *   The service container.
   * @param array<string, mixed> $configuration
   *   Plugin configuration.
   * @param string $plugin_id
   *   The plugin ID.
   * @param mixed $plugin_definition
   *   The plugin definition.
   */
  public static function create(
    ContainerInterface $container,
    array $configuration,
    $plugin_id,
    $plugin_definition,
  ): static {
    $instance = new static($configuration, $plugin_id, $plugin_definition);
    $instance->entityTypeManager = $container->get('entity_type.manager');
    $instance->logger = $container->get('logger.factory')->get('dnd_jobs');
    $instance->console = $container->get('dnd_jobs.console_client');
    $instance->sidecar = $container->get('dnd_jobs.sidecar_client');

    return $instance;
  }

  /**
   * Load a node of the expected bundle by UUID.
   *
   * @param string $uuid
   *   The node UUID.
   * @param string $bundle
   *   The expected content type.
   *
   * @return \Drupal\node\NodeInterface
   *   The node.
   *
   * @throws \RuntimeException
   *   When no node of that bundle matches the UUID.
   */
  protected function loadNode(string $uuid, string $bundle): NodeInterface {
    $nodes = $this->entityTypeManager
      ->getStorage('node')
      ->loadByProperties(['uuid' => $uuid, 'type' => $bundle]);
    $node = reset($nodes);
    if (!$node instanceof NodeInterface) {
      throw new \RuntimeException(sprintf('No %s node found for id %s.', $bundle, $uuid));
    }

    return $node;
  }

  /**
   * Read a required string from a job payload.
   *
   * @param array<string, mixed> $payload
   *   The job payload.
   * @param string $key
   *   The payload key.
   *
   * @return string
   *   The trimmed value.
   *
   * @throws \RuntimeException
   *   When the key is missing or blank.
   */
  protected function requireString(array $payload, string $key): string {
    $value = $payload[$key] ?? NULL;
    if (!is_string($value) || trim($value) === '') {
      throw new \RuntimeException(sprintf('Job payload is missing "%s".', $key));
    }

    return trim($value);
  }

  /**
   * Read an optional string from a job payload.
   *
   * @param array<string, mixed> $payload
   *   The job payload.
   * @param string $key
   *   The payload key.
   *
   * @return string|null
   *   The trimmed value, or NULL when absent or blank.
   */
  protected function optionalString(array $payload, string $key): ?string {
    $value = $payload[$key] ?? NULL;
    if (!is_string($value) || trim($value) === '') {
      return NULL;
    }

    return trim($value);
  }

  /**
   * Read an optional integer from a job payload.
   *
   * @param array<string, mixed> $payload
   *   The job payload.
   * @param string $key
   *   The payload key.
   *
   * @return int|null
   *   The value, or NULL when absent or not numeric.
   */
  protected function optionalInt(array $payload, string $key): ?int {
    $value = $payload[$key] ?? NULL;
    if (is_int($value)) {
      return $value;
    }

    return is_string($value) && is_numeric($value) ? (int) $value : NULL;
  }

  /**
   * Read an array from a job payload.
   *
   * @param array<string, mixed> $payload
   *   The job payload.
   * @param string $key
   *   The payload key.
   *
   * @return array<string, mixed>
   *   The value, or an empty array when absent.
   */
  protected function arrayValue(array $payload, string $key): array {
    $value = $payload[$key] ?? NULL;

    return is_array($value) ? $value : [];
  }

  /**
   * Attach a result to the job so the console can read it when polling.
   *
   * The processor persists the (mutated) payload when the job finishes, so
   * anything stored here survives to the next status poll.
   *
   * @param \Drupal\advancedqueue\Job $job
   *   The job being processed.
   * @param array<string, mixed> $result
   *   The result values (e.g. a new image URL or created node id).
   */
  protected function storeResult(Job $job, array $result): void {
    $payload = $job->getPayload();
    $payload['result'] = $result;
    $job->setPayload($payload);
  }

}
