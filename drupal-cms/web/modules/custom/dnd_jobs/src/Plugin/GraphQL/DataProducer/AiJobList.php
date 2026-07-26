<?php

declare(strict_types=1);

namespace Drupal\dnd_jobs\Plugin\GraphQL\DataProducer;

use Drupal\Core\Plugin\ContainerFactoryPluginInterface;
use Drupal\Core\Plugin\Context\ContextDefinition;
use Drupal\Core\StringTranslation\TranslatableMarkup;
use Drupal\dnd_jobs\Service\JobQueue;
use Drupal\graphql\Attribute\DataProducer;
use Drupal\graphql\GraphQL\Execution\FieldContext;
use Drupal\graphql\Plugin\GraphQL\DataProducer\DataProducerPluginBase;
use Symfony\Component\DependencyInjection\ContainerInterface;

/**
 * Lists queued AI jobs, most recent first.
 *
 * Backs the console activity bar: what is running, what is waiting behind it,
 * and what finished while you were on another screen.
 */
#[DataProducer(
  id: "ai_jobs",
  name: new TranslatableMarkup("AI Jobs"),
  description: new TranslatableMarkup("Lists queued AI jobs, optionally filtered by state."),
  produces: new ContextDefinition(
    data_type: "any",
    label: new TranslatableMarkup("The jobs"),
  ),
  consumes: [
    "states" => new ContextDefinition(
      data_type: "any",
      label: new TranslatableMarkup("States to include"),
      required: FALSE,
    ),
    "limit" => new ContextDefinition(
      data_type: "integer",
      label: new TranslatableMarkup("Maximum number of jobs"),
      required: FALSE,
    ),
  ],
)]
final class AiJobList extends DataProducerPluginBase implements ContainerFactoryPluginInterface {

  /**
   * How many jobs to return when the caller does not say.
   */
  private const DEFAULT_LIMIT = 20;

  /**
   * The AI job queue.
   *
   * @var \Drupal\dnd_jobs\Service\JobQueue
   */
  protected JobQueue $jobQueue;

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
  ): self {
    $instance = new self($configuration, $plugin_id, $plugin_definition);
    $instance->jobQueue = $container->get('dnd_jobs.job_queue');

    return $instance;
  }

  /**
   * List the jobs.
   *
   * @param mixed $states
   *   The states to include, or NULL for every state.
   * @param int|null $limit
   *   The maximum number of jobs to return.
   * @param \Drupal\graphql\GraphQL\Execution\FieldContext $context
   *   The GraphQL field execution context.
   *
   * @return array<int, array<string, mixed>>
   *   The job records, most recent first.
   */
  public function resolve(mixed $states, ?int $limit, FieldContext $context): array {
    // The activity bar polls this; a cached list would freeze it.
    $context->mergeCacheMaxAge(0);

    $wanted = [];
    if (is_array($states)) {
      $wanted = array_values(array_filter(
        array_map(static fn (mixed $state): string => is_string($state) ? trim($state) : '', $states),
        static fn (string $state): bool => $state !== '',
      ));
    }

    return $this->jobQueue->list($wanted, $limit ?? self::DEFAULT_LIMIT);
  }

}
