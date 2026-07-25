<?php

declare(strict_types=1);

namespace Drupal\dnd_content\Plugin\GraphQL\DataProducer;

use Drupal\Core\Entity\EntityTypeManagerInterface;
use Drupal\Core\File\FileExists;
use Drupal\Core\File\FileSystemInterface;
use Drupal\Core\Plugin\ContainerFactoryPluginInterface;
use Drupal\Core\Plugin\Context\ContextDefinition;
use Drupal\Core\Session\AccountInterface;
use Drupal\Core\StringTranslation\TranslatableMarkup;
use Drupal\file\FileRepositoryInterface;
use Drupal\graphql\Attribute\DataProducer;
use Drupal\graphql\GraphQL\Execution\FieldContext;
use Drupal\graphql\Plugin\GraphQL\DataProducer\DataProducerPluginBase;
use Drupal\media\MediaInterface;
use Drupal\node\NodeInterface;
use GraphQL\Error\UserError;
use Symfony\Component\DependencyInjection\ContainerInterface;

/**
 * Attaches a generated portrait image to a character node.
 *
 * Decodes a base64 PNG produced by the sidecar's ComfyUI endpoint, writes it as
 * a managed file, wraps it in an image media entity, and points the character's
 * field_image at that media. Returns the updated node.
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
   * Directory portraits are written to, under the public files scheme.
   */
  private const PORTRAIT_DIRECTORY = 'public://portraits';

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
   * The file repository.
   *
   * @var \Drupal\file\FileRepositoryInterface
   */
  protected FileRepositoryInterface $fileRepository;

  /**
   * The file system.
   *
   * @var \Drupal\Core\File\FileSystemInterface
   */
  protected FileSystemInterface $fileSystem;

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
    $instance->fileRepository = $container->get('file.repository');
    $instance->fileSystem = $container->get('file_system');
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
    $alt = trim($alt);
    if ($alt === '') {
      throw new UserError('Alt text is required for a portrait image.');
    }

    $data = base64_decode($image_base64, TRUE);
    if ($data === FALSE || $data === '') {
      throw new UserError('Invalid portrait image: expected base64-encoded data.');
    }

    $node = $this->loadCharacter($id);
    if (!$node->access('update', $this->currentUser)) {
      $context->addCacheableDependency($this->currentUser);
      throw new UserError('You do not have permission to update this character.');
    }

    $media = $this->createPortraitMedia($node, $data, $alt);

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
   * Write the image as a managed file and wrap it in an image media entity.
   *
   * @param \Drupal\node\NodeInterface $node
   *   The character the portrait belongs to, used to name the file and media.
   * @param string $data
   *   The raw (decoded) PNG bytes.
   * @param string $alt
   *   The alt text.
   *
   * @return \Drupal\media\MediaInterface
   *   The saved image media entity.
   *
   * @throws \GraphQL\Error\UserError
   *   When the destination directory or file cannot be written.
   */
  private function createPortraitMedia(NodeInterface $node, string $data, string $alt): MediaInterface {
    // prepareDirectory() takes the directory by reference, so it needs a
    // variable rather than the class constant directly.
    $directory = self::PORTRAIT_DIRECTORY;
    if (!$this->fileSystem->prepareDirectory(
      $directory,
      FileSystemInterface::CREATE_DIRECTORY | FileSystemInterface::MODIFY_PERMISSIONS
    )) {
      throw new UserError('Could not prepare the portrait directory.');
    }

    // Timestamped so regenerating a portrait never overwrites the previous
    // file, which older revisions may still reference.
    $filename = sprintf('portrait-%s-%d.png', $node->uuid(), time());

    try {
      $file = $this->fileRepository->writeData(
        $data,
        $directory . '/' . $filename,
        FileExists::Rename
      );
    }
    catch (\Exception $e) {
      throw new UserError('Could not write the portrait file: ' . $e->getMessage());
    }

    // Type the media so it shows under the right filter in the portrait picker.
    $is_pc = (bool) $node->get('field_character_type')->value;
    $media_type = $is_pc ? 'character_portrait' : 'npc_portrait';

    $media = $this->entityTypeManager->getStorage('media')->create([
      'bundle' => 'image',
      'name' => sprintf('Portrait: %s', $node->label()),
      'uid' => $this->currentUser->id(),
      'status' => 1,
      'field_media_type' => $media_type,
      'field_media_image' => [
        'target_id' => $file->id(),
        'alt' => $alt,
      ],
    ]);
    $media->save();

    return $media;
  }

}
