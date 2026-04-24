<?php

declare(strict_types=1);

namespace Drupal\dnd_migrate\Plugin\migrate\process;

use Drupal\migrate\MigrateExecutableInterface;
use Drupal\migrate\ProcessPluginBase;
use Drupal\migrate\Row;
use Drupal\Core\Entity\EntityTypeManagerInterface;
use Drupal\Core\Plugin\ContainerFactoryPluginInterface;
use Symfony\Component\DependencyInjection\ContainerInterface;

/**
 * Looks up entity IDs from a flat array of entity title strings.
 *
 * Accepts a PHP array of title strings and returns an array of entity
 * reference values suitable for a multi-value entity reference field.
 * Titles that do not match any entity of the configured type and bundle
 * are silently skipped.
 *
 * Example configuration:
 * @code
 * process:
 *   field_magic_items_ref:
 *     plugin: dnd_array_entity_lookup
 *     source: magic_items
 *     entity_type: node
 *     bundle: item
 *     search_key: title
 * @endcode
 *
 * @MigrateProcessPlugin(
 *   id = "dnd_array_entity_lookup",
 *   handle_multiples = TRUE
 * )
 */
final class DndArrayEntityLookup extends ProcessPluginBase implements ContainerFactoryPluginInterface {
  /**
   * The entity type manager.
   *
   * @var \Drupal\Core\Entity\EntityTypeManagerInterface
   */
  protected EntityTypeManagerInterface $entityTypeManager;

  /**
   * Constructs a DndArrayEntityLookup process plugin instance.
   *
   * @param array<string, mixed> $configuration
   *   Plugin configuration.
   * @param string $plugin_id
   *   Plugin ID.
   * @param mixed $plugin_definition
   *   Plugin definition.
   * @param \Drupal\Core\Entity\EntityTypeManagerInterface $entity_type_manager
   *   The entity type manager service.
   */
  public function __construct(
    array $configuration,
    string $plugin_id,
    mixed $plugin_definition,
    EntityTypeManagerInterface $entity_type_manager,
  ) {
    parent::__construct($configuration, $plugin_id, $plugin_definition);
    $this->entityTypeManager = $entity_type_manager;
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
          $container->get('entity_type.manager'),
      );
  }

  /**
   * {@inheritdoc}
   *
   * @param mixed $value
   *   A flat array of entity title strings.
   * @param \Drupal\migrate\MigrateExecutableInterface $migrate_executable
   *   The migration executable.
   * @param \Drupal\migrate\Row $row
   *   The current source row.
   * @param string $destination_property
   *   The destination property name.
   *
   * @return array<int, array{target_id: int}>
   *   Array of entity reference values for the multi-value field.
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

    $entity_type = (string) ($this->configuration['entity_type'] ?? 'node');
    $bundle = (string) ($this->configuration['bundle'] ?? '');
    $search_key = (string) ($this->configuration['search_key'] ?? 'title');

    $storage = $this->entityTypeManager->getStorage($entity_type);
    $results = [];

    foreach ($value as $title) {
      if (!is_string($title) || $title === '') {
        continue;
      }

      $query = $storage->getQuery()
        ->condition($search_key, $title)
        ->accessCheck(FALSE)
        ->range(0, 1);

      if ($bundle !== '') {
        $raw_key = $this->entityTypeManager
          ->getDefinition($entity_type)
          ->getKey('bundle');
        $bundle_key = is_string($raw_key) ? $raw_key : '';
        if ($bundle_key !== '') {
          $query->condition($bundle_key, $bundle);
        }
      }

      $entity_ids = $query->execute();
      if (empty($entity_ids)) {
        continue;
      }

      $results[] = ['target_id' => (int) reset($entity_ids)];
    }

    return $results;
  }

}
