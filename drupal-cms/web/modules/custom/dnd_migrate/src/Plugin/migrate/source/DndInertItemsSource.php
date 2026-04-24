<?php

declare(strict_types=1);

namespace Drupal\dnd_migrate\Plugin\migrate\source;

use Drupal\migrate\MigrateException;
use Drupal\migrate\Plugin\migrate\source\SourcePluginBase;

/**
 * Source plugin that yields one row per unique inert magic item.
 *
 * Scans all JSON files in one or more configured directories for items in the
 * top-level "magic_items" array whose name contains "(Inert)".  Each unique
 * item name produces exactly one source row, keyed by a slugified version of
 * the name.
 *
 * Configuration:
 *   data_dirs: list of absolute directory paths to scan.
 *
 * Example plugin configuration:
 * @code
 * source:
 *   plugin: dnd_inert_items_source
 *   data_dirs:
 *     - '/var/www/html/game_data/characters'
 *     - '/var/www/html/game_data/npcs'
 * @endcode
 *
 * @MigrateSource(
 *   id = "dnd_inert_items_source",
 *   source_module = "dnd_migrate"
 * )
 */
class DndInertItemsSource extends SourcePluginBase {

  /**
   * {@inheritdoc}
   *
   * @return array<string, array<string, string>>
   *   Source ID definitions keyed by property name.
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
   *   Human-readable field labels keyed by property name.
   */
  public function fields(): array {
    return [
      'item_key'  => (string) $this->t('Slugified item name used as unique ID'),
      'item_name' => (string) $this->t('Full item name including the (Inert) suffix'),
    ];
  }

  /**
   * {@inheritdoc}
   */
  public function __toString(): string {
    return 'dnd_inert_items_source';
  }

  /**
   * {@inheritdoc}
   *
   * @throws \Drupal\migrate\MigrateException
   */
  protected function initializeIterator(): \Iterator {
    $data_dirs = $this->configuration['data_dirs'] ?? [];
    if (!is_array($data_dirs) || $data_dirs === []) {
      throw new MigrateException('dnd_inert_items_source requires a "data_dirs" list configuration key.');
    }

    $seen = [];

    foreach ($data_dirs as $data_dir) {
      if (!is_dir((string) $data_dir)) {
        continue;
      }

      $files = glob($data_dir . '/*.json');
      if ($files === FALSE) {
        continue;
      }

      foreach ($files as $filepath) {
        if (str_contains(strtolower(basename($filepath)), 'example')) {
          continue;
        }

        $raw = file_get_contents($filepath);
        if ($raw === FALSE) {
          continue;
        }

        $data = json_decode($raw, TRUE);
        if (!is_array($data)) {
          continue;
        }

        $magic_items = $data['magic_items'] ?? [];
        if (!is_array($magic_items)) {
          continue;
        }

        foreach ($magic_items as $item_name) {
          if (!is_string($item_name) || !str_contains($item_name, '(Inert)')) {
            continue;
          }

          $key = $this->slugify($item_name);
          if (isset($seen[$key])) {
            continue;
          }

          $seen[$key] = TRUE;
          yield [
            'item_key'  => $key,
            'item_name' => $item_name,
          ];
        }
      }
    }
  }

  /**
   * Convert an item name to a slug suitable for use as a unique key.
   *
   * @param string $name
   *   The item name.
   *
   * @return string
   *   Lowercased, non-alphanumeric characters replaced with underscores.
   */
  private function slugify(string $name): string {
    $slug = strtolower($name);
    $slug = preg_replace('/[^a-z0-9]+/', '_', $slug) ?? $slug;
    return trim($slug, '_');
  }

}
