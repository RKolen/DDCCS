<?php

declare(strict_types=1);

namespace Drupal\dnd_jobs\Plugin\GraphQL\DataProducer;

use Drupal\Core\Plugin\Context\ContextDefinition;
use Drupal\Core\StringTranslation\TranslatableMarkup;
use Drupal\graphql\Attribute\DataProducer;
use Drupal\graphql\Plugin\GraphQL\DataProducer\DataProducerPluginBase;

/**
 * Reads one field from a job record.
 *
 * Job records are plain arrays from the queue service rather than entities, so
 * every AiJob field is a key lookup; this producer is what the schema extension
 * maps each of them through.
 */
#[DataProducer(
  id: "ai_job_field",
  name: new TranslatableMarkup("AI Job Field"),
  description: new TranslatableMarkup("Reads a single field from a job record."),
  produces: new ContextDefinition(
    data_type: "any",
    label: new TranslatableMarkup("The field value"),
  ),
  consumes: [
    "job" => new ContextDefinition(
      data_type: "any",
      label: new TranslatableMarkup("The job record"),
    ),
    "field" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("The field name"),
    ),
  ],
)]
final class AiJobField extends DataProducerPluginBase {

  /**
   * Read the field.
   *
   * @param mixed $job
   *   The job record.
   * @param string $field
   *   The field name.
   *
   * @return mixed
   *   The field value, or NULL when the record does not carry it.
   */
  public function resolve(mixed $job, string $field): mixed {
    return is_array($job) ? ($job[$field] ?? NULL) : NULL;
  }

}
