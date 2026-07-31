<?php

declare(strict_types=1);

namespace Drupal\dnd_jobs\Plugin\GraphQL\DataProducer;

use Drupal\Core\Plugin\ContainerFactoryPluginInterface;
use Drupal\Core\Plugin\Context\ContextDefinition;
use Drupal\Core\StringTranslation\TranslatableMarkup;
use Drupal\dnd_jobs\Service\JobQueue;
use Drupal\graphql\Attribute\DataProducer;
use Drupal\graphql\Plugin\GraphQL\DataProducer\DataProducerPluginBase;
use GraphQL\Error\UserError;
use Symfony\Component\DependencyInjection\ContainerInterface;

/**
 * Deletes finished jobs, clearing the console's activity log.
 *
 * The activity bar is a live view of the job table with no copy of its own, so
 * "Clear completed" has to delete rows to have any effect. Live work and
 * results still awaiting a decision are protected by the queue service.
 */
#[DataProducer(
  id: "clear_ai_jobs",
  name: new TranslatableMarkup("Clear AI Jobs"),
  description: new TranslatableMarkup("Deletes finished jobs from the queue."),
  produces: new ContextDefinition(
    data_type: "any",
    label: new TranslatableMarkup("How many jobs were cleared and kept"),
  ),
  consumes: [
    "states" => new ContextDefinition(
      data_type: "any",
      label: new TranslatableMarkup("Terminal states to clear"),
      required: FALSE,
    ),
  ],
)]
final class ClearAiJobs extends DataProducerPluginBase implements ContainerFactoryPluginInterface {

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
   * Clear the finished jobs.
   *
   * @param mixed $states
   *   The terminal states to clear, or NULL for every terminal state.
   *
   * @return array{cleared: int, kept: int}
   *   How many jobs were deleted, and how many were kept back for review.
   *
   * @throws \GraphQL\Error\UserError
   *   When a state that is not terminal is asked for.
   */
  public function resolve(mixed $states): array {
    $wanted = [];
    if (is_array($states)) {
      $wanted = array_values(array_filter(
        array_map(static fn (mixed $state): string => is_string($state) ? trim($state) : '', $states),
        static fn (string $state): bool => $state !== '',
      ));
    }

    try {
      return $this->jobQueue->clearFinished($wanted);
    }
    catch (\InvalidArgumentException $e) {
      throw new UserError($e->getMessage());
    }
  }

}
