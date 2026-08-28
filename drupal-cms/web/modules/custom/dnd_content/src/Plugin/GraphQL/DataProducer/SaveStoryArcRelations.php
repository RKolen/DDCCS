<?php

declare(strict_types=1);

namespace Drupal\dnd_content\Plugin\GraphQL\DataProducer;

use Drupal\Core\Entity\EntityTypeManagerInterface;
use Drupal\Core\Plugin\ContainerFactoryPluginInterface;
use Drupal\Core\Plugin\Context\ContextDefinition;
use Drupal\Core\Session\AccountInterface;
use Drupal\Core\StringTranslation\TranslatableMarkup;
use Drupal\dnd_content\Service\StoryArcWriter;
use Drupal\graphql\Attribute\DataProducer;
use Drupal\graphql\GraphQL\Execution\FieldContext;
use Drupal\graphql\Plugin\GraphQL\DataProducer\DataProducerPluginBase;
use Drupal\node\NodeInterface;
use GraphQL\Error\UserError;
use Symfony\Component\DependencyInjection\ContainerInterface;

/**
 * Replaces a story arc's relationship paragraph collections.
 *
 * The payload holds a "party" list, an "npc" list, or both. Only the sides
 * present are replaced, so each suggestion run saves independently.
 * Replacement within a side is wholesale: the console sends the set that
 * survived accept/reject, not a diff.
 */
#[DataProducer(
  id: "save_story_arc_relations",
  name: new TranslatableMarkup("Save Story Arc Relations"),
  description: new TranslatableMarkup("Replaces a story arc's party and NPC relationship paragraphs."),
  produces: new ContextDefinition(
    data_type: "any",
    label: new TranslatableMarkup("Updated story arc node"),
  ),
  consumes: [
    "id" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("Story arc node UUID"),
    ),
    "payload" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("JSON-encoded relation lists"),
    ),
  ],
)]
final class SaveStoryArcRelations extends DataProducerPluginBase implements ContainerFactoryPluginInterface {

  /**
   * Payload keys mapped to the story_arc field they replace.
   */
  private const RELATION_FIELDS = [
    'party' => 'field_arc_party_relations',
    'npc' => 'field_arc_npc_relations',
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
   * The story arc field writer.
   *
   * @var \Drupal\dnd_content\Service\StoryArcWriter
   */
  protected StoryArcWriter $arcWriter;

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
    $instance->arcWriter = $container->get('dnd_content.story_arc_writer');
    return $instance;
  }

  /**
   * Replaces the relationship collections named in the payload.
   *
   * @param string $id
   *   UUID of the story arc node.
   * @param string $payload
   *   JSON-encoded map with a "party" and/or "npc" list of relation dicts.
   * @param \Drupal\graphql\GraphQL\Execution\FieldContext $context
   *   GraphQL field execution context.
   *
   * @return \Drupal\node\NodeInterface
   *   The updated story arc node.
   *
   * @throws \GraphQL\Error\UserError
   *   When the arc is missing, the payload is invalid, or access is denied.
   */
  public function resolve(string $id, string $payload, FieldContext $context): NodeInterface {
    $data = json_decode($payload, TRUE);
    if (!is_array($data)) {
      throw new UserError('Invalid relations payload: expected a JSON object.');
    }

    $nodes = $this->entityTypeManager
      ->getStorage('node')
      ->loadByProperties(['uuid' => $id, 'type' => 'story_arc']);
    $node = reset($nodes);
    if (!$node instanceof NodeInterface) {
      throw new UserError('Story arc not found.');
    }
    if (!$node->access('update', $this->currentUser)) {
      $context->addCacheableDependency($this->currentUser);
      throw new UserError('You do not have permission to update this story arc.');
    }

    $campaign_field = $node->get('field_campaign');
    $campaign_tid = $campaign_field->isEmpty() ? NULL : (int) $campaign_field->target_id;

    $touched = FALSE;
    foreach (self::RELATION_FIELDS as $key => $field) {
      if (!array_key_exists($key, $data)) {
        continue;
      }
      $node->set($field, $this->arcWriter->buildRelations($data[$key], $campaign_tid));
      $touched = TRUE;
    }

    if (!$touched) {
      throw new UserError('Relations payload must contain a "party" or "npc" list.');
    }

    $node->save();

    return $node;
  }

}
