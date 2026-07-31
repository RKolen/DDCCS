<?php

declare(strict_types=1);

namespace Drupal\dnd_jobs\Plugin\AdvancedQueue\JobType;

use Drupal\advancedqueue\Attribute\AdvancedQueueJobType;
use Drupal\advancedqueue\Job;
use Drupal\advancedqueue\JobResult;
use Drupal\Core\File\FileUrlGeneratorInterface;
use Drupal\Core\StringTranslation\TranslatableMarkup;
use Drupal\dnd_content\Service\PortraitWriter;
use Drupal\dnd_jobs\Service\JobReview;
use Drupal\file\FileInterface;
use Drupal\media\MediaInterface;
use Symfony\Component\DependencyInjection\ContainerInterface;

/**
 * Generates a character portrait with ComfyUI and stores it for review.
 *
 * The console used to hold this call open for the several minutes a CPU render
 * takes; as a job it survives navigation and runs one at a time with every
 * other heavy AI action, which is what keeps two large models from being
 * resident at once.
 *
 * The render lands in the media library but is deliberately *not* attached: a
 * job finishing while the operator is on another screen must not replace a
 * portrait they were happy with. The result carries review: pending, and the
 * resolveAiJob mutation is what finally attaches or drops it.
 */
#[AdvancedQueueJobType(
  id: "dnd_portrait",
  label: new TranslatableMarkup("Character portrait"),
  max_retries: 0,
)]
final class PortraitJobType extends AiJobTypeBase {

  /**
   * The file URL generator.
   *
   * @var \Drupal\Core\File\FileUrlGeneratorInterface
   */
  protected FileUrlGeneratorInterface $fileUrlGenerator;

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
  ): static {
    $instance = parent::create($container, $configuration, $plugin_id, $plugin_definition);
    $instance->fileUrlGenerator = $container->get('file_url_generator');
    $instance->portraitWriter = $container->get('dnd_content.portrait_writer');

    return $instance;
  }

  /**
   * {@inheritdoc}
   */
  public function process(Job $job): JobResult {
    $payload = $job->getPayload();

    try {
      $node = $this->loadNode($this->requireString($payload, 'characterId'), 'character');

      $response = $this->sidecar->post('/character/portrait', [
        'profile' => $this->arrayValue($payload, 'profile'),
        'positive' => $this->optionalString($payload, 'positive'),
        'negative' => $this->optionalString($payload, 'negative'),
        'seed' => $this->optionalInt($payload, 'seed'),
        'width' => $this->optionalInt($payload, 'width'),
        'height' => $this->optionalInt($payload, 'height'),
        // An existing portrait to keep the likeness of. The sidecar drops back
        // to text-to-image when it cannot use it, so this never fails a job.
        'reference_image_url' => $this->optionalString($payload, 'referenceImageUrl'),
        'identity_weight' => $this->optionalFloat($payload, 'identityWeight'),
      ]);

      $encoded = $response['image_base64'] ?? NULL;
      $data = is_string($encoded) ? base64_decode($encoded, TRUE) : FALSE;
      if ($data === FALSE || $data === '') {
        return JobResult::failure('The sidecar returned no portrait image.');
      }

      $alt = is_string($response['alt'] ?? NULL) && trim((string) $response['alt']) !== ''
        ? (string) $response['alt']
        : sprintf('Portrait of %s', $node->label());

      $media = $this->portraitWriter->store($node, $data, $alt, (int) $node->getOwnerId());

      $this->storeResult($job, [
        'characterId' => $node->uuid(),
        'mediaId' => $media->uuid(),
        'imageUrl' => $this->imageUrl($media),
        'alt' => $alt,
        'seed' => is_int($response['seed'] ?? NULL) ? $response['seed'] : NULL,
        // Whether the render actually kept the previous portrait's likeness.
        // Reported rather than assumed: asking for it is not the same as
        // getting it, and the console should not claim a likeness it lacks.
        'usedReference' => ($response['used_reference'] ?? FALSE) === TRUE,
        'review' => JobReview::PENDING,
      ]);

      return JobResult::success(sprintf('Portrait rendered for %s - review it to attach it.', $node->label()));
    }
    catch (\RuntimeException $e) {
      $this->logger->error('Portrait job failed: @message', ['@message' => $e->getMessage()]);

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
