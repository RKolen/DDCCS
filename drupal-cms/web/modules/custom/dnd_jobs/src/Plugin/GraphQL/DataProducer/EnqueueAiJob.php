<?php

declare(strict_types=1);

namespace Drupal\dnd_jobs\Plugin\GraphQL\DataProducer;

use Drupal\Component\Plugin\Exception\PluginException;
use Drupal\Core\Plugin\ContainerFactoryPluginInterface;
use Drupal\Core\Plugin\Context\ContextDefinition;
use Drupal\Core\StringTranslation\TranslatableMarkup;
use Drupal\dnd_jobs\Service\JobQueue;
use Drupal\graphql\Attribute\DataProducer;
use Drupal\graphql\Plugin\GraphQL\DataProducer\DataProducerPluginBase;
use GraphQL\Error\UserError;
use Symfony\Component\DependencyInjection\ContainerInterface;

/**
 * Enqueues a heavy AI job and returns it immediately.
 *
 * Nothing runs here: the job lands in the single serialized queue and the
 * console gets an id to poll, which is what makes navigating away safe.
 */
#[DataProducer(
  id: "enqueue_ai_job",
  name: new TranslatableMarkup("Enqueue AI Job"),
  description: new TranslatableMarkup("Queues a heavy AI job for background processing."),
  produces: new ContextDefinition(
    data_type: "any",
    label: new TranslatableMarkup("The queued job"),
  ),
  consumes: [
    "type" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("Job type plugin id"),
    ),
    "payload" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("JSON-encoded job payload"),
    ),
    "label" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("Display label"),
    ),
  ],
)]
final class EnqueueAiJob extends DataProducerPluginBase implements ContainerFactoryPluginInterface {

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
   * Queue the job.
   *
   * @param string $type
   *   The job type plugin id.
   * @param string $payload
   *   The JSON-encoded job payload.
   * @param string $label
   *   The display label for the activity bar.
   *
   * @return array<string, mixed>
   *   The queued job record.
   *
   * @throws \GraphQL\Error\UserError
   *   When the payload is not a JSON object, the job type is not registered,
   *   or the queue is unavailable.
   */
  public function resolve(string $type, string $payload, string $label): array {
    $decoded = json_decode($payload, TRUE);
    if (!is_array($decoded)) {
      throw new UserError('Job payload must be a JSON-encoded object.');
    }

    $label = trim($label);
    if ($label === '') {
      throw new UserError('A job label is required.');
    }
    $decoded['label'] = $label;

    try {
      return $this->jobQueue->enqueue(trim($type), $decoded);
    }
    catch (PluginException) {
      // Uncaught, GraphQL masks this as "Internal server error".
      throw new UserError(sprintf(
        'Unknown job type "%s". Run "ddev drush cache:rebuild" if the job type was just added.',
        trim($type),
      ));
    }
    catch (\RuntimeException | \InvalidArgumentException $e) {
      throw new UserError('Could not queue the job: ' . $e->getMessage());
    }
  }

}
