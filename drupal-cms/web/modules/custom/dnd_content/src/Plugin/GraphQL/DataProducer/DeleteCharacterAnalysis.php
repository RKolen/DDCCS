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
 * Delete the character_analysis node for a character (discard).
 */
#[DataProducer(
  id: "delete_character_analysis",
  name: new TranslatableMarkup("Delete Character Analysis"),
  description: new TranslatableMarkup("Delete a character's analysis node and its paragraphs."),
  produces: new ContextDefinition(
    data_type: "boolean",
    label: new TranslatableMarkup("Deleted"),
  ),
  consumes: [
    "campaign_id" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("Campaign term UUID"),
    ),
    "character_id" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("Character node UUID"),
    ),
  ],
)]
final class DeleteCharacterAnalysis extends DataProducerPluginBase implements ContainerFactoryPluginInterface {

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
   * Delete the analysis node for a character (keyed by character).
   *
   * @param string $campaign_id
   *   The campaign term UUID (accepted but unused; the record is keyed by
   *   character).
   * @param string $character_id
   *   The character node UUID.
   * @param \Drupal\graphql\GraphQL\Execution\FieldContext $context
   *   The GraphQL field execution context.
   *
   * @return bool
   *   TRUE when a node was deleted (or none existed), FALSE on access denial.
   *
   * @throws \GraphQL\Error\UserError
   *   When the character is missing.
   */
  public function resolve(
    string $campaign_id,
    string $character_id,
    FieldContext $context,
  ): bool {
    // $campaign_id is accepted for a stable mutation signature but not used to
    // locate the record: the analysis is keyed by character alone.
    unset($campaign_id);
    $node_storage = $this->entityTypeManager->getStorage('node');

    $characters = $node_storage->loadByProperties(['uuid' => $character_id, 'type' => 'character']);
    $character = reset($characters);
    if (!$character instanceof NodeInterface) {
      throw new UserError('Character not found.');
    }

    $existing = $node_storage->loadByProperties([
      'type' => 'character_analysis',
      'field_character' => $character->id(),
    ]);
    foreach ($existing as $node) {
      if (!$node->access('delete', $this->currentUser)) {
        $context->addCacheableDependency($this->currentUser);
        return FALSE;
      }
      $node->delete();
    }
    return TRUE;
  }

}
