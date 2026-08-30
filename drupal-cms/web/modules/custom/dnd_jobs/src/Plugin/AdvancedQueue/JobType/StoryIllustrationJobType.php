<?php

declare(strict_types=1);

namespace Drupal\dnd_jobs\Plugin\AdvancedQueue\JobType;

use Drupal\advancedqueue\Attribute\AdvancedQueueJobType;
use Drupal\advancedqueue\Job;
use Drupal\advancedqueue\JobResult;
use Drupal\Core\File\FileUrlGeneratorInterface;
use Drupal\Core\StringTranslation\TranslatableMarkup;
use Drupal\dnd_content\Service\IllustrationWriter;
use Drupal\dnd_jobs\Service\JobReview;
use Drupal\file\FileInterface;
use Drupal\media\MediaInterface;
use Symfony\Component\DependencyInjection\ContainerInterface;

/**
 * Renders a story-scene illustration with ComfyUI and stores it for review.
 *
 * The render lands in the media library but is not appended to the story until
 * the operator accepts it, matching the portrait job.
 */
#[AdvancedQueueJobType(
  id: "dnd_story_illustration",
  label: new TranslatableMarkup("Story scene illustration"),
  max_retries: 0,
)]
final class StoryIllustrationJobType extends AiJobTypeBase {

  /**
   * The file URL generator.
   *
   * @var \Drupal\Core\File\FileUrlGeneratorInterface
   */
  protected FileUrlGeneratorInterface $fileUrlGenerator;

  /**
   * The illustration writer.
   *
   * @var \Drupal\dnd_content\Service\IllustrationWriter
   */
  protected IllustrationWriter $illustrationWriter;

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
  ): static {
    $instance = parent::create($container, $configuration, $plugin_id, $plugin_definition);
    $instance->fileUrlGenerator = $container->get('file_url_generator');
    $instance->illustrationWriter = $container->get('dnd_content.illustration_writer');

    return $instance;
  }

  /**
   * {@inheritdoc}
   */
  public function process(Job $job): JobResult {
    $payload = $job->getPayload();

    try {
      $node = $this->loadNode($this->requireString($payload, 'storyId'), 'story');
      $excerpt = $this->requireString($payload, 'excerpt');
      $title = $this->optionalString($payload, 'title') ?? (string) $node->label();

      $response = $this->sidecar->post('/story/scene', [
        'excerpt' => $excerpt,
        'title' => $title,
        'roster' => $this->arrayValue($payload, 'roster'),
        'people' => $this->arrayValue($payload, 'people'),
        'seed' => $this->optionalInt($payload, 'seed'),
        'shot' => $this->optionalString($payload, 'shot') ?? 'full',
        'angle' => $this->optionalString($payload, 'angle') ?? 'three_quarter',
      ]);

      $encoded = $response['image_base64'] ?? NULL;
      $data = is_string($encoded) ? base64_decode($encoded, TRUE) : FALSE;
      if ($data === FALSE || $data === '') {
        return JobResult::failure('The sidecar returned no scene image.');
      }

      $alt = is_string($response['alt'] ?? NULL) && trim((string) $response['alt']) !== ''
        ? (string) $response['alt']
        : sprintf('Illustration of %s', $title);

      $media = $this->illustrationWriter->store($node, $data, $alt, (int) $node->getOwnerId());

      $this->storeResult($job, [
        'storyId' => $node->uuid(),
        'mediaId' => $media->uuid(),
        'imageUrl' => $this->imageUrl($media),
        'alt' => $alt,
        'seed' => is_int($response['seed'] ?? NULL) ? $response['seed'] : NULL,
        'prompt' => is_string($response['prompt'] ?? NULL) ? $response['prompt'] : '',
        'usedIpadapter' => is_int($response['used_ipadapter'] ?? NULL) ? $response['used_ipadapter'] : 0,
        'leadFaces' => is_array($response['lead_faces'] ?? NULL) ? $response['lead_faces'] : [],
        'swappedFaces' => is_array($response['swapped_faces'] ?? NULL) ? $response['swapped_faces'] : [],
        'review' => JobReview::PENDING,
      ]);

      return JobResult::success(sprintf(
        'Scene rendered for %s - review it to attach it.',
        $title,
      ));
    }
    catch (\RuntimeException $e) {
      $this->logger->error('Story illustration job failed: @message', ['@message' => $e->getMessage()]);

      return JobResult::failure($e->getMessage());
    }
  }

  /**
   * Resolve the public URL of a media entity's image file.
   *
   * @param \Drupal\media\MediaInterface $media
   *   The image media entity.
   *
   * @return string|null
   *   The absolute file URL, or NULL when the file cannot be resolved.
   */
  private function imageUrl(MediaInterface $media): ?string {
    if (!$media->hasField('field_media_image')) {
      return NULL;
    }
    $file = $media->get('field_media_image')->entity;
    if (!$file instanceof FileInterface) {
      return NULL;
    }

    return $this->fileUrlGenerator->generateAbsoluteString($file->getFileUri());
  }

}
