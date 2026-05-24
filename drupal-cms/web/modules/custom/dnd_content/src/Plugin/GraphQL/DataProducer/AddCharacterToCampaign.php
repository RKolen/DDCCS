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
 * Clones a source character into a campaign and adds the clone to the party.
 *
 * Source characters (field_source_character = true) are templates. When added
 * to a campaign, a campaign-specific clone is created: field_source_character
 * is set to false and field_campaign is set to the target campaign term. The
 * clone is then appended to field_current_party on the campaign term.
 */
#[DataProducer(
  id: "add_character_to_campaign",
  name: new TranslatableMarkup("Add Character to Campaign"),
  description: new TranslatableMarkup("Clones a source character into a campaign and registers the clone in field_current_party."),
  produces: new ContextDefinition(
    data_type: "any",
    label: new TranslatableMarkup("Updated campaign term"),
  ),
  consumes: [
    "campaign_id" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("Campaign term UUID"),
    ),
    "character_id" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("Source character node UUID"),
    ),
  ],
)]
final class AddCharacterToCampaign extends DataProducerPluginBase implements ContainerFactoryPluginInterface {

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
   * Clones the source character and appends it to the campaign party.
   *
   * @param string $campaign_id
   *   The UUID of the campaign taxonomy term.
   * @param string $character_id
   *   The UUID of the source character node.
   * @param \Drupal\graphql\GraphQL\Execution\FieldContext $context
   *   The GraphQL field execution context.
   *
   * @return \Drupal\taxonomy\TermInterface
   *   The updated campaign term.
   *
   * @throws \GraphQL\Error\UserError
   *   When the campaign or character cannot be found, or permissions are
   *   denied.
   */
  public function resolve(string $campaign_id, string $character_id, FieldContext $context): TermInterface {
    $terms = $this->entityTypeManager
      ->getStorage('taxonomy_term')
      ->loadByProperties(['uuid' => $campaign_id, 'vid' => 'campaign']);

    $term = reset($terms);
    if (!$term instanceof TermInterface) {
      throw new UserError('Campaign not found.');
    }

    $nodes = $this->entityTypeManager
      ->getStorage('node')
      ->loadByProperties(['uuid' => $character_id, 'type' => 'character']);

    $source = reset($nodes);
    if (!$source instanceof NodeInterface) {
      throw new UserError('Character not found.');
    }

    if (!$term->access('update', $this->currentUser)) {
      $context->addCacheableDependency($this->currentUser);
      throw new UserError('You do not have permission to update this campaign.');
    }

    if (!$source->access('create', $this->currentUser)) {
      $context->addCacheableDependency($this->currentUser);
      throw new UserError('You do not have permission to create characters.');
    }

    // createDuplicate() assigns a new nid/uuid and resets timestamps.
    // Paragraph fields are deep-cloned by the paragraphs module hooks.
    // Validation is skipped: the source is already persisted and trusted;
    // the only overrides (field_campaign, field_source_character) are set to
    // known-valid values. save() will surface any genuine constraint errors.
    $clone = $source->createDuplicate();
    $clone->set('field_campaign', $term->id());
    $clone->set('field_source_character', FALSE);
    $clone->save();

    $term->get('field_current_party')->appendItem(['target_id' => $clone->id()]);
    $term->save();

    return $term;
  }

}
