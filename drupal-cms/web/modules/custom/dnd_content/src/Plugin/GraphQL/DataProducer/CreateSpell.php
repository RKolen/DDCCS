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
use Drupal\taxonomy\TermInterface;
use GraphQL\Error\UserError;
use Symfony\Component\DependencyInjection\ContainerInterface;

/**
 * Creates a spells-vocabulary term, or fills an existing stub.
 *
 * Used by the console to store homebrew and official spells imported from
 * the rules wiki. A second create with the same name (case and punctuation
 * ignored) returns the existing term so an import cannot duplicate the vault.
 * Empty fields on a stub are filled; non-empty fields are left alone.
 */
#[DataProducer(
  id: "create_spell",
  name: new TranslatableMarkup("Create Spell"),
  description: new TranslatableMarkup("Creates a spells term, or returns the existing name."),
  produces: new ContextDefinition(
    data_type: "any",
    label: new TranslatableMarkup("Created spell term"),
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
   * Create the spell term, or fill empty fields on the existing name.
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
   * @return \Drupal\taxonomy\TermInterface
   *   The created or existing spells term.
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
  ): TermInterface {
    $name = trim($title);
    if ($name === '') {
      throw new UserError('A spell name is required.');
    }

    if (!$this->currentUser->hasPermission('create terms in spells')) {
      $context->addCacheableDependency($this->currentUser);
      throw new UserError('You do not have permission to create spells.');
    }

    $incoming = [
      'level' => $level,
      'school' => $school,
      'casting_time' => $casting_time,
      'spell_range' => $spell_range,
      'components' => $components,
      'duration' => $duration,
      'concentration' => $concentration,
      'ritual' => $ritual,
      'description' => $description,
    ];

    $existing = $this->findExisting($name);
    if ($existing !== NULL) {
      $this->fillEmpty($existing, $incoming);
      return $existing;
    }

    $values = [
      'vid' => 'spells',
      'name' => $name,
      'status' => 1,
      'field_spell_level' => $level ?? 0,
    ];
    $this->applyIncoming($values, $incoming);

    $term = $this->entityTypeManager->getStorage('taxonomy_term')->create($values);
    $term->save();

    return $term;
  }

  /**
   * Find a spells term that already carries this name.
   *
   * Matching is case-insensitive and ignores punctuation so a wiki import
   * of "Melf's Acid Arrow" hits an existing "Melfs Acid Arrow".
   *
   * @param string $title
   *   The spell name.
   *
   * @return \Drupal\taxonomy\TermInterface|null
   *   The existing term, or NULL when there is none.
   */
  private function findExisting(string $title): ?TermInterface {
    $wanted = $this->nameKey($title);
    if ($wanted === '') {
      return NULL;
    }
    $storage = $this->entityTypeManager->getStorage('taxonomy_term');
    $ids = $storage->getQuery()
      ->accessCheck(FALSE)
      ->condition('vid', 'spells')
      ->execute();
    /** @var \Drupal\taxonomy\TermInterface $term */
    foreach ($storage->loadMultiple($ids) as $term) {
      if ($this->nameKey((string) $term->label()) === $wanted) {
        return $term;
      }
    }
    return NULL;
  }

  /**
   * Fill only empty fields on an existing term.
   *
   * @param \Drupal\taxonomy\TermInterface $term
   *   The existing spell term.
   * @param array<string, mixed> $incoming
   *   Incoming field values from the caller.
   */
  private function fillEmpty(TermInterface $term, array $incoming): void {
    $changed = FALSE;

    if ($term->get('field_spell_level')->isEmpty() && $incoming['level'] !== NULL) {
      $term->set('field_spell_level', $incoming['level']);
      $changed = TRUE;
    }

    $school_tid = $this->findOrCreateSchool(
      is_string($incoming['school']) ? $incoming['school'] : NULL,
    );
    if ($school_tid !== NULL && $term->get('field_spell_school')->isEmpty()) {
      $term->set('field_spell_school', ['target_id' => $school_tid]);
      $changed = TRUE;
    }

    $string_fields = [
      'field_spell_casting_time' => 'casting_time',
      'field_spell_range' => 'spell_range',
      'field_spell_components' => 'components',
      'field_spell_duration' => 'duration',
    ];
    foreach ($string_fields as $field => $key) {
      $raw = $incoming[$key];
      $value = is_string($raw) ? trim($raw) : '';
      if ($value === '' || !$term->get($field)->isEmpty()) {
        continue;
      }
      $term->set($field, $value);
      $changed = TRUE;
    }

    if ($incoming['concentration'] !== NULL && $term->get('field_spell_concentration')->isEmpty()) {
      $term->set('field_spell_concentration', $incoming['concentration'] ? 1 : 0);
      $changed = TRUE;
    }
    if ($incoming['ritual'] !== NULL && $term->get('field_spell_ritual')->isEmpty()) {
      $term->set('field_spell_ritual', $incoming['ritual'] ? 1 : 0);
      $changed = TRUE;
    }

    $description = is_string($incoming['description']) ? trim($incoming['description']) : '';
    if ($description !== '' && $term->get('field_spell_description')->isEmpty()) {
      $term->set('field_spell_description', [
        'value' => $description,
        'format' => 'plain_text',
      ]);
      $changed = TRUE;
    }

    if ($changed) {
      $term->save();
    }
  }

  /**
   * Apply incoming values onto a create-values array.
   *
   * @param array<string, mixed> $values
   *   Term create values, modified in place.
   * @param array<string, mixed> $incoming
   *   Incoming field values from the caller.
   */
  private function applyIncoming(array &$values, array $incoming): void {
    $school_tid = $this->findOrCreateSchool(
      is_string($incoming['school']) ? $incoming['school'] : NULL,
    );
    if ($school_tid !== NULL) {
      $values['field_spell_school'] = ['target_id' => $school_tid];
    }

    $string_fields = [
      'field_spell_casting_time' => 'casting_time',
      'field_spell_range' => 'spell_range',
      'field_spell_components' => 'components',
      'field_spell_duration' => 'duration',
    ];
    foreach ($string_fields as $field => $key) {
      $raw = $incoming[$key];
      $value = is_string($raw) ? trim($raw) : '';
      if ($value !== '') {
        $values[$field] = $value;
      }
    }

    if ($incoming['concentration'] !== NULL) {
      $values['field_spell_concentration'] = $incoming['concentration'] ? 1 : 0;
    }
    if ($incoming['ritual'] !== NULL) {
      $values['field_spell_ritual'] = $incoming['ritual'] ? 1 : 0;
    }

    $description = is_string($incoming['description']) ? trim($incoming['description']) : '';
    if ($description !== '') {
      $values['field_spell_description'] = [
        'value' => $description,
        'format' => 'plain_text',
      ];
    }
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
   * Normalise a spell name for duplicate comparison.
   *
   * @param string $name
   *   Raw spell name.
   *
   * @return string
   *   Lowercased name with punctuation stripped.
   */
  private function nameKey(string $name): string {
    $key = strtolower(trim($name));
    $key = str_replace(["'", "\u{2019}"], '', $key);
    $stripped = preg_replace('/[^a-z0-9]+/', '', $key);
    return is_string($stripped) ? $stripped : '';
  }

}
