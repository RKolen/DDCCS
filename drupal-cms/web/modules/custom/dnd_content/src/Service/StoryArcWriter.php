<?php

declare(strict_types=1);

namespace Drupal\dnd_content\Service;

use Drupal\Core\Entity\EntityTypeManagerInterface;
use Drupal\node\NodeInterface;
use Drupal\paragraphs\Entity\Paragraph;
use Drupal\taxonomy\TermInterface;

/**
 * Writes story_arc node fields and arc_relationship_pair paragraphs.
 *
 * Shared by the three arc mutations. Payloads use the console's camelCase
 * names and are partial patches: only the keys present are written.
 */
final class StoryArcWriter {

  /**
   * Scalar payload keys mapped to their story_arc field name.
   */
  private const TEXT_FIELDS = [
    'body' => 'field_body',
    'overallPlot' => 'field_overall_plot',
  ];

  /**
   * The entity type manager.
   *
   * @var \Drupal\Core\Entity\EntityTypeManagerInterface
   */
  private EntityTypeManagerInterface $entityTypeManager;

  /**
   * Constructs a StoryArcWriter.
   *
   * @param \Drupal\Core\Entity\EntityTypeManagerInterface $entity_type_manager
   *   The entity type manager.
   */
  public function __construct(EntityTypeManagerInterface $entity_type_manager) {
    $this->entityTypeManager = $entity_type_manager;
  }

  /**
   * Apply a partial story_arc payload to a node.
   *
   * Unrecognised keys are ignored; unresolvable references are skipped so a
   * partially matched import still saves what it matched.
   *
   * @param \Drupal\node\NodeInterface $node
   *   The story_arc node to write to.
   * @param array<string, mixed> $data
   *   The decoded payload.
   */
  public function applyFields(NodeInterface $node, array $data): void {
    $campaign = $this->campaignTid($node);

    foreach (self::TEXT_FIELDS as $key => $field) {
      if (array_key_exists($key, $data)) {
        $node->set($field, [
          'value' => (string) $data[$key],
          'format' => 'plain_text',
        ]);
      }
    }

    if (array_key_exists('levelRange', $data)) {
      $node->set('field_level_range', (string) $data['levelRange']);
    }

    if (array_key_exists('targetStories', $data)) {
      $stories = $data['targetStories'];
      $node->set('field_target_stories', $stories === NULL ? NULL : (int) $stories);
    }

    if (array_key_exists('faction', $data)) {
      $term = $this->resolveTerm((string) $data['faction'], 'factions');
      $node->set('field_faction', $term instanceof TermInterface ? $term->id() : NULL);
    }

    if (array_key_exists('party', $data)) {
      $node->set('field_party', $this->resolveCharacterIds($data['party'], $campaign));
    }

    if (array_key_exists('npcs', $data)) {
      $node->set('field_npcs', $this->resolveCharacterIds($data['npcs'], $campaign));
    }
  }

  /**
   * Build arc_relationship_pair paragraph references from a relation list.
   *
   * A pair missing either end is skipped: it could not be read back from
   * either character's page.
   *
   * @param mixed $items
   *   The list of relation dicts.
   * @param int|null $campaign_tid
   *   Campaign term id used to disambiguate title matches, or NULL.
   *
   * @return array<int, array{target_id: int, target_revision_id: int}>
   *   Entity-reference-revisions values.
   */
  public function buildRelations($items, ?int $campaign_tid = NULL): array {
    if (!is_array($items)) {
      return [];
    }
    $values = [];
    foreach ($items as $item) {
      if (!is_array($item)) {
        continue;
      }
      $source = $this->resolveCharacter((string) ($item['source'] ?? ''), $campaign_tid);
      $target = $this->resolveCharacter((string) ($item['target'] ?? ''), $campaign_tid);
      if (!$source instanceof NodeInterface || !$target instanceof NodeInterface) {
        continue;
      }
      $tier = isset($item['tier']) ? (int) $item['tier'] : NULL;
      $paragraph = Paragraph::create([
        'type' => 'arc_relationship_pair',
        'field_pair_source' => $source->id(),
        'field_pair_target' => $target->id(),
        'field_pair_type' => (string) ($item['type'] ?? ''),
        'field_pair_tier' => $tier !== NULL && $tier >= 1 && $tier <= 3 ? $tier : NULL,
        'field_pair_note' => [
          'value' => (string) ($item['note'] ?? ''),
          'format' => 'plain_text',
        ],
      ]);
      $paragraph->save();
      $values[] = [
        'target_id' => (int) $paragraph->id(),
        'target_revision_id' => (int) $paragraph->getRevisionId(),
      ];
    }
    return $values;
  }

  /**
   * Resolve a list of character references to node ids.
   *
   * @param mixed $refs
   *   A list of character UUIDs or titles.
   * @param int|null $campaign_tid
   *   Campaign term id used to disambiguate title matches, or NULL.
   *
   * @return array<int, int>
   *   The resolved node ids, in payload order, without duplicates.
   */
  private function resolveCharacterIds($refs, ?int $campaign_tid = NULL): array {
    if (!is_array($refs)) {
      return [];
    }
    $ids = [];
    foreach ($refs as $ref) {
      $node = $this->resolveCharacter((string) $ref, $campaign_tid);
      if ($node instanceof NodeInterface) {
        $ids[(int) $node->id()] = (int) $node->id();
      }
    }
    return array_values($ids);
  }

  /**
   * Resolve one character reference to a node.
   *
   * Accepts a node UUID or an exact title, so the importer and the AI
   * suggestions can pass names directly.
   *
   * Titles are ambiguous here - a canonical character and its campaign clone
   * share one. The campaign clone wins when a campaign is known (that is what
   * the party is built from), else the canonical node, which is right for NPCs.
   *
   * @param string $ref
   *   A character node UUID or exact title.
   * @param int|null $campaign_tid
   *   Campaign term id to prefer when a title matches more than one node.
   *
   * @return \Drupal\node\NodeInterface|null
   *   The character node, or NULL when nothing matches.
   */
  public function resolveCharacter(string $ref, ?int $campaign_tid = NULL): ?NodeInterface {
    $ref = trim($ref);
    if ($ref === '') {
      return NULL;
    }
    $storage = $this->entityTypeManager->getStorage('node');

    $matches = $storage->loadByProperties(['uuid' => $ref, 'type' => 'character']);
    $node = reset($matches);
    if ($node instanceof NodeInterface) {
      return $node;
    }

    $matches = $storage->loadByProperties(['title' => $ref, 'type' => 'character']);
    if ($matches === []) {
      return NULL;
    }
    if (count($matches) === 1) {
      return reset($matches);
    }

    $fallback = NULL;
    foreach ($matches as $candidate) {
      if ($campaign_tid !== NULL
        && (int) $candidate->get('field_campaign')->target_id === $campaign_tid) {
        return $candidate;
      }
      if ($fallback === NULL || (bool) $candidate->get('field_source_character')->value) {
        $fallback = $candidate;
      }
    }
    return $fallback;
  }

  /**
   * Read a node's campaign term id.
   *
   * @param \Drupal\node\NodeInterface $node
   *   The node to read field_campaign from.
   *
   * @return int|null
   *   The campaign term id, or NULL when unset.
   */
  private function campaignTid(NodeInterface $node): ?int {
    if (!$node->hasField('field_campaign')) {
      return NULL;
    }
    $field = $node->get('field_campaign');
    return $field->isEmpty() ? NULL : (int) $field->target_id;
  }

  /**
   * Resolve a taxonomy term reference within one vocabulary.
   *
   * @param string $ref
   *   A term UUID or exact name.
   * @param string $vid
   *   The vocabulary machine name.
   *
   * @return \Drupal\taxonomy\TermInterface|null
   *   The term, or NULL when nothing matches.
   */
  public function resolveTerm(string $ref, string $vid): ?TermInterface {
    $ref = trim($ref);
    if ($ref === '') {
      return NULL;
    }
    $storage = $this->entityTypeManager->getStorage('taxonomy_term');

    $matches = $storage->loadByProperties(['uuid' => $ref, 'vid' => $vid]);
    $term = reset($matches);
    if ($term instanceof TermInterface) {
      return $term;
    }

    $matches = $storage->loadByProperties(['name' => $ref, 'vid' => $vid]);
    $term = reset($matches);
    return $term instanceof TermInterface ? $term : NULL;
  }

}
