<?php

declare(strict_types=1);

namespace Drupal\dnd_migrate\Plugin\migrate\process;

use Drupal\migrate\MigrateExecutableInterface;
use Drupal\migrate\Plugin\MigrationInterface;
use Drupal\migrate\Plugin\MigrationPluginManagerInterface;
use Drupal\migrate\ProcessPluginBase;
use Drupal\Core\Plugin\ContainerFactoryPluginInterface;
use Symfony\Component\DependencyInjection\ContainerInterface;
use Drupal\migrate\Row;

/**
 * Looks up a single paragraph ID from a previous paragraph sub-migration.
 *
 * Returns the result as a keyed array suitable for entity_reference_revisions
 * fields: ['target_id' => X, 'target_revision_id' => Y].
 *
 * Unlike the built-in migration_lookup plugin (which returns a flat numeric
 * array), this plugin returns the named-key format that ERR fields require.
 *
 * Example configuration:
 * @code
 * process:
 *   field_backstory:
 *     plugin: dnd_paragraph_lookup
 *     migration: dnd_character_backstory
 *     source: file_id
 * @endcode
 *
 * @MigrateProcessPlugin(
 *   id = "dnd_paragraph_lookup",
 *   handle_multiples = FALSE
 * )
 */
final class DndParagraphLookup extends ProcessPluginBase implements ContainerFactoryPluginInterface {
  /**
   * The migration plugin manager.
   *
   * @var \Drupal\migrate\Plugin\MigrationPluginManagerInterface
   */
  protected MigrationPluginManagerInterface $migrationPluginManager;

  /**
   * Constructs a DndParagraphLookup process plugin instance.
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
   *   The source ID value to look up (e.g. file_id or item_key).
   * @param \Drupal\migrate\MigrateExecutableInterface $migrate_executable
   *   The migration executable.
   * @param \Drupal\migrate\Row $row
   *   The current source row.
   * @param string $destination_property
   *   The destination property name.
   *
   * @return array<string, int>|null
   *   Keyed array with target_id and target_revision_id, or null if not found.
   */
  public function transform(
    $value,
    MigrateExecutableInterface $migrate_executable,
    Row $row,
    $destination_property,
  ): ?array {
    $migration_id = $this->configuration['migration'] ?? '';
    if ($migration_id === '' || $value === NULL || $value === '') {
      return NULL;
    }

    $migration_instance = $this->migrationPluginManager->createInstance($migration_id);
    if (!$migration_instance instanceof MigrationInterface) {
      return NULL;
    }

    $source_id_key = $this->configuration['source_id'] ?? 'id';
    $destination_ids = $migration_instance->getIdMap()->lookupDestinationIds(
          [$source_id_key => (string) $value]
      );

    if (empty($destination_ids)) {
      return NULL;
    }

    $first = reset($destination_ids);
    if (!is_array($first) || count($first) < 2) {
      return NULL;
    }

    return [
      'target_id' => (int) $first[0],
      'target_revision_id' => (int) $first[1],
    ];
  }

}
