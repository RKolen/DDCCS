<?php

declare(strict_types=1);

namespace Drupal\dnd_migrate\Plugin\migrate\process;

use Drupal\Core\Entity\EntityTypeManagerInterface;
use Drupal\Core\Plugin\ContainerFactoryPluginInterface;
use Drupal\migrate\MigrateExecutableInterface;
use Drupal\migrate\ProcessPluginBase;
use Drupal\migrate\Row;
use Symfony\Component\DependencyInjection\ContainerInterface;

/**
 * Creates the nested ability_scores paragraph hierarchy for a character.
 *
 * Reads six flattened ability score source properties (ability_str,
 * ability_dex, ability_con, ability_int, ability_wis, ability_cha) from the
 * current row and:
 *
 * 1. Looks up the six ability taxonomy terms in the "ability_scores" vocab.
 * 2. Creates one paragraph:ability_score entity per stat.
 * 3. Creates one paragraph:ability_scores entity that references all six.
 * 4. Returns [target_id, target_revision_id] for the wrapper paragraph, ready
 *    for assignment to an entity_reference_revisions field.
 *
 * The plugin receives the Row object directly and does not transform an input
 * value — configure it with source set to any existing key (e.g. "file_id").
 *
 * Example configuration:
 * @code
 * process:
 *   field_ability_scores:
 *     plugin: dnd_ability_scores_paragraph
 *     source: file_id
 * @endcode
 *
 * @MigrateProcessPlugin(
 *   id = "dnd_ability_scores_paragraph",
 *   handle_multiples = FALSE
 * )
 */
final class DndAbilityScoresParagraph extends ProcessPluginBase implements ContainerFactoryPluginInterface {
  /**
   * Map of source property name to ability taxonomy term name.
   */
  private const ABILITY_MAP = [
    'ability_str' => 'Strength',
    'ability_dex' => 'Dexterity',
    'ability_con' => 'Constitution',
    'ability_int' => 'Intelligence',
    'ability_wis' => 'Wisdom',
    'ability_cha' => 'Charisma',
  ];

  /**
   * The entity type manager.
   *
   * @var \Drupal\Core\Entity\EntityTypeManagerInterface
   */
  protected EntityTypeManagerInterface $entityTypeManager;

  /**
   * Constructs a DndAbilityScoresParagraph process plugin.
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
   *   Not used; all data is read from the Row.
   * @param \Drupal\migrate\MigrateExecutableInterface $migrate_executable
   *   The migration executable.
   * @param \Drupal\migrate\Row $row
   *   The current source row.
   * @param string $destination_property
   *   The destination property name.
   *
   * @return array{target_id: int, target_revision_id: int}|null
   *   ERR value for field_ability_scores, or NULL if no scores found.
   */
  public function transform(
    $value,
    MigrateExecutableInterface $migrate_executable,
    Row $row,
    $destination_property,
  ): ?array {
    $paragraph_storage = $this->entityTypeManager->getStorage('paragraph');
    $term_storage      = $this->entityTypeManager->getStorage('taxonomy_term');

    // Resolve taxonomy term IDs once, keyed by ability name.
    $term_ids = [];
    foreach (self::ABILITY_MAP as $term_name) {
      $terms = $term_storage->loadByProperties([
        'vid'  => 'ability_scores',
        'name' => $term_name,
      ]);
      if ($terms !== []) {
        $term_ids[$term_name] = (int) reset($terms)->id();
      }
    }

    // Map from ability name to wrapper field name.
    $ability_field_map = [
      'Strength'     => 'field_strength',
      'Dexterity'    => 'field_dexterity',
      'Constitution' => 'field_constitution',
      'Intelligence' => 'field_intelligence',
      'Wisdom'       => 'field_wisdom',
      'Charisma'     => 'field_charisma',
    ];

    // Build the six ability_score sub-paragraphs, keyed by ability name.
    // Entities are retained (not just IDs) so that the wrapper paragraph can
    // reference them as objects — this allows Drupal to correctly set the
    // parent_type / parent_id / parent_field_name on each sub-paragraph when
    // the wrapper is saved, preventing "cannot be referenced" errors in the UI.
    $sub_entities = [];
    $has_any      = FALSE;

    foreach (self::ABILITY_MAP as $source_key => $term_name) {
      $score = $row->getSourceProperty($source_key);
      if ($score === NULL) {
        continue;
      }
      $has_any = TRUE;

      $tid = $term_ids[$term_name] ?? NULL;

      /** @var \Drupal\paragraphs\Entity\Paragraph $sub */
      $sub = $paragraph_storage->create([
        'type'        => 'ability_score',
        'field_score' => (int) $score,
      ]);

      if ($tid !== NULL) {
        $sub->set('field_ability', ['target_id' => $tid]);
      }

      $sub->save();
      $sub_entities[$term_name] = $sub;
    }

    if (!$has_any) {
      return NULL;
    }

    // Build the wrapper paragraph using entity objects so Drupal's ERR field
    // save sets parent info on each sub-paragraph automatically.
    /** @var \Drupal\paragraphs\Entity\Paragraph $wrapper */
    $wrapper = $paragraph_storage->create(['type' => 'ability_scores']);
    foreach ($ability_field_map as $term_name => $field_name) {
      if (isset($sub_entities[$term_name])) {
        $wrapper->set($field_name, $sub_entities[$term_name]);
      }
    }
    $wrapper->save();

    return [
      'target_id'          => (int) $wrapper->id(),
      'target_revision_id' => (int) $wrapper->getRevisionId(),
    ];
  }

}
