<?php

declare(strict_types=1);

namespace Drupal\dnd_migrate\Plugin\migrate\source;

use Drupal\migrate\MigrateException;
use Drupal\migrate\Plugin\migrate\source\SourcePluginBase;

/**
 * Source plugin for the custom_items.json keyed-object format.
 *
 * The items JSON file uses item names as top-level keys, with each value
 * being an item definition object. This plugin iterates over those keyed
 * entries and yields one source row per item.
 *
 * Example plugin configuration:
 * @code
 * source:
 *   plugin: dnd_items_json
 *   file_path: '/var/www/html/game_data/items/custom_items.json'
 * @endcode
 *
 * @MigrateSource(
 *   id = "dnd_items_json",
 *   source_module = "dnd_migrate"
 * )
 */
class DndItemsJson extends SourcePluginBase {

  /**
   * {@inheritdoc}
   *
   * @return array<string, array<string, string>>
   *   Field IDs mapped to their type definitions.
   */
  public function getIds(): array {
    return [
      'item_key' => ['type' => 'string'],
    ];
  }

  /**
   * {@inheritdoc}
   *
   * @return array<string, string>
   *   Field names mapped to their human-readable labels.
   */
  public function fields(): array {
    return [
      'item_key' => (string) $this->t('Item key (the top-level JSON object key, typically the item name)'),
      'name' => (string) $this->t('Item display name'),
      'item_type' => (string) $this->t('Item type identifier (e.g. magic_item, weapon, armor)'),
      'is_magic' => (string) $this->t('Boolean flag indicating whether the item is magical'),
      'description' => (string) $this->t('Human-readable item description'),
      'properties' => (string) $this->t('Properties object containing rarity, attunement, benefit'),
      'notes' => (string) $this->t('Free-form notes about the item'),
    ];
  }

  /**
   * {@inheritdoc}
   */
  public function __toString(): string {
    return $this->configuration['file_path'] ?? 'dnd_items_json';
  }

  /**
   * {@inheritdoc}
   *
   * @throws \Drupal\migrate\MigrateException
   *   Thrown when file_path is missing or the file cannot be read.
   */
  protected function initializeIterator(): \Iterator {
    $file_path = $this->configuration['file_path'] ?? '';

    if ($file_path === '') {
      throw new MigrateException('The dnd_items_json source plugin requires a "file_path" configuration key.');
    }

    if (!is_file($file_path)) {
      throw new MigrateException(sprintf('The configured file_path "%s" does not exist or is not a file.', $file_path));
    }

    $raw = file_get_contents($file_path);
    if ($raw === FALSE) {
      throw new MigrateException(sprintf('Could not read file at "%s".', $file_path));
    }

    $data = json_decode($raw, TRUE);
    if (!is_array($data)) {
      throw new MigrateException(sprintf('The file "%s" does not contain a valid JSON object.', $file_path));
    }

    foreach ($data as $item_key => $item_data) {
      if (!is_array($item_data)) {
        continue;
      }
      yield ['item_key' => $item_key] + $item_data;
    }
  }

}
