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
 * Writes the editable profile fields of a character node.
 *
 * The payload is a JSON object keyed by the camelCase names the Gatsby console
 * uses. Only keys present in the payload are written, so the editor can send a
 * partial patch of just the fields the operator touched. Keys absent from
 * ::FIELD_MAP are ignored - that map is the whitelist, and the only thing
 * standing between this mutation and arbitrary field writes.
 *
 * Portrait, voice, and arc-analysis fields are deliberately absent: they are
 * owned by the Portrait Studio, Consultation, and Arc Analysis screens and are
 * written by ::updateCharacter, ::setCharacterPortrait, ::setCharacterImage and
 * ::saveCharacterArc. field_character_type, field_source_character and
 * field_campaign are absent too - moving a character between campaigns or
 * flipping a player character into an NPC is a structural change with its own
 * consequences, not a profile edit.
 *
 * Multi-value text fields are always written with the plain_text format and one
 * value per delta. That is what stops the "<p>Steadfast</p>" wrappers, and the
 * several-traits-in-one-delta values, that formatted-text widgets left behind.
 */
#[DataProducer(
  id: "update_character_profile",
  name: new TranslatableMarkup("Update Character Profile"),
  description: new TranslatableMarkup("Writes the editable profile fields of a character node."),
  produces: new ContextDefinition(
    data_type: "any",
    label: new TranslatableMarkup("Updated character node"),
  ),
  consumes: [
    "id" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("Character node UUID"),
    ),
    "payload" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("JSON-encoded map of profile fields"),
    ),
  ],
)]
final class UpdateCharacterProfile extends DataProducerPluginBase implements ContainerFactoryPluginInterface {

  /**
   * Text format used for every text value this mutation writes.
   */
  private const TEXT_FORMAT = 'plain_text';

  /**
   * The editable fields, keyed by the payload key the console sends.
   *
   * Each entry is [field name, kind, vocabulary]. The vocabulary is present
   * only for the term-reference kinds and is asserted against the resolved
   * term, so a UUID from the wrong vocabulary is rejected rather than written.
   *
   * @var array<string, array{0: string, 1: string, 2?: string}>
   */
  private const FIELD_MAP = [
    // Identity.
    'firstName'   => ['field_first_name', 'string'],
    'lastName'    => ['field_last_name', 'string'],
    'nickname'    => ['field_nickname', 'string'],
    'pronouns'    => ['field_pronouns', 'string'],
    'gender'      => ['field_gender', 'list_string'],
    'role'        => ['field_role', 'string'],
    // Ancestry.
    'species'     => ['field_species', 'term_ref', 'species'],
    'lineage'     => ['field_lineage', 'term_ref', 'lineage'],
    'background'  => ['field_background', 'term_ref', 'backgrounds'],
    // Vitals.
    'level'            => ['field_level', 'int'],
    'maximumHitpoints' => ['field_maximum_hitpoints', 'int'],
    'armorClass'       => ['field_armor_class', 'int'],
    'movementSpeed'    => ['field_movement_speed', 'int'],
    'proficiencyBonus' => ['field_proficiency_bonus', 'int'],
    'gold'             => ['field_gold', 'int'],
    // Roleplay.
    'personalityTraits' => ['field_personality_traits', 'text_list'],
    'ideals'            => ['field_ideals', 'text_list'],
    'bonds'             => ['field_bonds', 'text_list'],
    'flaws'             => ['field_flaws', 'text_list'],
    'personality'       => ['field_personality', 'text_long'],
    'notes'             => ['field_notes', 'text_long'],
    // Story.
    'majorPlotActions'     => ['field_major_plot_actions', 'text_list'],
    'specializedAbilities' => ['field_specialized_abilities', 'text_list'],
    'plotHooks'            => ['field_plot_hooks', 'text_list'],
    'abilities'            => ['field_abilities', 'text_list'],
    // Proficiencies.
    'languages' => ['field_languages', 'term_ref_multi', 'languages'],
    'skills'    => ['field_skills', 'term_ref_multi', 'skills'],
    'tools'     => ['field_tools', 'term_ref_multi', 'tool_profiencies'],
    // Antagonist (NPCs).
    'encounterTactics' => ['field_encounter_tactics', 'text_list'],
    'defeatConditions' => ['field_defeat_conditions', 'text_list'],
    'lairActions'      => ['field_lair_actions', 'text_list'],
    'legendaryActions' => ['field_legendary_actions', 'text_list'],
    'regionalEffects'  => ['field_regional_effects', 'text_list'],
    'recurring'        => ['field_recurring', 'bool'],
    // AI.
    'aiEnabled'      => ['field_ai_enabled', 'bool'],
    'aiModel'        => ['field_ai_model', 'string'],
    'aiTemperature'  => ['field_ai_temperature', 'decimal'],
    'aiMaxTokens'    => ['field_ai_max_tokens', 'int'],
    'aiSystemPrompt' => ['field_ai_system_prompt', 'text_long'],
  ];

  /**
   * The current user.
   *
   * @var \Drupal\Core\Session\AccountInterface
   */
  protected AccountInterface $currentUser;

  /**
   * The entity type manager.
   *
   * @var \Drupal\Core\Entity\EntityTypeManagerInterface
   */
  protected EntityTypeManagerInterface $entityTypeManager;

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
    $instance->currentUser = $container->get('current_user');
    $instance->entityTypeManager = $container->get('entity_type.manager');
    return $instance;
  }

  /**
   * Write the supplied profile fields onto the character.
   *
   * @param string $id
   *   The character node UUID.
   * @param string $payload
   *   JSON object of profile fields to write.
   * @param \Drupal\graphql\GraphQL\Execution\FieldContext $context
   *   The GraphQL field execution context.
   *
   * @return \Drupal\node\NodeInterface
   *   The updated character node.
   *
   * @throws \GraphQL\Error\UserError
   *   When the payload is malformed, the character is not found, permission is
   *   denied, or a written field fails validation.
   */
  public function resolve(string $id, string $payload, FieldContext $context): NodeInterface {
    $data = json_decode($payload, TRUE);
    if (!is_array($data)) {
      throw new UserError('Payload must be a JSON object.');
    }

    $nodes = $this->entityTypeManager
      ->getStorage('node')
      ->loadByProperties(['uuid' => $id, 'type' => 'character']);

    $node = reset($nodes);
    if (!$node instanceof NodeInterface) {
      throw new UserError('Character not found.');
    }

    if (!$node->access('update', $this->currentUser)) {
      $context->addCacheableDependency($this->currentUser);
      throw new UserError('You do not have permission to update this character.');
    }

    $changed = [];

    // The node label is a base field, not part of FIELD_MAP. It is required,
    // so a blank title is rejected rather than silently clearing the name.
    if (array_key_exists('title', $data)) {
      $title = trim((string) $data['title']);
      if ($title === '') {
        throw new UserError('Title cannot be empty.');
      }
      $node->setTitle($title);
      $changed[] = 'title';
    }

    $term_storage = $this->entityTypeManager->getStorage('taxonomy_term');

    foreach (self::FIELD_MAP as $key => $definition) {
      if (!array_key_exists($key, $data)) {
        continue;
      }
      [$field, $kind] = $definition;
      if (!$node->hasField($field)) {
        continue;
      }
      $node->set($field, $this->fieldValue($kind, $data[$key], $definition[2] ?? '', $term_storage));
      $changed[] = $field;
    }

    if ($changed === []) {
      return $node;
    }

    // Only the fields this mutation actually set are validated. Validating the
    // whole node would let unrelated pre-existing damage - a dangling
    // field_equipment_items reference to a deleted item, say - block every
    // edit to a character, including ones that have nothing to do with it.
    $violations = $node->validate()->getByFields($changed);
    if ($violations->count() > 0) {
      throw new UserError((string) $violations->get(0)->getMessage());
    }
    $node->save();

    return $node;
  }

  /**
   * Convert one payload value into the field value Drupal expects.
   *
   * @param string $kind
   *   The kind from ::FIELD_MAP.
   * @param mixed $value
   *   The raw value from the payload.
   * @param string $vocabulary
   *   Target vocabulary, for the term-reference kinds.
   * @param \Drupal\Core\Entity\EntityStorageInterface $term_storage
   *   Taxonomy term storage.
   *
   * @return mixed
   *   The value to hand to NodeInterface::set(). NULL clears the field.
   *
   * @throws \GraphQL\Error\UserError
   *   When a term reference cannot be resolved in its vocabulary.
   */
  private function fieldValue(
    string $kind,
    mixed $value,
    string $vocabulary,
    EntityStorageInterface $term_storage,
  ): mixed {
    return match ($kind) {
      'string', 'list_string' => $this->stringOrNull($value),
      'int' => is_numeric($value) ? (int) $value : NULL,
      'decimal' => is_numeric($value) ? (float) $value : NULL,
      'bool' => (bool) $value,
      'text_long' => $this->textValue($value),
      'text_list' => $this->textList($value),
      'term_ref' => $this->termReference($value, $vocabulary, $term_storage),
      'term_ref_multi' => $this->termReferenceList($value, $vocabulary, $term_storage),
      default => NULL,
    };
  }

  /**
   * Trim a scalar into a string, treating blank as "clear the field".
   *
   * @param mixed $value
   *   The raw value.
   *
   * @return string|null
   *   The trimmed string, or NULL when empty.
   */
  private function stringOrNull(mixed $value): ?string {
    if (!is_scalar($value)) {
      return NULL;
    }
    $trimmed = trim((string) $value);
    return $trimmed === '' ? NULL : $trimmed;
  }

  /**
   * Build a single formatted-text field value.
   *
   * @param mixed $value
   *   The raw value.
   *
   * @return array{value: string, format: string}|null
   *   The field item, or NULL when empty.
   */
  private function textValue(mixed $value): ?array {
    $text = $this->stringOrNull($value);
    return $text === NULL ? NULL : ['value' => $text, 'format' => self::TEXT_FORMAT];
  }

  /**
   * Build a multi-value text field value, one entry per delta.
   *
   * @param mixed $value
   *   A list of strings from the payload.
   *
   * @return array<int, array{value: string, format: string}>
   *   The field items; an empty list clears the field.
   */
  private function textList(mixed $value): array {
    if (!is_array($value)) {
      return [];
    }
    $items = [];
    foreach ($value as $entry) {
      $text = $this->stringOrNull($entry);
      if ($text !== NULL) {
        $items[] = ['value' => $text, 'format' => self::TEXT_FORMAT];
      }
    }
    return $items;
  }

  /**
   * Resolve a single term UUID into an entity-reference field value.
   *
   * @param mixed $value
   *   The term UUID, or NULL/'' to clear the reference.
   * @param string $vocabulary
   *   The vocabulary the term must belong to.
   * @param \Drupal\Core\Entity\EntityStorageInterface $term_storage
   *   Taxonomy term storage.
   *
   * @return array{target_id: int}|null
   *   The reference value, or NULL when cleared.
   *
   * @throws \GraphQL\Error\UserError
   *   When the UUID does not name a term in that vocabulary.
   */
  private function termReference(
    mixed $value,
    string $vocabulary,
    EntityStorageInterface $term_storage,
  ): ?array {
    $uuid = $this->stringOrNull($value);
    if ($uuid === NULL) {
      return NULL;
    }
    return ['target_id' => $this->termId($uuid, $vocabulary, $term_storage)];
  }

  /**
   * Resolve a list of term UUIDs into entity-reference field values.
   *
   * @param mixed $value
   *   A list of term UUIDs.
   * @param string $vocabulary
   *   The vocabulary the terms must belong to.
   * @param \Drupal\Core\Entity\EntityStorageInterface $term_storage
   *   Taxonomy term storage.
   *
   * @return array<int, array{target_id: int}>
   *   The reference values; an empty list clears the field.
   *
   * @throws \GraphQL\Error\UserError
   *   When a UUID does not name a term in that vocabulary.
   */
  private function termReferenceList(
    mixed $value,
    string $vocabulary,
    EntityStorageInterface $term_storage,
  ): array {
    if (!is_array($value)) {
      return [];
    }
    $items = [];
    $seen = [];
    foreach ($value as $entry) {
      $uuid = $this->stringOrNull($entry);
      if ($uuid === NULL || isset($seen[$uuid])) {
        continue;
      }
      $seen[$uuid] = TRUE;
      $items[] = ['target_id' => $this->termId($uuid, $vocabulary, $term_storage)];
    }
    return $items;
  }

  /**
   * Look up a term by UUID and assert its vocabulary.
   *
   * The vocabulary check is the point of resolving by UUID rather than by name:
   * it stops a term id from one vocabulary being written into a field that
   * targets another.
   *
   * @param string $uuid
   *   The term UUID.
   * @param string $vocabulary
   *   The vocabulary the term must belong to.
   * @param \Drupal\Core\Entity\EntityStorageInterface $term_storage
   *   Taxonomy term storage.
   *
   * @return int
   *   The term ID.
   *
   * @throws \GraphQL\Error\UserError
   *   When no such term exists in that vocabulary.
   */
  private function termId(string $uuid, string $vocabulary, EntityStorageInterface $term_storage): int {
    $terms = $term_storage->loadByProperties(['uuid' => $uuid, 'vid' => $vocabulary]);
    $term = reset($terms);
    if (!$term instanceof TermInterface) {
      throw new UserError(sprintf('No %s term found for id %s.', $vocabulary, $uuid));
    }
    return (int) $term->id();
  }

}
