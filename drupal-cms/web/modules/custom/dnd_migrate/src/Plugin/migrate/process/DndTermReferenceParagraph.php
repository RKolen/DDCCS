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
 * Converts a single taxonomy term name into a paragraph entity reference.
 *
 * This is a generic, configurable process plugin called once per source
 * element (handle_multiples = FALSE). Drupal migrate iterates a source array
 * and calls transform() with one term name string per invocation.
 *
 * Required configuration:
 *   paragraph_type: The paragraph bundle to create (e.g. 'spell_reference').
 *   field_name: The paragraph field that holds the taxonomy term reference
 *               (e.g. 'field_spell').
 *   vocabulary: The taxonomy vocabulary machine name to search (e.g. 'spells').
 *
 * Example configuration for Known Spells:
 * @code
 * process:
 *   field_spells_ref:
 *     plugin: dnd_term_reference_paragraph
 *     source: known_spells
 *     paragraph_type: spell_reference
 *     field_name: field_spell
 *     vocabulary: spells
 * @endcode
 *
 * @MigrateProcessPlugin(
 *   id = "dnd_term_reference_paragraph",
 *   handle_multiples = FALSE
 * )
 */
final class DndTermReferenceParagraph extends ProcessPluginBase implements ContainerFactoryPluginInterface {
  /**
   * The entity type manager.
   *
   * @var \Drupal\Core\Entity\EntityTypeManagerInterface
   */
  protected EntityTypeManagerInterface $entityTypeManager;

  /**
   * Constructs a DndTermReferenceParagraph instance.
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
   * Receives one taxonomy term name string at a time (migrate iterates the
   * source array). Looks up the term in the configured vocabulary, creates a
   * paragraph of the configured type, and returns its entity reference values.
   *
   * @param mixed $value
   *   A single taxonomy term name string.
   * @param \Drupal\migrate\MigrateExecutableInterface $migrate_executable
   *   The migration executable.
   * @param \Drupal\migrate\Row $row
   *   The current source row.
   * @param string $destination_property
   *   The destination property name.
   *
   * @return array{target_id: int, target_revision_id: int}|null
   *   Paragraph entity reference value, or NULL when the pipeline is stopped.
   */
  public function transform(
    $value,
    MigrateExecutableInterface $migrate_executable,
    Row $row,
    $destination_property,
  ): ?array {
    if (!is_string($value) || $value === '') {
      $this->stopPipeline();
      return NULL;
    }

    $vocabulary     = (string) ($this->configuration['vocabulary'] ?? '');
    $paragraph_type = (string) ($this->configuration['paragraph_type'] ?? '');
    $field_name     = (string) ($this->configuration['field_name'] ?? '');

    $terms = $this->entityTypeManager->getStorage('taxonomy_term')->loadByProperties([
      'vid'  => $vocabulary,
      'name' => $value,
    ]);

    if (empty($terms)) {
      $this->stopPipeline();
      return NULL;
    }

    $term = reset($terms);
    /** @var \Drupal\paragraphs\Entity\Paragraph $paragraph */
    $paragraph = $this->entityTypeManager->getStorage('paragraph')->create([
      'type'      => $paragraph_type,
      $field_name => [['target_id' => $term->id()]],
    ]);
    $paragraph->save();

    return [
      'target_id'          => (int) $paragraph->id(),
      'target_revision_id' => (int) $paragraph->getRevisionId(),
    ];
  }

}
