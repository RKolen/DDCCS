<?php

declare(strict_types=1);

namespace Drupal\dnd_migrate\Plugin\migrate\process;

use Drupal\taxonomy\Entity\Term;
use Drupal\Core\Entity\EntityStorageInterface;
use Drupal\Core\Entity\EntityTypeManagerInterface;
use Drupal\Core\Plugin\ContainerFactoryPluginInterface;
use Drupal\migrate\MigrateExecutableInterface;
use Drupal\migrate\ProcessPluginBase;
use Drupal\migrate\Row;
use Symfony\Component\DependencyInjection\ContainerInterface;

/**
 * Creates a class paragraph from dnd_class, subclass, and level source fields.
 *
 * Reads the following source properties from the current Row:
 *   - dnd_class  (string) : D&D class name, looked up in the "class" taxonomy
 *   - subclass   (string) : subclass name, looked up in "subclasses" taxonomy
 *   - level      (int)    : character level.
 *
 * Returns [target_id, target_revision_id] for the created paragraph:class
 * entity, ready for assignment to an entity_reference_revisions field.
 *
 * Taxonomy terms that do not yet exist are created automatically.
 *
 * Example configuration:
 * @code
 * process:
 *   field_class:
 *     plugin: dnd_class_paragraph
 *     source: file_id
 * @endcode
 *
 * @MigrateProcessPlugin(
 *   id = "dnd_class_paragraph",
 *   handle_multiples = FALSE
 * )
 */
final class DndClassParagraph extends ProcessPluginBase implements ContainerFactoryPluginInterface {
  /**
   * The entity type manager.
   *
   * @var \Drupal\Core\Entity\EntityTypeManagerInterface
   */
  protected EntityTypeManagerInterface $entityTypeManager;

  /**
   * Constructs a DndClassParagraph process plugin.
   *
   * @param array<string, mixed> $configuration
   *   Plugin configuration.
   * @param string $plugin_id
   *   Plugin ID.
   * @param mixed $plugin_definition
   *   Plugin definition.
   * @param \Drupal\Core\Entity\EntityTypeManagerInterface $entity_type_manager
   *   The entity type manager.
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
   * @param mixed $value
   *   Not used; data is read directly from the Row.
   * @param \Drupal\migrate\MigrateExecutableInterface $migrate_executable
   *   The migration executable.
   * @param \Drupal\migrate\Row $row
   *   The current source row.
   * @param string $destination_property
   *   The destination property name.
   *
   * @return array{target_id: int, target_revision_id: int}|null
   *   ERR value for the class paragraph field, or NULL if no class found.
   */
  public function transform(
    $value,
    MigrateExecutableInterface $migrate_executable,
    Row $row,
    $destination_property,
  ): ?array {
    $class_name    = (string) ($row->getSourceProperty('dnd_class') ?? '');
    $subclass_name = (string) ($row->getSourceProperty('subclass') ?? '');
    $level         = $row->getSourceProperty('level');

    if ($class_name === '') {
      return NULL;
    }

    $term_storage = $this->entityTypeManager->getStorage('taxonomy_term');

    // Look up or create the class term.
    $class_tid = $this->findOrCreateTerm($term_storage, 'class', $class_name);

    // Look up or create the subclass term if provided.
    $subclass_tid = NULL;
    if ($subclass_name !== '') {
      $subclass_tid = $this->findOrCreateTerm($term_storage, 'subclasses', $subclass_name);
    }

    $paragraph_values = [
      'type'        => 'class',
      'field_class' => ['target_id' => $class_tid],
      'field_level' => is_numeric($level) ? (int) $level : NULL,
    ];

    if ($subclass_tid !== NULL) {
      $paragraph_values['field_subclass_ref'] = ['target_id' => $subclass_tid];
    }

    /** @var \Drupal\paragraphs\Entity\Paragraph $paragraph */
    $paragraph = $this->entityTypeManager->getStorage('paragraph')->create($paragraph_values);
    $paragraph->save();

    return [
      'target_id'          => (int) $paragraph->id(),
      'target_revision_id' => (int) $paragraph->getRevisionId(),
    ];
  }

  /**
   * Find an existing taxonomy term by name or create it.
   *
   * @param \Drupal\Core\Entity\EntityStorageInterface $storage
   *   The taxonomy_term entity storage.
   * @param string $vocabulary
   *   The vocabulary machine name.
   * @param string $name
   *   The term name to find or create.
   *
   * @return int
   *   The term ID.
   */
  private function findOrCreateTerm(
    EntityStorageInterface $storage,
    string $vocabulary,
    string $name,
  ): int {
    $existing = $storage->loadByProperties(['vid' => $vocabulary, 'name' => $name]);
    if ($existing !== []) {
      return (int) reset($existing)->id();
    }

    $term = Term::create(['vid' => $vocabulary, 'name' => $name]);
    $term->save();
    return (int) $term->id();
  }

}
