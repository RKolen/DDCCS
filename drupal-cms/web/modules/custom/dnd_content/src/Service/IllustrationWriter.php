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
 * Stores a generated story-scene illustration without attaching it.
 *
 * The queued illustration job must not decide for the operator: store() puts
 * the image in the library, assign() appends it to the story's
 * field_illustrations, and a background render that still needs review stops
 * at store().
 */
final class IllustrationWriter {

  /**
   * Directory illustrations are written to, under the public files scheme.
   */
  private const ILLUSTRATION_DIRECTORY = 'public://illustrations';

  /**
   * Constructs an IllustrationWriter.
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
   * Store an illustration in the media library without touching the story.
   *
   * @param \Drupal\node\NodeInterface $node
   *   The story the illustration was rendered for. Used to name the file and
   *   media, not modified.
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
      throw new \RuntimeException('Alt text is required for a story illustration.');
    }
    if ($data === '') {
      throw new \RuntimeException('Illustration image data is empty.');
    }

    $directory = self::ILLUSTRATION_DIRECTORY;
    if (!$this->fileSystem->prepareDirectory(
      $directory,
      FileSystemInterface::CREATE_DIRECTORY | FileSystemInterface::MODIFY_PERMISSIONS
    )) {
      throw new \RuntimeException('Could not prepare the illustration directory.');
    }

    $filename = sprintf('illustration-%s-%d.png', $node->uuid(), time());

    try {
      $file = $this->fileRepository->writeData(
        $data,
        $directory . '/' . $filename,
        FileExists::Rename
      );
    }
    catch (\Exception $e) {
      throw new \RuntimeException('Could not write the illustration file: ' . $e->getMessage(), 0, $e);
    }

    $media = $this->entityTypeManager->getStorage('media')->create([
      'bundle' => 'image',
      'name' => sprintf('Illustration: %s', $node->label()),
      'uid' => $owner_id,
      'status' => 1,
      'field_media_type' => 'story_scenario',
      'field_media_image' => [
        'target_id' => $file->id(),
        'alt' => $alt,
      ],
    ]);
    $media->save();

    return $media;
  }

  /**
   * Append an illustration to a story's gallery.
   *
   * The accept half of a reviewed render. Existing illustrations are kept.
   *
   * @param \Drupal\node\NodeInterface $node
   *   The story node.
   * @param \Drupal\media\MediaInterface $media
   *   The image media entity to append.
   *
   * @throws \RuntimeException
   *   When the story has no illustrations field.
   */
  public function assign(NodeInterface $node, MediaInterface $media): void {
    if (!$node->hasField('field_illustrations')) {
      throw new \RuntimeException('This story has no illustrations field.');
    }
    $existing = $node->get('field_illustrations')->getValue();
    $existing[] = ['target_id' => $media->id()];
    $node->set('field_illustrations', $existing);
    $node->save();
  }

}
