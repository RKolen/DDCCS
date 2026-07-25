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
use Drupal\media\MediaInterface;
use Drupal\node\NodeInterface;
use GraphQL\Error\UserError;
use Symfony\Component\DependencyInjection\ContainerInterface;

/**
 * Points a character's portrait at an existing image media entity.
 *
 * Unlike SetCharacterPortrait, which creates media from a base64 payload, this
 * selects an already-stored image media - for example a previously generated
 * portrait chosen from the media library - and makes it the character's active
 * field_image. Returns the updated node.
 */
#[DataProducer(
  id: "set_character_image",
  name: new TranslatableMarkup("Set Character Image"),
  description: new TranslatableMarkup("Points a character's portrait at existing media."),
  produces: new ContextDefinition(
    data_type: "any",
    label: new TranslatableMarkup("Updated character node"),
  ),
  consumes: [
    "id" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("Character node UUID"),
    ),
    "media_id" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("Image media UUID"),
    ),
  ],
)]
final class SetCharacterImage extends DataProducerPluginBase implements ContainerFactoryPluginInterface {

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
   * Point the character's portrait at an existing image media.
   *
   * @param string $id
   *   The character node UUID.
   * @param string $media_id
   *   The image media UUID to attach.
   * @param \Drupal\graphql\GraphQL\Execution\FieldContext $context
   *   The GraphQL field execution context.
   *
   * @return \Drupal\node\NodeInterface
   *   The updated character node.
   *
   * @throws \GraphQL\Error\UserError
   *   When the character or media is missing, or access is denied.
   */
  public function resolve(
    string $id,
    string $media_id,
    FieldContext $context,
  ): NodeInterface {
    $node = $this->loadCharacter($id);
    if (!$node->access('update', $this->currentUser)) {
      $context->addCacheableDependency($this->currentUser);
      throw new UserError('You do not have permission to update this character.');
    }

    $media = $this->loadImageMedia($media_id);

    $node->set('field_image', ['target_id' => $media->id()]);
    $node->save();

    return $node;
  }

  /**
   * Load a character node by UUID.
   *
   * @param string $id
   *   The character node UUID.
   *
   * @return \Drupal\node\NodeInterface
   *   The character node.
   *
   * @throws \GraphQL\Error\UserError
   *   When no character matches the UUID.
   */
  private function loadCharacter(string $id): NodeInterface {
    $nodes = $this->entityTypeManager
      ->getStorage('node')
      ->loadByProperties(['uuid' => $id, 'type' => 'character']);
    $node = reset($nodes);
    if (!$node instanceof NodeInterface) {
      throw new UserError('Character not found.');
    }
    return $node;
  }

  /**
   * Load an image media entity by UUID.
   *
   * @param string $media_id
   *   The image media UUID.
   *
   * @return \Drupal\media\MediaInterface
   *   The image media entity.
   *
   * @throws \GraphQL\Error\UserError
   *   When no image media matches the UUID.
   */
  private function loadImageMedia(string $media_id): MediaInterface {
    $media_entities = $this->entityTypeManager
      ->getStorage('media')
      ->loadByProperties(['uuid' => $media_id, 'bundle' => 'image']);
    $media = reset($media_entities);
    if (!$media instanceof MediaInterface) {
      throw new UserError('Image media not found.');
    }
    return $media;
  }

}
