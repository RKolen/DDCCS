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
 * Reads one queued AI job by id.
 *
 * This is the console's poll target, so the result must never be cached: a
 * cached "queued" would keep a finished job spinning in the UI forever.
 */
#[DataProducer(
  id: "ai_job",
  name: new TranslatableMarkup("AI Job"),
  description: new TranslatableMarkup("Reads a single queued AI job."),
  produces: new ContextDefinition(
    data_type: "any",
    label: new TranslatableMarkup("The job"),
  ),
  consumes: [
    "id" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("Job id"),
    ),
  ],
)]
final class AiJobStatus extends DataProducerPluginBase implements ContainerFactoryPluginInterface {

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
   * Read the job.
   *
   * @param string $id
   *   The job id.
   * @param \Drupal\graphql\GraphQL\Execution\FieldContext $context
   *   The GraphQL field execution context.
   *
   * @return array<string, mixed>|null
   *   The job record, or NULL when no such job exists.
   */
  public function resolve(string $id, FieldContext $context): ?array {
    // Job state changes outside any entity/cache tag, so this must be
    // uncacheable or a poll would keep returning the first state it saw.
    $context->mergeCacheMaxAge(0);

    return $this->jobQueue->load(trim($id));
  }

}
