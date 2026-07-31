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
 * Puts a job back on the queue after its worker went away.
 *
 * The manual half of the stall recovery: hook_cron() sweeps expired leases on
 * its own schedule, and this lets the operator act the moment they notice a job
 * that stopped moving rather than waiting for the next cron run.
 */
#[DataProducer(
  id: "requeue_ai_job",
  name: new TranslatableMarkup("Requeue AI Job"),
  description: new TranslatableMarkup("Puts a stalled job back on the queue."),
  produces: new ContextDefinition(
    data_type: "any",
    label: new TranslatableMarkup("The requeued job"),
  ),
  consumes: [
    "id" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("Job id"),
    ),
  ],
)]
final class RequeueAiJob extends DataProducerPluginBase implements ContainerFactoryPluginInterface {

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
   * Requeue the job.
   *
   * @param string $id
   *   The job id.
   *
   * @return array<string, mixed>
   *   The requeued job record.
   *
   * @throws \GraphQL\Error\UserError
   *   When no such job exists.
   */
  public function resolve(string $id): array {
    $job = $this->jobQueue->requeue(trim($id));
    if ($job === NULL) {
      throw new UserError(sprintf('No job found with id %s.', trim($id)));
    }

    return $job;
  }

}
