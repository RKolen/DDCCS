<?php

declare(strict_types=1);

namespace Drupal\dnd_content\Plugin\GraphQL\DataProducer;

use Drupal\Core\Plugin\Context\ContextDefinition;
use Drupal\Core\StringTranslation\TranslatableMarkup;
use Drupal\graphql\Attribute\DataProducer;
use Drupal\graphql\Plugin\GraphQL\DataProducer\DataProducerPluginBase;

/**
 * Reads one field from a wiki cache entry.
 *
 * Cache entries are flattened to plain arrays by the lookup and upsert
 * producers rather than being returned as nodes, so every WikiCacheEntry field
 * is a key lookup; this producer is what the schema extension maps each of
 * them through.
 */
#[DataProducer(
  id: "wiki_cache_entry_field",
  name: new TranslatableMarkup("Wiki Cache Entry Field"),
  description: new TranslatableMarkup("Reads a single field from a wiki cache entry."),
  produces: new ContextDefinition(
    data_type: "any",
    label: new TranslatableMarkup("The field value"),
  ),
  consumes: [
    "entry" => new ContextDefinition(
      data_type: "any",
      label: new TranslatableMarkup("The wiki cache entry"),
    ),
    "field" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("The field name"),
    ),
  ],
)]
final class WikiCacheEntryField extends DataProducerPluginBase {

  /**
   * Read the field.
   *
   * @param mixed $entry
   *   The wiki cache entry.
   * @param string $field
   *   The field name.
   *
   * @return mixed
   *   The field value, or NULL when the entry does not carry it.
   */
  public function resolve(mixed $entry, string $field): mixed {
    return is_array($entry) ? ($entry[$field] ?? NULL) : NULL;
  }

}
