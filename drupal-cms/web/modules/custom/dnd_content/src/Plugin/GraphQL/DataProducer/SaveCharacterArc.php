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
use Drupal\paragraphs\Entity\Paragraph;
use GraphQL\Error\UserError;
use Symfony\Component\DependencyInjection\ContainerInterface;

/**
 * Saves character arc analysis results onto a character node.
 *
 * Stores the scalar arc fields (direction, stage, summary, stories analysed,
 * updated) and rebuilds the arc_metric, arc_relationship, and arc_goal
 * paragraph collections from a JSON payload. Returns the updated node.
 */
#[DataProducer(
  id: "save_character_arc",
  name: new TranslatableMarkup("Save Character Arc"),
  description: new TranslatableMarkup("Persists arc analysis onto a character node."),
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
      label: new TranslatableMarkup("JSON-encoded arc result"),
    ),
  ],
)]
final class SaveCharacterArc extends DataProducerPluginBase implements ContainerFactoryPluginInterface {

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
   * Persist arc analysis onto the character.
   *
   * @param string $id
   *   The character node UUID.
   * @param string $payload
   *   The JSON-encoded arc result.
   * @param \Drupal\graphql\GraphQL\Execution\FieldContext $context
   *   The GraphQL field execution context.
   *
   * @return \Drupal\node\NodeInterface
   *   The updated character node.
   *
   * @throws \GraphQL\Error\UserError
   *   When the character is missing, the payload is invalid, or access denied.
   */
  public function resolve(string $id, string $payload, FieldContext $context): NodeInterface {
    $data = json_decode($payload, TRUE);
    if (!is_array($data)) {
      throw new UserError('Invalid arc payload: expected a JSON object.');
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

    $node->set('field_arc_direction', (string) ($data['direction'] ?? ''));
    $node->set('field_arc_stage', (string) ($data['stage'] ?? ''));
    $node->set('field_arc_summary', (string) ($data['summary'] ?? ''));
    $node->set('field_arc_stories', (int) ($data['stories_analyzed'] ?? 0));
    $node->set('field_arc_updated', (string) ($data['updated_at'] ?? ''));

    $node->set('field_arc_metrics', $this->buildMetrics($data['metrics'] ?? []));
    $node->set('field_arc_relationships', $this->buildRelationships($data['relationships'] ?? []));
    $node->set('field_arc_goals', $this->buildGoals($data['goals'] ?? []));

    $node->save();

    return $node;
  }

  /**
   * Build arc_metric paragraph references from the payload metrics map.
   *
   * @param mixed $metrics
   *   The metrics map keyed by metric id.
   *
   * @return array<int, array{target_id: int, target_revision_id: int}>
   *   Entity-reference-revisions values.
   */
  private function buildMetrics($metrics): array {
    if (!is_array($metrics)) {
      return [];
    }
    $values = [];
    foreach ($metrics as $key => $metric) {
      if (!is_array($metric)) {
        continue;
      }
      $series = is_array($metric['series'] ?? NULL) ? $metric['series'] : [];
      $values[] = $this->paragraphRef(Paragraph::create([
        'type' => 'arc_metric',
        'field_metric_key' => (string) $key,
        'field_metric_label' => (string) ($metric['label'] ?? $key),
        'field_metric_direction' => (string) ($metric['direction'] ?? 'stasis'),
        'field_metric_series' => implode(',', array_map('strval', $series)),
        'field_metric_obs' => (string) ($metric['obs'] ?? ''),
      ]));
    }
    return $values;
  }

  /**
   * Build arc_relationship paragraph references from the payload list.
   *
   * @param mixed $relationships
   *   The list of relationship dicts.
   *
   * @return array<int, array{target_id: int, target_revision_id: int}>
   *   Entity-reference-revisions values.
   */
  private function buildRelationships($relationships): array {
    if (!is_array($relationships)) {
      return [];
    }
    $values = [];
    foreach ($relationships as $rel) {
      if (!is_array($rel) || trim((string) ($rel['target'] ?? '')) === '') {
        continue;
      }
      $values[] = $this->paragraphRef(Paragraph::create([
        'type' => 'arc_relationship',
        'field_rel_target' => (string) $rel['target'],
        'field_rel_type' => (string) ($rel['type'] ?? 'neutral'),
        'field_rel_strength' => (int) ($rel['strength'] ?? 5),
        'field_rel_trust' => (int) ($rel['trust'] ?? 5),
        'field_rel_note' => (string) ($rel['note'] ?? ''),
      ]));
    }
    return $values;
  }

  /**
   * Build arc_goal paragraph references from the payload list.
   *
   * @param mixed $goals
   *   The list of goal dicts.
   *
   * @return array<int, array{target_id: int, target_revision_id: int}>
   *   Entity-reference-revisions values.
   */
  private function buildGoals($goals): array {
    if (!is_array($goals)) {
      return [];
    }
    $values = [];
    foreach ($goals as $goal) {
      if (!is_array($goal) || trim((string) ($goal['description'] ?? '')) === '') {
        continue;
      }
      $values[] = $this->paragraphRef(Paragraph::create([
        'type' => 'arc_goal',
        'field_goal_description' => (string) $goal['description'],
        'field_goal_status' => (string) ($goal['status'] ?? 'active'),
        'field_goal_progress' => (int) ($goal['progress'] ?? 0),
      ]));
    }
    return $values;
  }

  /**
   * Save a paragraph and return its entity-reference-revisions value.
   *
   * @param \Drupal\paragraphs\Entity\Paragraph $paragraph
   *   The unsaved paragraph.
   *
   * @return array{target_id: int, target_revision_id: int}
   *   The reference value.
   */
  private function paragraphRef(Paragraph $paragraph): array {
    $paragraph->save();
    return [
      'target_id' => (int) $paragraph->id(),
      'target_revision_id' => (int) $paragraph->getRevisionId(),
    ];
  }

}
