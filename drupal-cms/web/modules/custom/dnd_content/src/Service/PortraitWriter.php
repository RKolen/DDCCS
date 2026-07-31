<?php

declare(strict_types=1);

namespace Drupal\dnd_content\Service;

use Drupal\Core\Entity\EntityTypeManagerInterface;
use Drupal\Core\File\FileExists;
use Drupal\Core\File\FileSystemInterface;
use Drupal\file\FileRepositoryInterface;
use Drupal\media\MediaInterface;
use Drupal\node\NodeInterface;

/**
 * Stores a generated portrait image on a character node.
 *
 * Writes the decoded image as a managed file, wraps it in an image media
 * entity tagged with the right media type, and points the character's
 * field_image at it. Shared by the setCharacterPortrait GraphQL mutation (a
 * request-time write) and the queued portrait job (a background write), so both
 * paths produce identical file, media, and field state.
 *
 * The two halves are separately callable, because a background render must not
 * decide for the operator: store() puts the image in the library, assign()
 * makes it the character's portrait, and attach() does both for the callers
 * that were explicitly asked to.
 */
final class PortraitWriter {

  /**
   * Directory portraits are written to, under the public files scheme.
   */
  private const PORTRAIT_DIRECTORY = 'public://portraits';

  /**
   * Constructs a PortraitWriter.
   *
   * @param \Drupal\Core\Entity\EntityTypeManagerInterface $entityTypeManager
   *   The entity type manager.
   * @param \Drupal\file\FileRepositoryInterface $fileRepository
   *   The file repository.
   * @param \Drupal\Core\File\FileSystemInterface $fileSystem
   *   The file system.
   */
  public function __construct(
    private readonly EntityTypeManagerInterface $entityTypeManager,
    private readonly FileRepositoryInterface $fileRepository,
    private readonly FileSystemInterface $fileSystem,
  ) {}

  /**
   * Attach a portrait image to a character, replacing any previous reference.
   *
   * Stores and assigns in one step. Use this for a write the operator has
   * already asked for; a generated render that still needs review should call
   * store() now and assign() only once it is accepted.
   *
   * @param \Drupal\node\NodeInterface $node
   *   The character node to attach the portrait to.
   * @param string $data
   *   The raw (already decoded) image bytes.
   * @param string $alt
   *   The alt text. Required by the media image field.
   * @param int $owner_id
   *   The user id to own the new file and media entities.
   *
   * @return \Drupal\media\MediaInterface
   *   The saved image media entity now referenced by field_image.
   *
   * @throws \RuntimeException
   *   When the alt text is empty, or the directory or file cannot be written.
   */
  public function attach(NodeInterface $node, string $data, string $alt, int $owner_id): MediaInterface {
    $media = $this->store($node, $data, $alt, $owner_id);
    $this->assign($node, $media);

    return $media;
  }

  /**
   * Store a portrait in the media library without touching the character.
   *
   * This is the half of the write that is safe to do unattended: the render
   * lands in the library, but the character keeps the portrait it already has
   * until somebody accepts the new one. The queued portrait job stops here so a
   * background render can never silently replace a portrait the operator was
   * happy with.
   *
   * @param \Drupal\node\NodeInterface $node
   *   The character the portrait was rendered for. Used to name and type the
   *   file and media, not modified.
   * @param string $data
   *   The raw (already decoded) image bytes.
   * @param string $alt
   *   The alt text. Required by the media image field.
   * @param int $owner_id
   *   The user id to own the new file and media entities.
   *
   * @return \Drupal\media\MediaInterface
   *   The saved image media entity.
   *
   * @throws \RuntimeException
   *   When the alt text is empty, or the directory or file cannot be written.
   */
  public function store(NodeInterface $node, string $data, string $alt, int $owner_id): MediaInterface {
    $alt = trim($alt);
    if ($alt === '') {
      throw new \RuntimeException('Alt text is required for a portrait image.');
    }
    if ($data === '') {
      throw new \RuntimeException('Portrait image data is empty.');
    }

    return $this->createMedia($node, $data, $alt, $owner_id);
  }

  /**
   * Point a character's portrait at an image media entity.
   *
   * The accept half of a reviewed render, and the only step that changes what
   * the character shows.
   *
   * @param \Drupal\node\NodeInterface $node
   *   The character node to attach the portrait to.
   * @param \Drupal\media\MediaInterface $media
   *   The image media entity to reference.
   */
  public function assign(NodeInterface $node, MediaInterface $media): void {
    $node->set('field_image', ['target_id' => $media->id()]);
    $node->save();
  }

  /**
   * Write the image as a managed file and wrap it in an image media entity.
   *
   * @param \Drupal\node\NodeInterface $node
   *   The character the portrait belongs to, used to name the file and media.
   * @param string $data
   *   The raw (decoded) image bytes.
   * @param string $alt
   *   The alt text.
   * @param int $owner_id
   *   The user id to own the new file and media entities.
   *
   * @return \Drupal\media\MediaInterface
   *   The saved image media entity.
   *
   * @throws \RuntimeException
   *   When the destination directory or file cannot be written.
   */
  private function createMedia(NodeInterface $node, string $data, string $alt, int $owner_id): MediaInterface {
    // prepareDirectory() takes the directory by reference, so it needs a
    // variable rather than the class constant directly.
    $directory = self::PORTRAIT_DIRECTORY;
    if (!$this->fileSystem->prepareDirectory(
      $directory,
      FileSystemInterface::CREATE_DIRECTORY | FileSystemInterface::MODIFY_PERMISSIONS
    )) {
      throw new \RuntimeException('Could not prepare the portrait directory.');
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
      throw new \RuntimeException('Could not write the portrait file: ' . $e->getMessage(), 0, $e);
    }

    // Type the media so it shows under the right filter in the portrait picker.
    $is_pc = (bool) $node->get('field_character_type')->value;
    $media_type = $is_pc ? 'character_portrait' : 'npc_portrait';

    $media = $this->entityTypeManager->getStorage('media')->create([
      'bundle' => 'image',
      'name' => sprintf('Portrait: %s', $node->label()),
      'uid' => $owner_id,
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
