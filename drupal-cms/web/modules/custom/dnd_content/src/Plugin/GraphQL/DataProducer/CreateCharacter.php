<?php

declare(strict_types=1);

namespace Drupal\dnd_content\Plugin\GraphQL\DataProducer;

use Drupal\Core\Entity\EntityStorageInterface;
use Drupal\Core\Entity\EntityTypeManagerInterface;
use Drupal\Core\Plugin\ContainerFactoryPluginInterface;
use Drupal\Core\Plugin\Context\ContextDefinition;
use Drupal\Core\Session\AccountInterface;
use Drupal\Core\StringTranslation\TranslatableMarkup;
use Drupal\graphql\Attribute\DataProducer;
use Drupal\graphql\GraphQL\Execution\FieldContext;
use Drupal\graphql\Plugin\GraphQL\DataProducer\DataProducerPluginBase;
use Drupal\node\NodeInterface;
use GraphQL\Error\UserError;
use Symfony\Component\DependencyInjection\ContainerInterface;

/**
 * Creates a source character node from a derived character payload.
 *
 * The payload is the JSON-encoded character dictionary produced by the Python
 * sidecar's build-from-template endpoint (game_data character shape). This
 * producer constructs the node plus its nested paragraphs (ability scores,
 * class, backstory, spell slots, class-feature references) and flags it as a
 * source character (``field_source_character = TRUE``) with no campaign. A
 * campaign-specific clone is created separately via addCharacterToCampaign.
 */
#[DataProducer(
  id: "create_character",
  name: new TranslatableMarkup("Create Character"),
  description: new TranslatableMarkup("Creates a source character node from a derived payload."),
  produces: new ContextDefinition(
    data_type: "any",
    label: new TranslatableMarkup("Created character node"),
  ),
  consumes: [
    "payload" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("JSON-encoded derived character"),
    ),
  ],
)]
final class CreateCharacter extends DataProducerPluginBase implements ContainerFactoryPluginInterface {

  /**
   * The entity type manager.
   *
   * @var \Drupal\Core\Entity\EntityTypeManagerInterface
   */
  protected EntityTypeManagerInterface $entityTypeManager;

  /**
   * The current user.
   *
   * @var \Drupal\Core\Session\AccountInterface
   */
  protected AccountInterface $currentUser;

  /**
   * Maps the ability_scores wrapper field name to the ability term name.
   */
  private const ABILITY_FIELDS = [
    'field_strength'     => ['Strength', 'strength'],
    'field_dexterity'    => ['Dexterity', 'dexterity'],
    'field_constitution' => ['Constitution', 'constitution'],
    'field_intelligence' => ['Intelligence', 'intelligence'],
    'field_wisdom'       => ['Wisdom', 'wisdom'],
    'field_charisma'     => ['Charisma', 'charisma'],
  ];

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
  ): self {
    $instance = new self($configuration, $plugin_id, $plugin_definition);
    $instance->entityTypeManager = $container->get('entity_type.manager');
    $instance->currentUser = $container->get('current_user');
    return $instance;
  }

  /**
   * Resolves the mutation by creating a source character node.
   *
   * @param string $payload
   *   JSON-encoded derived character dictionary.
   * @param \Drupal\graphql\GraphQL\Execution\FieldContext $context
   *   The GraphQL field execution context.
   *
   * @return \Drupal\node\NodeInterface
   *   The newly created character node.
   *
   * @throws \GraphQL\Error\UserError
   *   When the payload is invalid, permission is denied, or validation fails.
   */
  public function resolve(string $payload, FieldContext $context): NodeInterface {
    $data = json_decode($payload, TRUE);
    if (!is_array($data) || !isset($data['name']) || trim((string) $data['name']) === '') {
      throw new UserError('Invalid character payload: a name is required.');
    }

    if (!$this->currentUser->hasPermission('create character content')) {
      $context->addCacheableDependency($this->currentUser);
      throw new UserError('You do not have permission to create characters.');
    }

    $values = [
      'type'                   => 'character',
      'title'                  => trim((string) $data['name']),
      'status'                 => 1,
      'field_source_character' => TRUE,
      'field_character_type'   => TRUE,
      'field_level'            => $this->intOrNull($data['level'] ?? NULL),
      'field_armor_class'      => $this->intOrNull($data['armor_class'] ?? NULL),
      'field_maximum_hitpoints' => $this->intOrNull($data['max_hit_points'] ?? NULL),
      'field_movement_speed'   => $this->intOrNull($data['movement_speed'] ?? NULL),
      'field_proficiency_bonus' => $this->intOrNull($data['proficiency_bonus'] ?? NULL),
      'field_gold'             => $this->intOrNull($this->gold($data)),
      'field_personality_traits' => $this->stringList($data['personality_traits'] ?? []),
      'field_ideals'           => $this->stringList($data['ideals'] ?? []),
      'field_bonds'            => $this->stringList($data['bonds'] ?? []),
      'field_flaws'            => $this->stringList($data['flaws'] ?? []),
    ];

    $term_storage = $this->entityTypeManager->getStorage('taxonomy_term');
    $this->addTermReference($values, 'field_species', 'species', (string) ($data['species'] ?? ''), $term_storage);
    $this->addTermReference($values, 'field_background', 'backgrounds', (string) ($data['background'] ?? ''), $term_storage);

    $values['field_skills'] = $this->skillReferences($data['skills'] ?? [], $term_storage);

    $ability_scores = $this->buildAbilityScores($data['ability_scores'] ?? [], $term_storage);
    if ($ability_scores !== NULL) {
      $values['field_ability_scores'] = $ability_scores;
    }

    $class = $this->buildClass($data, $term_storage);
    if ($class !== NULL) {
      $values['field_class'] = $class;
    }

    $backstory = $this->buildWysiwyg((string) ($data['backstory'] ?? ''));
    if ($backstory !== NULL) {
      $values['field_backstory'] = $backstory;
    }

    $values['field_spell_slots'] = $this->buildSpellSlots($data['spell_slots'] ?? []);
    $values['field_abilities_ref'] = $this->buildTermReferenceParagraphs(
      $data['class_abilities'] ?? [],
      $term_storage,
    );

    /** @var \Drupal\node\NodeInterface $node */
    $node = $this->entityTypeManager->getStorage('node')->create($values);

    if (!$node->access('create', $this->currentUser)) {
      $context->addCacheableDependency($this->currentUser);
      throw new UserError('You do not have permission to create characters.');
    }

    $violations = $node->validate();
    if ($violations->count() > 0) {
      throw new UserError((string) $violations->get(0)->getMessage());
    }

    $node->save();

    return $node;
  }

  /**
   * Read gold from the payload, tolerating top-level or equipment placement.
   *
   * @param array<string, mixed> $data
   *   Character payload.
   *
   * @return int|null
   *   Gold pieces, or NULL when absent.
   */
  private function gold(array $data): ?int {
    if (isset($data['gold']) && is_numeric($data['gold'])) {
      return (int) $data['gold'];
    }
    $equipment = is_array($data['equipment'] ?? NULL) ? $data['equipment'] : [];
    return isset($equipment['gold']) && is_numeric($equipment['gold']) ? (int) $equipment['gold'] : NULL;
  }

  /**
   * Coerce a value to an integer, returning NULL when not numeric.
   *
   * @param mixed $value
   *   Raw value.
   *
   * @return int|null
   *   Integer value or NULL.
   */
  private function intOrNull(mixed $value): ?int {
    return is_numeric($value) ? (int) $value : NULL;
  }

  /**
   * Convert a list of strings into multi-value text field items.
   *
   * @param mixed $value
   *   Source list.
   *
   * @return array<int, string>
   *   Filtered list of non-empty strings.
   */
  private function stringList(mixed $value): array {
    if (!is_array($value)) {
      return [];
    }
    return array_values(array_filter($value, static fn ($item): bool => is_string($item) && $item !== ''));
  }

  /**
   * Add a single taxonomy term reference to the node values by term name.
   *
   * @param array<string, mixed> $values
   *   Node values being assembled (modified by reference).
   * @param string $field
   *   Destination field name.
   * @param string $vocabulary
   *   Target vocabulary machine name.
   * @param string $name
   *   Term name to resolve or create.
   * @param \Drupal\Core\Entity\EntityStorageInterface $term_storage
   *   Taxonomy term storage.
   */
  private function addTermReference(
    array &$values,
    string $field,
    string $vocabulary,
    string $name,
    EntityStorageInterface $term_storage,
  ): void {
    $name = trim($name);
    if ($name === '') {
      return;
    }
    $values[$field] = ['target_id' => $this->findOrCreateTerm($term_storage, $vocabulary, $name)];
  }

  /**
   * Resolve proficient skill names to skills-vocabulary references.
   *
   * Saving-throw entries (keys ending in " Save") are derived, not skills,
   * and are excluded.
   *
   * @param mixed $skills
   *   Skills mapping (name => details) from the payload.
   * @param \Drupal\Core\Entity\EntityStorageInterface $term_storage
   *   Taxonomy term storage.
   *
   * @return array<int, array{target_id: int}>
   *   Entity reference values for field_skills.
   */
  private function skillReferences(mixed $skills, EntityStorageInterface $term_storage): array {
    if (!is_array($skills)) {
      return [];
    }
    $references = [];
    foreach (array_keys($skills) as $skill_name) {
      $name = (string) $skill_name;
      if ($name === '' || str_ends_with($name, ' Save')) {
        continue;
      }
      $terms = $term_storage->loadByProperties(['vid' => 'skills', 'name' => $name]);
      if ($terms !== []) {
        $references[] = ['target_id' => (int) reset($terms)->id()];
      }
    }
    return $references;
  }

  /**
   * Build the nested ability_scores paragraph hierarchy.
   *
   * @param mixed $scores
   *   Ability scores mapping (ability => score).
   * @param \Drupal\Core\Entity\EntityStorageInterface $term_storage
   *   Taxonomy term storage.
   *
   * @return array{target_id: int, target_revision_id: int}|null
   *   ERR value for field_ability_scores, or NULL when no scores supplied.
   */
  private function buildAbilityScores(mixed $scores, EntityStorageInterface $term_storage): ?array {
    if (!is_array($scores) || $scores === []) {
      return NULL;
    }

    $paragraph_storage = $this->entityTypeManager->getStorage('paragraph');
    /** @var \Drupal\paragraphs\Entity\Paragraph $wrapper */
    $wrapper = $paragraph_storage->create(['type' => 'ability_scores']);
    $has_any = FALSE;

    foreach (self::ABILITY_FIELDS as $field => [$term_name, $score_key]) {
      if (!isset($scores[$score_key]) || !is_numeric($scores[$score_key])) {
        continue;
      }
      $has_any = TRUE;
      /** @var \Drupal\paragraphs\Entity\Paragraph $sub */
      $sub = $paragraph_storage->create([
        'type'        => 'ability_score',
        'field_score' => (int) $scores[$score_key],
      ]);
      $terms = $term_storage->loadByProperties(['vid' => 'ability_scores', 'name' => $term_name]);
      if ($terms !== []) {
        $sub->set('field_ability', ['target_id' => (int) reset($terms)->id()]);
      }
      $sub->save();
      $wrapper->set($field, $sub);
    }

    if (!$has_any) {
      return NULL;
    }

    $wrapper->save();
    return [
      'target_id'          => (int) $wrapper->id(),
      'target_revision_id' => (int) $wrapper->getRevisionId(),
    ];
  }

  /**
   * Build the class paragraph from the payload class and level.
   *
   * @param array<string, mixed> $data
   *   Character payload.
   * @param \Drupal\Core\Entity\EntityStorageInterface $term_storage
   *   Taxonomy term storage.
   *
   * @return array{target_id: int, target_revision_id: int}|null
   *   ERR value for field_class, or NULL when no class supplied.
   */
  private function buildClass(array $data, EntityStorageInterface $term_storage): ?array {
    $class_name = trim((string) ($data['dnd_class'] ?? ''));
    if ($class_name === '') {
      return NULL;
    }

    $paragraph_values = [
      'type'        => 'class',
      'field_class' => ['target_id' => $this->findOrCreateTerm($term_storage, 'class', $class_name)],
      'field_level' => $this->intOrNull($data['level'] ?? NULL),
    ];

    $subclass = trim((string) ($data['subclass'] ?? ''));
    if ($subclass !== '') {
      $paragraph_values['field_subclass_ref'] = [
        'target_id' => $this->findOrCreateTerm($term_storage, 'subclasses', $subclass),
      ];
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
   * Build a wysiwyg paragraph for the backstory text.
   *
   * @param string $text
   *   Backstory text.
   *
   * @return array{target_id: int, target_revision_id: int}|null
   *   ERR value for field_backstory, or NULL when empty.
   */
  private function buildWysiwyg(string $text): ?array {
    if (trim($text) === '') {
      return NULL;
    }
    /** @var \Drupal\paragraphs\Entity\Paragraph $paragraph */
    $paragraph = $this->entityTypeManager->getStorage('paragraph')->create([
      'type'       => 'wysiwyg',
      'field_text' => ['value' => $text, 'format' => 'plain_text'],
    ]);
    $paragraph->save();
    return [
      'target_id'          => (int) $paragraph->id(),
      'target_revision_id' => (int) $paragraph->getRevisionId(),
    ];
  }

  /**
   * Build spell_slot paragraphs from a level-keyed slot map.
   *
   * @param mixed $slots
   *   Mapping of spell level to slot count.
   *
   * @return array<int, array{target_id: int, target_revision_id: int}>
   *   ERR values for field_spell_slots.
   */
  private function buildSpellSlots(mixed $slots): array {
    if (!is_array($slots) || $slots === []) {
      return [];
    }
    $paragraph_storage = $this->entityTypeManager->getStorage('paragraph');
    $references = [];
    foreach ($slots as $level => $count) {
      if (!is_numeric($level) || !is_numeric($count)) {
        continue;
      }
      /** @var \Drupal\paragraphs\Entity\Paragraph $paragraph */
      $paragraph = $paragraph_storage->create([
        'type'                        => 'spell_slot',
        'field_spell_level'           => (int) $level,
        'field_spell_slots_total'     => (int) $count,
        'field_spell_slots_available' => (int) $count,
      ]);
      $paragraph->save();
      $references[] = [
        'target_id'          => (int) $paragraph->id(),
        'target_revision_id' => (int) $paragraph->getRevisionId(),
      ];
    }
    return $references;
  }

  /**
   * Build ability_reference paragraphs for class-feature names.
   *
   * @param mixed $names
   *   Class feature names.
   * @param \Drupal\Core\Entity\EntityStorageInterface $term_storage
   *   Taxonomy term storage.
   *
   * @return array<int, array{target_id: int, target_revision_id: int}>
   *   ERR values for field_abilities_ref.
   */
  private function buildTermReferenceParagraphs(mixed $names, EntityStorageInterface $term_storage): array {
    if (!is_array($names) || $names === []) {
      return [];
    }
    $paragraph_storage = $this->entityTypeManager->getStorage('paragraph');
    $references = [];
    foreach ($names as $name) {
      if (!is_string($name) || $name === '') {
        continue;
      }
      $tid = $this->findOrCreateTerm($term_storage, 'abilities', $name);
      /** @var \Drupal\paragraphs\Entity\Paragraph $paragraph */
      $paragraph = $paragraph_storage->create([
        'type'          => 'ability_reference',
        'field_ability' => ['target_id' => $tid],
      ]);
      $paragraph->save();
      $references[] = [
        'target_id'          => (int) $paragraph->id(),
        'target_revision_id' => (int) $paragraph->getRevisionId(),
      ];
    }
    return $references;
  }

  /**
   * Find a taxonomy term by name, creating it when absent.
   *
   * @param \Drupal\Core\Entity\EntityStorageInterface $storage
   *   Taxonomy term storage.
   * @param string $vocabulary
   *   Vocabulary machine name.
   * @param string $name
   *   Term name.
   *
   * @return int
   *   The term ID.
   */
  private function findOrCreateTerm(EntityStorageInterface $storage, string $vocabulary, string $name): int {
    $existing = $storage->loadByProperties(['vid' => $vocabulary, 'name' => $name]);
    if ($existing !== []) {
      return (int) reset($existing)->id();
    }
    $term = $storage->create(['vid' => $vocabulary, 'name' => $name]);
    $term->save();
    return (int) $term->id();
  }

}
