<?php

declare(strict_types=1);

namespace Drupal\dnd_content\Plugin\GraphQL\DataProducer;

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
 * Creates a spell node, or returns the existing one with that title.
 *
 * Used by the console to store homebrew and official spells imported from
 * the rules wiki. A second create with the same title returns the existing
 * node so an import rerun cannot fill the vault with duplicates.
 */
#[DataProducer(
  id: "create_spell",
  name: new TranslatableMarkup("Create Spell"),
  description: new TranslatableMarkup("Creates a spell node, or returns the existing title."),
  produces: new ContextDefinition(
    data_type: "any",
    label: new TranslatableMarkup("Created spell node"),
  ),
  consumes: [
    "title" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("Spell name"),
    ),
    "level" => new ContextDefinition(
      data_type: "integer",
      label: new TranslatableMarkup("Spell level (0 = cantrip)"),
      required: FALSE,
    ),
    "school" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("School of magic"),
      required: FALSE,
    ),
    "casting_time" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("Casting time"),
      required: FALSE,
    ),
    "spell_range" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("Range"),
      required: FALSE,
    ),
    "components" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("Components"),
      required: FALSE,
    ),
    "duration" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("Duration"),
      required: FALSE,
    ),
    "concentration" => new ContextDefinition(
      data_type: "boolean",
      label: new TranslatableMarkup("Requires concentration"),
      required: FALSE,
    ),
    "ritual" => new ContextDefinition(
      data_type: "boolean",
      label: new TranslatableMarkup("Ritual"),
      required: FALSE,
    ),
    "description" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("Rules text"),
      required: FALSE,
    ),
  ],
)]
final class CreateSpell extends DataProducerPluginBase implements ContainerFactoryPluginInterface {

  /**
   * Canonical school names keyed by a lowercased lookup.
   *
   * @var array<string, string>
   */
  private const SCHOOLS = [
    'abjuration' => 'Abjuration',
    'conjuration' => 'Conjuration',
    'divination' => 'Divination',
    'enchantment' => 'Enchantment',
    'evocation' => 'Evocation',
    'illusion' => 'Illusion',
    'necromancy' => 'Necromancy',
    'transmutation' => 'Transmutation',
  ];

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
    $instance = new static($configuration, $plugin_id, $plugin_definition);
    $instance->entityTypeManager = $container->get('entity_type.manager');
    $instance->currentUser = $container->get('current_user');

    return $instance;
  }

  /**
   * Create the spell node, or return the existing title.
   *
   * @param string $title
   *   Spell name.
   * @param int|null $level
   *   Spell level; 0 is a cantrip.
   * @param string|null $school
   *   School of magic term name.
   * @param string|null $casting_time
   *   Casting time.
   * @param string|null $spell_range
   *   Range.
   * @param string|null $components
   *   Components string.
   * @param string|null $duration
   *   Duration.
   * @param bool|null $concentration
   *   Whether the spell requires concentration.
   * @param bool|null $ritual
   *   Whether the spell can be cast as a ritual.
   * @param string|null $description
   *   Rules text.
   * @param \Drupal\graphql\GraphQL\Execution\FieldContext $context
   *   The GraphQL field execution context.
   *
   * @return \Drupal\node\NodeInterface
   *   The created or existing spell node.
   *
   * @throws \GraphQL\Error\UserError
   *   When the title is blank, permission is denied, or the save fails.
   */
  public function resolve(
    string $title,
    ?int $level,
    ?string $school,
    ?string $casting_time,
    ?string $spell_range,
    ?string $components,
    ?string $duration,
    ?bool $concentration,
    ?bool $ritual,
    ?string $description,
    FieldContext $context,
  ): NodeInterface {
    $name = trim($title);
    if ($name === '') {
      throw new UserError('A spell name is required.');
    }

    if (!$this->currentUser->hasPermission('create spell content')) {
      $context->addCacheableDependency($this->currentUser);
      throw new UserError('You do not have permission to create spells.');
    }

    $existing = $this->findExisting($name);
    if ($existing !== NULL) {
      return $existing;
    }

    $values = [
      'type' => 'spell',
      'title' => $name,
      'status' => 1,
      'field_spell_level' => $level ?? 0,
    ];

    $school_tid = $this->findOrCreateSchool($school);
    if ($school_tid !== NULL) {
      $values['field_spell_school'] = ['target_id' => $school_tid];
    }

    $casting = $casting_time === NULL ? '' : trim($casting_time);
    if ($casting !== '') {
      $values['field_casting_time'] = $casting;
    }
    $range = $spell_range === NULL ? '' : trim($spell_range);
    if ($range !== '') {
      $values['field_spell_range'] = $range;
    }
    $comps = $components === NULL ? '' : trim($components);
    if ($comps !== '') {
      $values['field_spell_components'] = $comps;
    }
    $dur = $duration === NULL ? '' : trim($duration);
    if ($dur !== '') {
      $values['field_spell_duration'] = $dur;
    }
    if ($concentration !== NULL) {
      $values['field_concentration'] = $concentration ? 1 : 0;
    }
    if ($ritual !== NULL) {
      $values['field_ritual'] = $ritual ? 1 : 0;
    }

    $wysiwyg = $this->buildWysiwyg($description ?? '');
    if ($wysiwyg !== NULL) {
      $values['field_description'] = $wysiwyg;
    }

    $node = $this->entityTypeManager->getStorage('node')->create($values);
    $node->save();

    return $node;
  }

  /**
   * Find a spell that already carries this title.
   *
   * @param string $title
   *   The spell name.
   *
   * @return \Drupal\node\NodeInterface|null
   *   The existing spell, or NULL when there is none.
   */
  private function findExisting(string $title): ?NodeInterface {
    $nodes = $this->entityTypeManager->getStorage('node')->loadByProperties([
      'type' => 'spell',
      'title' => $title,
    ]);
    $node = reset($nodes);

    return $node instanceof NodeInterface ? $node : NULL;
  }

  /**
   * Resolve a spell_schools term by name, creating it when missing.
   *
   * @param string|null $school
   *   School name from the caller.
   *
   * @return int|null
   *   Term id, or NULL when no school was given.
   */
  private function findOrCreateSchool(?string $school): ?int {
    $raw = $school === NULL ? '' : trim($school);
    if ($raw === '') {
      return NULL;
    }
    $name = self::SCHOOLS[strtolower($raw)] ?? $raw;
    $storage = $this->entityTypeManager->getStorage('taxonomy_term');
    $existing = $storage->loadByProperties([
      'vid' => 'spell_schools',
      'name' => $name,
    ]);
    if ($existing !== []) {
      $term = reset($existing);
      return (int) $term->id();
    }
    $term = $storage->create(['vid' => 'spell_schools', 'name' => $name]);
    $term->save();
    return (int) $term->id();
  }

  /**
   * Build a wysiwyg paragraph reference for the description.
   *
   * @param string $text
   *   Rules text.
   *
   * @return array{target_id: int, target_revision_id: int}|null
   *   ERR value, or NULL when the text is blank.
   */
  private function buildWysiwyg(string $text): ?array {
    if (trim($text) === '') {
      return NULL;
    }
    /** @var \Drupal\paragraphs\Entity\Paragraph $paragraph */
    $paragraph = $this->entityTypeManager->getStorage('paragraph')->create([
      'type' => 'wysiwyg',
      'field_text' => ['value' => $text, 'format' => 'plain_text'],
    ]);
    $paragraph->save();
    return [
      'target_id' => (int) $paragraph->id(),
      'target_revision_id' => (int) $paragraph->getRevisionId(),
    ];
  }

}
