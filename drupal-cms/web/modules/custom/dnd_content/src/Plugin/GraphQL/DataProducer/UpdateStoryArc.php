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
use Drupal\taxonomy\TermInterface;
use GraphQL\Error\UserError;
use Symfony\Component\DependencyInjection\ContainerInterface;

/**
 * Writes a story_arc node's editable fields from a partial JSON patch.
 *
 * Only the keys present are written, so a single field can be edited without
 * round-tripping the arc. Relationships go through saveStoryArcRelations.
 */
#[DataProducer(
  id: "update_story_arc",
  name: new TranslatableMarkup("Update Story Arc"),
  description: new TranslatableMarkup("Writes editable fields onto a story arc node."),
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
      label: new TranslatableMarkup("JSON-encoded arc fields"),
    ),
  ],
)]
final class UpdateStoryArc extends DataProducerPluginBase implements ContainerFactoryPluginInterface {

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
   * Writes the supplied fields onto an existing story arc node.
   *
   * @param string $id
   *   UUID of the story arc node.
   * @param string $payload
   *   JSON-encoded map of arc fields to write.
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
      throw new UserError('Invalid arc payload: expected a JSON object.');
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

    if (array_key_exists('title', $data) && trim((string) $data['title']) !== '') {
      $node->setTitle(trim((string) $data['title']));
    }

    if (array_key_exists('campaign', $data)) {
      $term = $this->arcWriter->resolveTerm((string) $data['campaign'], 'campaign');
      if (!$term instanceof TermInterface) {
        throw new UserError('Campaign not found.');
      }
      $node->set('field_campaign', $term->id());
    }

    $this->arcWriter->applyFields($node, $data);
    $node->save();

    return $node;
  }

}
