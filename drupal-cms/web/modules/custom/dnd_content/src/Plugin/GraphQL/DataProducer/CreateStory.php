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
use Drupal\taxonomy\TermInterface;
use GraphQL\Error\UserError;
use Symfony\Component\DependencyInjection\ContainerInterface;

/**
 * Creates a story node linked to a campaign taxonomy term.
 *
 * The generated story text is stored in field_body (plain text format).
 * field_campaign is set to the loaded campaign term, field_story_number
 * to the provided integer, and field_session_date to the supplied date
 * string (or today if omitted).
 */
#[DataProducer(
  id: "create_story",
  name: new TranslatableMarkup("Create Story"),
  description: new TranslatableMarkup("Creates a story node and links it to a campaign."),
  produces: new ContextDefinition(
    data_type: "any",
    label: new TranslatableMarkup("Created story node"),
  ),
  consumes: [
    "campaign_id" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("Campaign term UUID"),
    ),
    "title" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("Story title"),
    ),
    "body" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("Story body text"),
    ),
    "story_number" => new ContextDefinition(
      data_type: "integer",
      label: new TranslatableMarkup("Story number in the series"),
    ),
    "session_date" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("Session date (YYYY-MM-DD)"),
      required: FALSE,
    ),
  ],
)]
final class CreateStory extends DataProducerPluginBase implements ContainerFactoryPluginInterface {

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
   * Creates and saves a story node linked to the given campaign.
   *
   * @param string $campaign_id
   *   UUID of the campaign taxonomy term.
   * @param string $title
   *   Story title.
   * @param string $body
   *   Story body text (markdown / plain text).
   * @param int $story_number
   *   Story number within the campaign series.
   * @param string|null $session_date
   *   Session date string in YYYY-MM-DD format, or NULL to use today.
   * @param \Drupal\graphql\GraphQL\Execution\FieldContext $context
   *   GraphQL field execution context.
   *
   * @return \Drupal\node\NodeInterface
   *   The newly created story node.
   *
   * @throws \GraphQL\Error\UserError
   *   When the campaign cannot be found or the user lacks permission.
   */
  public function resolve(
    string $campaign_id,
    string $title,
    string $body,
    int $story_number,
    ?string $session_date,
    FieldContext $context,
  ): NodeInterface {
    $terms = $this->entityTypeManager
      ->getStorage('taxonomy_term')
      ->loadByProperties(['uuid' => $campaign_id, 'vid' => 'campaign']);
    $term = reset($terms);
    if (!$term instanceof TermInterface) {
      throw new UserError('Campaign not found.');
    }

    if (!$this->currentUser->hasPermission('create story content')) {
      $context->addCacheableDependency($this->currentUser);
      throw new UserError('You do not have permission to create stories.');
    }

    $node = $this->entityTypeManager->getStorage('node')->create([
      'type'               => 'story',
      'title'              => $title,
      'field_body'         => ['value' => $body, 'format' => 'plain_text'],
      'field_story_number' => $story_number,
      'field_campaign'     => $term->id(),
      'field_session_date' => $session_date ?? date('Y-m-d'),
      'status'             => 1,
    ]);

    $node->save();

    return $node;
  }

}
