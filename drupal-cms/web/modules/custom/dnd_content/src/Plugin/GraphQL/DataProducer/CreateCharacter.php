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
use Drupal\taxonomy\TermInterface;
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
   * Default Piper TTS voice applied to new characters.
   *
   * Matches the project's canonical default voice used by existing
   * characters. Speed and pitch default to 1.0 and 0 respectively.
   */
  private const DEFAULT_VOICE_ID = 'en_US-ryan-low';

  /**
   * Game edition stamped on abilities created during character creation.
   */
  private const ABILITY_EDITION = 'D&D 5.5e (2024)';

  /**
   * Game edition stamped on backgrounds defined via the homebrew modal.
   */
  private const HOMEBREW_EDITION = 'Homebrew';

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
      // Sensible AI/voice defaults so a new character works out of the box.
      // Model, temperature, and max_tokens are intentionally left unset so they
      // inherit the global AI configuration rather than hardcoding values here.
      'field_ai_enabled'       => TRUE,
      'field_ai_system_prompt' => [
        'value'  => $this->defaultSystemPrompt($data),
        'format' => 'plain_text',
      ],
      'field_voice_speed'      => 1.0,
      'field_voice_pitch'      => 0,
    ];

    $this->addStringValue($values, 'field_first_name', $data['first_name'] ?? NULL);
    $this->addStringValue($values, 'field_last_name', $data['last_name'] ?? NULL);
    $this->addStringValue($values, 'field_nickname', $data['nickname'] ?? NULL);

    $term_storage = $this->entityTypeManager->getStorage('taxonomy_term');
    $this->addTermReference($values, 'field_species', 'species', (string) ($data['species'] ?? ''), $term_storage);
    $this->addTermReference($values, 'field_lineage', 'lineage', (string) ($data['subspecies'] ?? ''), $term_storage);
    $this->addBackground($values, $data, $term_storage);
    $this->addTermReference($values, 'field_voice_id_ref', 'voice_ids', self::DEFAULT_VOICE_ID, $term_storage);

    // Apply background grants: granted skills merge into the character's chosen
    // skills, the origin feat becomes a feat reference, and the equipment
    // package is attached as item nodes.
    $bgGrants = is_array($data['background_definition'] ?? NULL) ? $data['background_definition'] : [];
    $skillNames = array_keys(is_array($data['skills'] ?? NULL) ? $data['skills'] : []);
    if (is_array($bgGrants['skills'] ?? NULL)) {
      $skillNames = array_merge($skillNames, $bgGrants['skills']);
    }
    $values['field_skills'] = $this->skillReferences($skillNames, $term_storage);

    $toolNames = is_array($data['tools'] ?? NULL) ? $data['tools'] : [];
    if (is_array($bgGrants['tools'] ?? NULL)) {
      $toolNames = array_merge($toolNames, $bgGrants['tools']);
    }
    $values['field_tools'] = $this->termRefList($toolNames, 'tool_profiencies', $term_storage);

    $values['field_feats_ref'] = $this->buildFeatReferences(
      (string) ($bgGrants['feat'] ?? ''),
      (string) ($bgGrants['feat_description'] ?? ''),
      $term_storage,
    );
    // Prefer the wizard's resolved equipment selection (class + background A/B
    // choices); fall back to the background package for older callers.
    $equipmentNames = is_array($data['equipment'] ?? NULL) && $data['equipment'] !== []
      ? $data['equipment']
      : ($bgGrants['equipment'] ?? NULL);
    if (is_array($equipmentNames) && $equipmentNames !== []) {
      $values['field_equipment_items'] = $this->itemNodeRefs(
        $equipmentNames, $term_storage, $this->equipmentDescriptions($data),
      );
    }

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
    $values['field_abilities_ref'] = $this->buildAbilityParagraphs(
      $data['abilities'] ?? [],
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
   * Build a sensible default AI system prompt from the character payload.
   *
   * Derived from the character's own name, class, and level so it is useful
   * immediately without hardcoding any model configuration.
   *
   * @param array<string, mixed> $data
   *   Character payload.
   *
   * @return string
   *   A plain-text system prompt.
   */
  private function defaultSystemPrompt(array $data): string {
    $name = trim((string) $data['name']);
    $class = trim((string) ($data['dnd_class'] ?? ''));
    $level = $this->intOrNull($data['level'] ?? NULL);
    if ($class !== '' && $level !== NULL) {
      $descriptor = sprintf('a level %d %s', $level, $class);
    }
    elseif ($class !== '') {
      $descriptor = 'a ' . $class;
    }
    else {
      $descriptor = 'an adventurer';
    }
    return sprintf(
      'You are %s, %s. Stay in character, speaking and acting as they would.',
      $name,
      $descriptor,
    );
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
   * Add a trimmed string value to the node values when non-empty.
   *
   * @param array<string, mixed> $values
   *   Node values being assembled (modified by reference).
   * @param string $field
   *   Destination field name.
   * @param mixed $value
   *   Raw value; set only when it is a non-empty string after trimming.
   */
  private function addStringValue(array &$values, string $field, mixed $value): void {
    $trimmed = trim((string) ($value ?? ''));
    if ($trimmed !== '') {
      $values[$field] = $trimmed;
    }
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
   * Resolve a flat list of skill names to skills-vocabulary references.
   *
   * Saving-throw entries (ending in " Save") are derived, not skills, and are
   * excluded. Duplicate and unknown names are dropped.
   *
   * @param array<int, mixed> $names
   *   Skill names (e.g. the character's chosen skills plus background grants).
   * @param \Drupal\Core\Entity\EntityStorageInterface $term_storage
   *   Taxonomy term storage.
   *
   * @return array<int, array{target_id: int}>
   *   Entity reference values for field_skills.
   */
  private function skillReferences(array $names, EntityStorageInterface $term_storage): array {
    $references = [];
    $seen = [];
    foreach ($names as $candidate) {
      $name = trim((string) $candidate);
      if ($name === '' || str_ends_with($name, ' Save') || isset($seen[$name])) {
        continue;
      }
      $terms = $term_storage->loadByProperties(['vid' => 'skills', 'name' => $name]);
      if ($terms !== []) {
        $seen[$name] = TRUE;
        $references[] = ['target_id' => (int) reset($terms)->id()];
      }
    }
    return $references;
  }

  /**
   * Build a feat_reference paragraph for a feat (e.g. a background's feat).
   *
   * @param string $name
   *   Feat name; empty yields no reference.
   * @param string $description
   *   Feat rules text, used to backfill the feat term when missing.
   * @param \Drupal\Core\Entity\EntityStorageInterface $term_storage
   *   Taxonomy term storage.
   *
   * @return array<int, array{target_id: int, target_revision_id: int}>
   *   ERR values for field_feats_ref.
   */
  private function buildFeatReferences(string $name, string $description, EntityStorageInterface $term_storage): array {
    $clean = trim($name);
    if ($clean === '') {
      return [];
    }
    $tid = $this->findOrCreateFeat($term_storage, $clean, $description);
    /** @var \Drupal\paragraphs\Entity\Paragraph $paragraph */
    $paragraph = $this->entityTypeManager->getStorage('paragraph')->create([
      'type'       => 'feat_reference',
      'field_feat' => ['target_id' => $tid],
    ]);
    $paragraph->save();
    return [[
      'target_id'          => (int) $paragraph->id(),
      'target_revision_id' => (int) $paragraph->getRevisionId(),
    ]];
  }

  /**
   * Find a feat term by name, backfilling its description when empty.
   *
   * Updates existing feats (created bare by migrations) with their rules text
   * resolved from the wiki, and stamps the 2024 edition.
   *
   * @param \Drupal\Core\Entity\EntityStorageInterface $storage
   *   Taxonomy term storage.
   * @param string $name
   *   Feat name.
   * @param string $description
   *   Feat rules text; backfilled only when the term has none.
   *
   * @return int
   *   The feat term ID.
   */
  private function findOrCreateFeat(EntityStorageInterface $storage, string $name, string $description): int {
    $existing = $storage->loadByProperties(['vid' => 'feats', 'name' => $name]);
    if ($existing !== []) {
      $term = reset($existing);
      assert($term instanceof TermInterface);
      if ($description !== '' && $term->get('field_feat_description')->isEmpty()) {
        $term->set('field_feat_description', ['value' => $description, 'format' => 'plain_text']);
        $editionTid = $this->editionTermId($storage, self::ABILITY_EDITION);
        if ($editionTid !== NULL && $term->get('field_edition')->isEmpty()) {
          $term->set('field_edition', ['target_id' => $editionTid]);
        }
        $term->save();
      }
      return (int) $term->id();
    }

    $values = ['vid' => 'feats', 'name' => $name];
    if ($description !== '') {
      $values['field_feat_description'] = ['value' => $description, 'format' => 'plain_text'];
    }
    $editionTid = $this->editionTermId($storage, self::ABILITY_EDITION);
    if ($editionTid !== NULL) {
      $values['field_edition'] = ['target_id' => $editionTid];
    }
    $term = $storage->create($values);
    $term->save();
    return (int) $term->id();
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
   * Build ability_reference paragraphs from resolved abilities.
   *
   * Each ability is a dict ({name, description, level, source_type}) resolved
   * from the rules wiki. The ability term is created on first use with its
   * rules text and metadata, then reused on subsequent characters.
   *
   * @param mixed $abilities
   *   Resolved ability dicts.
   * @param \Drupal\Core\Entity\EntityStorageInterface $term_storage
   *   Taxonomy term storage.
   *
   * @return array<int, array{target_id: int, target_revision_id: int}>
   *   ERR values for field_abilities_ref.
   */
  private function buildAbilityParagraphs(mixed $abilities, EntityStorageInterface $term_storage): array {
    if (!is_array($abilities) || $abilities === []) {
      return [];
    }
    $paragraph_storage = $this->entityTypeManager->getStorage('paragraph');
    $references = [];
    foreach ($abilities as $ability) {
      if (!is_array($ability)) {
        continue;
      }
      $name = trim((string) ($ability['name'] ?? ''));
      if ($name === '') {
        continue;
      }
      $tid = $this->upsertAbilityTerm($term_storage, $ability, $name);
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
   * Find an ability term by name, creating it with metadata when absent.
   *
   * @param \Drupal\Core\Entity\EntityStorageInterface $storage
   *   Taxonomy term storage.
   * @param array<string, mixed> $ability
   *   Resolved ability dict ({name, description, level, source_type}).
   * @param string $name
   *   Ability name (already trimmed and non-empty).
   *
   * @return int
   *   The ability term ID.
   */
  private function upsertAbilityTerm(EntityStorageInterface $storage, array $ability, string $name): int {
    $existing = $storage->loadByProperties(['vid' => 'abilities', 'name' => $name]);
    if ($existing !== []) {
      return (int) reset($existing)->id();
    }

    $values = ['vid' => 'abilities', 'name' => $name];

    $description = trim((string) ($ability['description'] ?? ''));
    if ($description !== '') {
      $values['field_ability_description'] = ['value' => $description, 'format' => 'plain_text'];
    }

    $sourceType = trim((string) ($ability['source_type'] ?? ''));
    if ($sourceType !== '') {
      $values['field_ability_source_type'] = $sourceType;
    }

    if (isset($ability['level']) && is_numeric($ability['level'])) {
      $values['field_ability_level'] = (int) $ability['level'];
    }

    $editionTid = $this->editionTermId($storage, self::ABILITY_EDITION);
    if ($editionTid !== NULL) {
      $values['field_edition'] = ['target_id' => $editionTid];
    }

    $term = $storage->create($values);
    $term->save();
    return (int) $term->id();
  }

  /**
   * Resolve a game-edition term ID by name.
   *
   * @param \Drupal\Core\Entity\EntityStorageInterface $storage
   *   Taxonomy term storage.
   * @param string $name
   *   Edition term name (e.g. "D&D 5.5e (2024)" or "Homebrew").
   *
   * @return int|null
   *   The edition term ID, or NULL when the term is absent.
   */
  private function editionTermId(EntityStorageInterface $storage, string $name): ?int {
    $existing = $storage->loadByProperties(['vid' => 'game_edition', 'name' => $name]);
    return $existing === [] ? NULL : (int) reset($existing)->id();
  }

  /**
   * Set the character's background, populating the term from a definition.
   *
   * When the payload includes a background_definition, the background term is
   * upserted with its granted skills, tools, ability options, origin feat,
   * gold, and equipment. A newly created term (the wizard's "not on the list"
   * path) is stamped Homebrew; an existing-but-empty official term (resolved
   * from the rules wiki) is stamped with the 2024 edition. Without a
   * definition, an existing background term is simply referenced.
   *
   * @param array<string, mixed> $values
   *   Node values being assembled (modified by reference).
   * @param array<string, mixed> $data
   *   Character payload.
   * @param \Drupal\Core\Entity\EntityStorageInterface $term_storage
   *   Taxonomy term storage.
   */
  private function addBackground(array &$values, array $data, EntityStorageInterface $term_storage): void {
    $name = trim((string) ($data['background'] ?? ''));
    if ($name === '') {
      return;
    }
    $definition = $data['background_definition'] ?? NULL;
    if (!is_array($definition)) {
      $this->addTermReference($values, 'field_background', 'backgrounds', $name, $term_storage);
      return;
    }
    $values['field_background'] = [
      'target_id' => $this->upsertBackground(
        $name, $definition, $term_storage, $this->equipmentDescriptions($data),
      ),
    ];
  }

  /**
   * Create or update a background term from a definition.
   *
   * @param string $name
   *   Background name.
   * @param array<string, mixed> $definition
   *   Definition with skills, tools, ability options, feat, gold, equipment.
   * @param \Drupal\Core\Entity\EntityStorageInterface $term_storage
   *   Taxonomy term storage.
   * @param array<string, array{description?: string, item_type?: string}> $descriptions
   *   Resolved catalogue data keyed by item name (description + type).
   *
   * @return int
   *   The background term ID.
   */
  private function upsertBackground(string $name, array $definition, EntityStorageInterface $term_storage, array $descriptions = []): int {
    $existing = $term_storage->loadByProperties(['vid' => 'backgrounds', 'name' => $name]);
    $isNew = $existing === [];
    $term = $isNew ? $term_storage->create(['vid' => 'backgrounds', 'name' => $name]) : reset($existing);
    assert($term instanceof TermInterface);

    // A new term is homebrew. An existing-but-empty term is an official
    // background being populated from the rules wiki (stamped 2024). An
    // existing, already-populated term is reused untouched.
    if (!$isNew && !$term->get('field_skills')->isEmpty()) {
      return (int) $term->id();
    }

    $term->set('field_skills', $this->termRefList($definition['skills'] ?? [], 'skills', $term_storage));
    $term->set('field_tools', $this->termRefList($definition['tools'] ?? [], 'tool_profiencies', $term_storage));
    $term->set('field_ability_options', $this->termRefList($definition['abilities'] ?? [], 'ability_scores', $term_storage));

    $feat = trim((string) ($definition['feat'] ?? ''));
    $term->set('field_feat', $feat === '' ? NULL : [
      'target_id' => $this->findOrCreateFeat($term_storage, $feat, (string) ($definition['feat_description'] ?? '')),
    ]);

    $term->set('field_gold', $this->intOrNull($definition['gold'] ?? NULL));
    $term->set('field_equipment_items', $this->itemNodeRefs($definition['equipment'] ?? [], $term_storage, $descriptions));

    $edition = $isNew ? self::HOMEBREW_EDITION : self::ABILITY_EDITION;
    $editionTid = $this->editionTermId($term_storage, $edition);
    if ($editionTid !== NULL) {
      $term->set('field_edition', ['target_id' => $editionTid]);
    }

    $term->save();
    return (int) $term->id();
  }

  /**
   * Resolve a list of term names to reference values within a vocabulary.
   *
   * @param mixed $names
   *   List of term names.
   * @param string $vocabulary
   *   Vocabulary machine name.
   * @param \Drupal\Core\Entity\EntityStorageInterface $term_storage
   *   Taxonomy term storage.
   *
   * @return array<int, array{target_id: int}>
   *   Entity reference values.
   */
  private function termRefList(mixed $names, string $vocabulary, EntityStorageInterface $term_storage): array {
    if (!is_array($names)) {
      return [];
    }
    $refs = [];
    $seen = [];
    foreach ($names as $name) {
      $clean = trim((string) $name);
      if ($clean !== '' && !isset($seen[$clean])) {
        $seen[$clean] = TRUE;
        $refs[] = ['target_id' => $this->findOrCreateTerm($term_storage, $vocabulary, $clean)];
      }
    }
    return $refs;
  }

  /**
   * Resolve equipment names to item node references, creating items when new.
   *
   * New items are created with their type (taken from the resolved catalogue
   * when available, otherwise inferred from the name), a rules-wiki description
   * (when one was resolved), and the 2024 edition; existing items are reused
   * untouched.
   *
   * @param mixed $names
   *   List of item names.
   * @param \Drupal\Core\Entity\EntityStorageInterface $term_storage
   *   Taxonomy term storage (used to resolve the edition term).
   * @param array<string, array{description?: string, item_type?: string}> $descriptions
   *   Resolved catalogue data keyed by item name (description + type).
   *
   * @return array<int, array{target_id: int}>
   *   Entity reference values pointing at item nodes.
   */
  private function itemNodeRefs(mixed $names, EntityStorageInterface $term_storage, array $descriptions = []): array {
    if (!is_array($names)) {
      return [];
    }
    $node_storage = $this->entityTypeManager->getStorage('node');
    $editionTid = $this->editionTermId($term_storage, self::ABILITY_EDITION);
    $refs = [];
    $seen = [];
    foreach ($names as $name) {
      $clean = trim((string) $name);
      if ($clean === '' || isset($seen[$clean])) {
        continue;
      }
      $seen[$clean] = TRUE;
      $existing = $node_storage->loadByProperties(['type' => 'item', 'title' => $clean]);
      if ($existing !== []) {
        $refs[] = ['target_id' => (int) reset($existing)->id()];
        continue;
      }
      $info = is_array($descriptions[$clean] ?? NULL) ? $descriptions[$clean] : [];
      $catalogType = trim((string) ($info['item_type'] ?? ''));
      $itemValues = [
        'type'            => 'item',
        'title'           => $clean,
        'status'          => 1,
        'field_item_type' => $catalogType !== '' ? $catalogType : $this->inferItemType($clean),
      ];
      $description = $this->buildWysiwyg((string) ($info['description'] ?? ''));
      if ($description !== NULL) {
        $itemValues['field_description'] = $description;
      }
      if ($editionTid !== NULL) {
        $itemValues['field_edition'] = ['target_id' => $editionTid];
      }
      $item = $node_storage->create($itemValues);
      $item->save();
      $refs[] = ['target_id' => (int) $item->id()];
    }
    return $refs;
  }

  /**
   * Extract the resolved equipment description map from the payload.
   *
   * @param array<string, mixed> $data
   *   Character payload.
   *
   * @return array<string, array{description?: string, item_type?: string}>
   *   Catalogue data keyed by item name, or an empty map when absent.
   */
  private function equipmentDescriptions(array $data): array {
    $map = $data['equipment_descriptions'] ?? NULL;
    if (!is_array($map)) {
      return [];
    }
    $result = [];
    foreach ($map as $name => $info) {
      if (is_string($name) && is_array($info)) {
        $result[$name] = $info;
      }
    }
    return $result;
  }

  /**
   * Infer an item's type (weapon/armor/item) from its name.
   *
   * @param string $name
   *   Item name.
   *
   * @return string
   *   One of "weapon", "armor", or "item" (the gear default).
   */
  private function inferItemType(string $name): string {
    $lower = strtolower($name);
    $weapons = [
      'sword', 'dagger', 'axe', 'bow', 'crossbow', 'mace', 'spear', 'rapier',
      'hammer', 'club', 'flail', 'glaive', 'halberd', 'javelin', 'lance', 'maul',
      'pike', 'quarterstaff', 'scimitar', 'sickle', 'trident', 'whip', 'dart',
      'sling', 'morningstar', 'war pick', 'blowgun', 'net',
    ];
    $armors = ['armor', 'armour', 'shield', 'mail', 'plate', 'breastplate', 'cuirass'];
    foreach ($weapons as $weapon) {
      if (str_contains($lower, $weapon)) {
        return 'weapon';
      }
    }
    foreach ($armors as $armor) {
      if (str_contains($lower, $armor)) {
        return 'armor';
      }
    }
    return 'item';
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
