<?php

declare(strict_types=1);

namespace Drupal\dnd_migrate\Plugin\migrate\source;

use Drupal\migrate\MigrateException;
use Drupal\migrate\Plugin\migrate\source\SourcePluginBase;

/**
 * Source plugin that flattens spell_slots objects into individual rows.
 *
 * Characters store spell slots as a JSON object keyed by spell level:
 * {"1": 4, "2": 3, "3": 2}
 *
 * This plugin reads all character JSON files from a directory and yields
 * one row per (character, slot_level) combination, so that each row can
 * be migrated into a separate paragraph:spell_slot entity.
 *
 * Example plugin configuration:
 * @code
 * source:
 *   plugin: dnd_spell_slots_source
 *   data_dir: '/var/www/html/game_data/characters'
 * @endcode
 *
 * @MigrateSource(
 *   id = "dnd_spell_slots_source",
 *   source_module = "dnd_migrate"
 * )
 */
class DndSpellSlotsSource extends SourcePluginBase {

  /**
   * {@inheritdoc}
   *
   * @return array<string, array<string, string>>
   *   Field IDs mapped to their type definitions.
   */
  public function getIds(): array {
    return [
      'file_id' => ['type' => 'string'],
      'slot_level' => ['type' => 'integer'],
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
      'file_id' => (string) $this->t('Character file identifier (filename without .json)'),
      'slot_level' => (string) $this->t('Spell slot level (1-9)'),
      'slot_total' => (string) $this->t('Total number of spell slots at this level'),
    ];
  }

  /**
   * {@inheritdoc}
   */
  public function __toString(): string {
    return $this->configuration['data_dir'] ?? 'dnd_spell_slots_source';
  }

  /**
   * {@inheritdoc}
   *
   * @throws \Drupal\migrate\MigrateException
   *   Thrown when data_dir is missing or is not a valid directory.
   */
  protected function initializeIterator(): \Iterator {
    $data_dir = $this->configuration['data_dir'] ?? '';

    if ($data_dir === '') {
      throw new MigrateException('The dnd_spell_slots_source plugin requires a "data_dir" configuration key.');
    }

    if (!is_dir($data_dir)) {
      throw new MigrateException(sprintf('The configured data_dir "%s" does not exist or is not a directory.', $data_dir));
    }

    $files = glob($data_dir . '/*.json');
    if ($files === FALSE || $files === []) {
      return;
    }

    foreach ($files as $filepath) {
      $basename = basename($filepath, '.json');

      if (str_contains(strtolower($basename), 'example')) {
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

      // Optional: filter by profile_type.
      if (array_key_exists('profile_type_filter', $this->configuration)) {
        $expected = (string) $this->configuration['profile_type_filter'];
        $actual   = (string) ($data['profile_type'] ?? '');
        if ($actual !== $expected) {
          continue;
        }
      }

      $spell_slots = $data['spell_slots'] ?? [];
      if (!is_array($spell_slots) || $spell_slots === []) {
        continue;
      }

      foreach ($spell_slots as $level => $total) {
        yield [
          'file_id' => $basename,
          'slot_level' => (int) $level,
          'slot_total' => (int) $total,
        ];
      }
    }
  }

}
