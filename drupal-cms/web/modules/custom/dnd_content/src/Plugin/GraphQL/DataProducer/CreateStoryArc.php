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
 * Creates a story_arc node linked to a campaign taxonomy term.
 *
 * Only the campaign and title are required, so the wizard can save the arc
 * after step one. Relationships go through saveStoryArcRelations.
 */
#[DataProducer(
  id: "create_story_arc",
  name: new TranslatableMarkup("Create Story Arc"),
  description: new TranslatableMarkup("Creates a story arc node and links it to a campaign."),
  produces: new ContextDefinition(
    data_type: "any",
    label: new TranslatableMarkup("Created story arc node"),
  ),
  consumes: [
    "campaign_id" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("Campaign term UUID"),
    ),
    "title" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("Arc title"),
    ),
    "payload" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("JSON-encoded arc fields"),
      required: FALSE,
    ),
  ],
)]
final class CreateStoryArc extends DataProducerPluginBase implements ContainerFactoryPluginInterface {

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
   * Creates and saves a story arc node linked to the given campaign.
   *
   * @param string $campaign_id
   *   UUID of the campaign taxonomy term.
   * @param string $title
   *   Arc title.
   * @param string|null $payload
   *   JSON-encoded map of arc fields, or NULL to create a bare arc.
   * @param \Drupal\graphql\GraphQL\Execution\FieldContext $context
   *   GraphQL field execution context.
   *
   * @return \Drupal\node\NodeInterface
   *   The newly created story arc node.
   *
   * @throws \GraphQL\Error\UserError
   *   When the campaign is missing, the payload is invalid, or access denied.
   */
  public function resolve(
    string $campaign_id,
    string $title,
    ?string $payload,
    FieldContext $context,
  ): NodeInterface {
    $data = [];
    if ($payload !== NULL && trim($payload) !== '') {
      $decoded = json_decode($payload, TRUE);
      if (!is_array($decoded)) {
        throw new UserError('Invalid arc payload: expected a JSON object.');
      }
      $data = $decoded;
    }

    $terms = $this->entityTypeManager
      ->getStorage('taxonomy_term')
      ->loadByProperties(['uuid' => $campaign_id, 'vid' => 'campaign']);
    $term = reset($terms);
    if (!$term instanceof TermInterface) {
      throw new UserError('Campaign not found.');
    }

    if (!$this->currentUser->hasPermission('create story_arc content')) {
      $context->addCacheableDependency($this->currentUser);
      throw new UserError('You do not have permission to create story arcs.');
    }

    $node = $this->entityTypeManager->getStorage('node')->create([
      'type' => 'story_arc',
      'title' => $title,
      'field_campaign' => $term->id(),
      'status' => 1,
    ]);

    $this->arcWriter->applyFields($node, $data);
    $node->save();

    return $node;
  }

}
