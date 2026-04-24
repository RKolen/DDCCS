<?php

declare(strict_types=1);

namespace Drupal\dnd_migrate\Plugin\migrate\process;

use Drupal\migrate\MigrateExecutableInterface;
use Drupal\migrate\Plugin\MigrationInterface;
use Drupal\migrate\Plugin\MigrationPluginManagerInterface;
use Drupal\migrate\ProcessPluginBase;
use Drupal\migrate\Row;
use Drupal\Core\Plugin\ContainerFactoryPluginInterface;
use Symfony\Component\DependencyInjection\ContainerInterface;

/**
 * Looks up spell slot paragraph IDs from the dnd_character_spell_slots map.
 *
 * This process plugin resolves a spell_slots object ({"1": 4, "2": 3} ...) to
 * an array of entity_reference_revisions values suitable for the
 * field_spell_slots ERR field on node:character.
 *
 * For each spell level present in the source, it queries the migrate ID map
 * for the dnd_character_spell_slots migration to retrieve the corresponding
 * paragraph entity IDs.
 *
 * The migration dnd_character_spell_slots must have run before this plugin
 * is used.
 *
 * Example configuration:
 * @code
 * process:
 *   field_spell_slots:
 *     plugin: dnd_spell_slot_lookup
 *     source: spell_slots
 * @endcode
 *
 * @MigrateProcessPlugin(
 *   id = "dnd_spell_slot_lookup",
 *   handle_multiples = FALSE
 * )
 */
final class DndSpellSlotLookup extends ProcessPluginBase implements ContainerFactoryPluginInterface {
  /**
   * The migration plugin manager.
   *
   * @var \Drupal\migrate\Plugin\MigrationPluginManagerInterface
   */
  protected MigrationPluginManagerInterface $migrationPluginManager;

  /**
   * Constructs a DndSpellSlotLookup process plugin instance.
   *
   * @param array<string, mixed> $configuration
   *   Plugin configuration.
   * @param string $plugin_id
   *   Plugin ID.
   * @param mixed $plugin_definition
   *   Plugin definition.
   * @param \Drupal\migrate\Plugin\MigrationPluginManagerInterface $migration_plugin_manager
   *   The migration plugin manager service.
   */
  public function __construct(
    array $configuration,
    string $plugin_id,
    mixed $plugin_definition,
    MigrationPluginManagerInterface $migration_plugin_manager,
  ) {
    parent::__construct($configuration, $plugin_id, $plugin_definition);
    $this->migrationPluginManager = $migration_plugin_manager;
  }

  /**
   * Creates an instance of the plugin.
   *
   * @param \Symfony\Component\DependencyInjection\ContainerInterface $container
   *   The service container.
   * @param array<string, mixed> $configuration
   *   Plugin configuration.
   * @param string $plugin_id
   *   Plugin ID.
   * @param mixed $plugin_definition
   *   Plugin definition.
   *
   * @return static
   *   Plugin instance.
   */
  public static function create(
    ContainerInterface $container,
    array $configuration,
    $plugin_id,
    $plugin_definition,
  ): static {
    return new static(
          $configuration,
          $plugin_id,
          $plugin_definition,
          $container->get('plugin.manager.migration'),
      );
  }

  /**
   * {@inheritdoc}
   *
   * @param mixed $value
   *   The spell_slots array keyed by level (e.g. {"1": 4, "2": 3}).
   * @param \Drupal\migrate\MigrateExecutableInterface $migrate_executable
   *   The migration executable.
   * @param \Drupal\migrate\Row $row
   *   The current source row (provides file_id).
   * @param string $destination_property
   *   The destination property name.
   *
   * @return array<int, array{target_id: int, target_revision_id: int}>
   *   Array of paragraph reference arrays for the ERR field.
   */
  public function transform(
    $value,
    MigrateExecutableInterface $migrate_executable,
    Row $row,
    $destination_property,
  ): array {
    if (!is_array($value) || $value === []) {
      return [];
    }

    $file_id = (string) $row->getSourceProperty('file_id');

    $migration_instance = $this->migrationPluginManager->createInstance('dnd_character_spell_slots');
    if (!$migration_instance instanceof MigrationInterface) {
      return [];
    }

    $id_map = $migration_instance->getIdMap();

    $results = [];
    foreach (array_keys($value) as $level) {
      $destination_ids = $id_map->lookupDestinationIds([
        'file_id' => $file_id,
        'slot_level' => (int) $level,
      ]);

      if ($destination_ids === []) {
        continue;
      }

      $first_key = array_key_first($destination_ids);
      $first_match = $destination_ids[$first_key];

      if (!is_array($first_match) || count($first_match) < 2) {
        continue;
      }

      $results[] = [
        'target_id' => (int) $first_match[0],
        'target_revision_id' => (int) $first_match[1],
      ];
    }

    return $results;
  }

}
