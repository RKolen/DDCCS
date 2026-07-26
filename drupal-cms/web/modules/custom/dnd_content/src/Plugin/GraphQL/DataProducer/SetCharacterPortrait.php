<?php

declare(strict_types=1);

namespace Drupal\dnd_content\Plugin\GraphQL\DataProducer;

use Drupal\Core\Entity\EntityTypeManagerInterface;
use Drupal\Core\Plugin\ContainerFactoryPluginInterface;
use Drupal\Core\Plugin\Context\ContextDefinition;
use Drupal\Core\Session\AccountInterface;
use Drupal\Core\StringTranslation\TranslatableMarkup;
use Drupal\dnd_content\Service\PortraitWriter;
use Drupal\graphql\Attribute\DataProducer;
use Drupal\graphql\GraphQL\Execution\FieldContext;
use Drupal\graphql\Plugin\GraphQL\DataProducer\DataProducerPluginBase;
use Drupal\node\NodeInterface;
use GraphQL\Error\UserError;
use Symfony\Component\DependencyInjection\ContainerInterface;

/**
 * Attaches a generated portrait image to a character node.
 *
 * Decodes a base64 PNG produced by the sidecar's ComfyUI endpoint and hands it
 * to the shared portrait writer, which stores it as a managed file plus image
 * media and points the character's field_image at that media. Returns the
 * updated node.
 */
#[DataProducer(
  id: "set_character_portrait",
  name: new TranslatableMarkup("Set Character Portrait"),
  description: new TranslatableMarkup("Stores a generated portrait on a character node."),
  produces: new ContextDefinition(
    data_type: "any",
    label: new TranslatableMarkup("Updated character node"),
  ),
  consumes: [
    "id" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("Character node UUID"),
    ),
    "image_base64" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("Base64-encoded PNG"),
    ),
    "alt" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("Image alt text"),
    ),
  ],
)]
final class SetCharacterPortrait extends DataProducerPluginBase implements ContainerFactoryPluginInterface {

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
   * The shared portrait writer.
   *
   * @var \Drupal\dnd_content\Service\PortraitWriter
   */
  protected PortraitWriter $portraitWriter;

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
    $instance->portraitWriter = $container->get('dnd_content.portrait_writer');
    return $instance;
  }

  /**
   * Store the generated portrait on the character.
   *
   * @param string $id
   *   The character node UUID.
   * @param string $image_base64
   *   The base64-encoded PNG image data.
   * @param string $alt
   *   The alt text. Required by the media image field.
   * @param \Drupal\graphql\GraphQL\Execution\FieldContext $context
   *   The GraphQL field execution context.
   *
   * @return \Drupal\node\NodeInterface
   *   The updated character node.
   *
   * @throws \GraphQL\Error\UserError
   *   When the character is missing, the image is invalid, or access denied.
   */
  public function resolve(
    string $id,
    string $image_base64,
    string $alt,
    FieldContext $context,
  ): NodeInterface {
    $data = base64_decode($image_base64, TRUE);
    if ($data === FALSE || $data === '') {
      throw new UserError('Invalid portrait image: expected base64-encoded data.');
    }

    $node = $this->loadCharacter($id);
    if (!$node->access('update', $this->currentUser)) {
      $context->addCacheableDependency($this->currentUser);
      throw new UserError('You do not have permission to update this character.');
    }

    try {
      $this->portraitWriter->attach($node, $data, $alt, (int) $this->currentUser->id());
    }
    catch (\RuntimeException $e) {
      throw new UserError($e->getMessage());
    }

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

}
