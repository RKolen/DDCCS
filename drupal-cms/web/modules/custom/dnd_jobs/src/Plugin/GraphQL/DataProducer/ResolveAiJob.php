<?php

declare(strict_types=1);

namespace Drupal\dnd_jobs\Plugin\GraphQL\DataProducer;

use Drupal\Core\Plugin\ContainerFactoryPluginInterface;
use Drupal\Core\Plugin\Context\ContextDefinition;
use Drupal\Core\StringTranslation\TranslatableMarkup;
use Drupal\dnd_jobs\Service\JobReview;
use Drupal\graphql\Attribute\DataProducer;
use Drupal\graphql\Plugin\GraphQL\DataProducer\DataProducerPluginBase;
use GraphQL\Error\UserError;
use Symfony\Component\DependencyInjection\ContainerInterface;

/**
 * Accepts or discards a finished job's pending result.
 *
 * The console's confirm step. A job type that produces something reviewable
 * stops short of writing it to the content, so this is where a generated
 * portrait actually becomes the character's portrait - or does not.
 *
 * The decision is a string, not a boolean, on purpose. A boolean
 * ContextDefinition here got resolved twice per request - once as FALSE, then
 * with the real argument - which discarded renders the operator had accepted. A
 * string argument arrives once and intact, and JobReview is idempotent besides,
 * so a repeat of the same decision is harmless either way.
 */
#[DataProducer(
  id: "resolve_ai_job",
  name: new TranslatableMarkup("Resolve AI Job"),
  description: new TranslatableMarkup("Accepts or discards a finished job's result."),
  produces: new ContextDefinition(
    data_type: "any",
    label: new TranslatableMarkup("The reviewed job"),
  ),
  consumes: [
    "id" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("Job id"),
    ),
    "decision" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("Either accept or discard"),
    ),
  ],
)]
final class ResolveAiJob extends DataProducerPluginBase implements ContainerFactoryPluginInterface {

  /**
   * The job review service.
   *
   * @var \Drupal\dnd_jobs\Service\JobReview
   */
  protected JobReview $jobReview;

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
    $instance->jobReview = $container->get('dnd_jobs.job_review');

    return $instance;
  }

  /**
   * Apply or drop the job's result.
   *
   * @param string $id
   *   The job id.
   * @param string $decision
   *   Either "accept" (write the result onto the content) or "discard".
   *
   * @return array<string, mixed>
   *   The reviewed job record.
   *
   * @throws \GraphQL\Error\UserError
   *   When the decision is unknown, the job cannot be reviewed, or the write is
   *   not permitted.
   */
  public function resolve(string $id, string $decision): array {
    $decision = strtolower(trim($decision));
    if ($decision !== JobReview::ACCEPT && $decision !== JobReview::DISCARD) {
      throw new UserError(sprintf(
        'Unknown decision "%s": expected "%s" or "%s".',
        $decision,
        JobReview::ACCEPT,
        JobReview::DISCARD
      ));
    }

    try {
      return $this->jobReview->resolve(trim($id), $decision === JobReview::ACCEPT);
    }
    catch (\RuntimeException $e) {
      throw new UserError($e->getMessage());
    }
  }

}
