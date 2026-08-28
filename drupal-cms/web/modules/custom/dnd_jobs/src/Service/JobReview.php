<?php

declare(strict_types=1);

namespace Drupal\dnd_jobs\Service;

use Drupal\Core\Entity\EntityTypeManagerInterface;
use Drupal\Core\Session\AccountInterface;
use Drupal\dnd_content\Service\IllustrationWriter;
use Drupal\dnd_content\Service\PortraitWriter;
use Drupal\media\MediaInterface;
use Drupal\node\NodeInterface;

/**
 * Applies or drops a finished job's result once somebody has looked at it.
 *
 * A queued job runs unattended, so it may finish while the operator is on a
 * different screen entirely - or not at the console at all. Writing its output
 * straight onto the content would mean a background render silently replacing a
 * portrait somebody was happy with, so job types that produce something
 * reviewable stop one step short and mark their result "pending". This service
 * is the other half: accept applies it, discard leaves the content alone, and
 * either way the decision is recorded on the job so the activity bar stops
 * asking.
 *
 * Discarding is not destructive. The render stays in the media library and can
 * still be picked later from the portrait picker; only the character's
 * field_image is left untouched.
 */
final class JobReview {

  /**
   * Result marker for a finished job nobody has accepted or discarded yet.
   */
  public const PENDING = 'pending';

  /**
   * Result marker for a result that has been applied to the content.
   */
  public const ACCEPTED = 'accepted';

  /**
   * Result marker for a result the operator chose not to apply.
   */
  public const DISCARDED = 'discarded';

  /**
   * The decision that applies a result.
   */
  public const ACCEPT = 'accept';

  /**
   * The decision that leaves a result unapplied.
   */
  public const DISCARD = 'discard';

  /**
   * Job types whose result the console applies itself.
   *
   * A portrait is written onto the character here, server-side, because the
   * media already exists and only Drupal can attach it. An arc result is
   * different: the console loads it into an editable review - relations into
   * the relation tables, a drafted arc into its form - and the operator saves
   * from there, through the ordinary write paths. Accepting one of these is
   * therefore only a bookkeeping flip, so the activity bar stops offering a
   * decision that has already been made.
   */
  private const CONSOLE_APPLIED_TYPES = [
    'dnd_arc_relations',
    'dnd_arc_backfill',
    'dnd_story_events',
  ];

  /**
   * Constructs a JobReview.
   *
   * @param \Drupal\dnd_jobs\Service\JobQueue $jobQueue
   *   The AI job queue.
   * @param \Drupal\Core\Entity\EntityTypeManagerInterface $entityTypeManager
   *   The entity type manager.
   * @param \Drupal\dnd_content\Service\PortraitWriter $portraitWriter
   *   The shared portrait writer.
   * @param \Drupal\dnd_content\Service\IllustrationWriter $illustrationWriter
   *   The shared illustration writer.
   * @param \Drupal\Core\Session\AccountInterface $currentUser
   *   The current user, checked for update access on the target content.
   */
  public function __construct(
    private readonly JobQueue $jobQueue,
    private readonly EntityTypeManagerInterface $entityTypeManager,
    private readonly PortraitWriter $portraitWriter,
    private readonly IllustrationWriter $illustrationWriter,
    private readonly AccountInterface $currentUser,
  ) {}

  /**
   * Accept or discard a finished job's pending result.
   *
   * Repeating a decision is a no-op that succeeds: the caller asked for a state
   * the job is already in, and failing would leave the console stuck showing a
   * result it has in fact dealt with. Only a contradicting decision is an
   * error, because that one the operator needs to know about.
   *
   * @param string $job_id
   *   The job id.
   * @param bool $accepted
   *   TRUE to apply the result to the content, FALSE to leave it unapplied.
   *
   * @return array<string, mixed>
   *   The updated job record.
   *
   * @throws \RuntimeException
   *   When the job is missing, unfinished, has nothing reviewable, was already
   *   decided the other way, is of a type that produces nothing reviewable, or
   *   the user cannot update the target.
   */
  public function resolve(string $job_id, bool $accepted): array {
    $job = $this->jobQueue->load($job_id);
    if ($job === NULL) {
      throw new \RuntimeException(sprintf('No job found with id %s.', $job_id));
    }
    if (($job['state'] ?? '') !== 'success') {
      throw new \RuntimeException('Only a job that finished successfully has a result to review.');
    }

    $result = json_decode((string) ($job['result'] ?? ''), TRUE);
    if (!is_array($result)) {
      throw new \RuntimeException('This job produced no result to review.');
    }

    // A result stored without a marker has not been decided by anyone, so it
    // is pending. Only the portrait job type has ever written one, which left
    // every other reviewable result unresolvable.
    $review = $result['review'] ?? self::PENDING;
    $wanted = $accepted ? self::ACCEPTED : self::DISCARDED;
    if ($review === $wanted) {
      return $job;
    }
    if ($review !== self::PENDING) {
      throw new \RuntimeException(sprintf(
        'This result was already %s and cannot be %s now.',
        is_string($review) ? $review : 'applied',
        $wanted
      ));
    }

    if ($accepted) {
      $this->apply((string) ($job['type'] ?? ''), $result);
    }

    $updated = $this->jobQueue->updateResult($job_id, [
      'review' => $accepted ? self::ACCEPTED : self::DISCARDED,
    ]);

    return $updated ?? $job;
  }

  /**
   * Write a pending result onto the content it belongs to.
   *
   * @param string $type
   *   The job type plugin id.
   * @param array<string, mixed> $result
   *   The pending result values.
   *
   * @throws \RuntimeException
   *   When the job type has no reviewable output, the referenced content is
   *   gone, or the user cannot update it.
   */
  private function apply(string $type, array $result): void {
    if (in_array($type, self::CONSOLE_APPLIED_TYPES, TRUE)) {
      return;
    }
    if ($type === 'dnd_story_illustration') {
      $node = $this->loadStory($this->requireString($result, 'storyId'));
      if (!$node->access('update', $this->currentUser)) {
        throw new \RuntimeException('You do not have permission to update this story.');
      }
      $this->illustrationWriter->assign($node, $this->loadImageMedia($this->requireString($result, 'mediaId')));
      return;
    }
    if ($type !== 'dnd_portrait') {
      throw new \RuntimeException(sprintf('Job type %s produces nothing to review.', $type));
    }

    $node = $this->loadCharacter($this->requireString($result, 'characterId'));
    if (!$node->access('update', $this->currentUser)) {
      throw new \RuntimeException('You do not have permission to update this character.');
    }

    $this->portraitWriter->assign($node, $this->loadImageMedia($this->requireString($result, 'mediaId')));
  }

  /**
   * Read a required string from a result payload.
   *
   * @param array<string, mixed> $result
   *   The result values.
   * @param string $key
   *   The key to read.
   *
   * @return string
   *   The trimmed value.
   *
   * @throws \RuntimeException
   *   When the key is missing or blank.
   */
  private function requireString(array $result, string $key): string {
    $value = $result[$key] ?? NULL;
    if (!is_string($value) || trim($value) === '') {
      throw new \RuntimeException(sprintf('The job result is missing "%s".', $key));
    }

    return trim($value);
  }

  /**
   * Load a character node by UUID.
   *
   * @param string $uuid
   *   The character node UUID.
   *
   * @return \Drupal\node\NodeInterface
   *   The character node.
   *
   * @throws \RuntimeException
   *   When no character matches the UUID.
   */
  private function loadCharacter(string $uuid): NodeInterface {
    $nodes = $this->entityTypeManager
      ->getStorage('node')
      ->loadByProperties(['uuid' => $uuid, 'type' => 'character']);
    $node = reset($nodes);
    if (!$node instanceof NodeInterface) {
      throw new \RuntimeException('The character this result belongs to no longer exists.');
    }

    return $node;
  }

  /**
   * Load a story node by UUID.
   *
   * @param string $uuid
   *   The story node UUID.
   *
   * @return \Drupal\node\NodeInterface
   *   The story node.
   *
   * @throws \RuntimeException
   *   When no story matches the UUID.
   */
  private function loadStory(string $uuid): NodeInterface {
    $nodes = $this->entityTypeManager
      ->getStorage('node')
      ->loadByProperties(['uuid' => $uuid, 'type' => 'story']);
    $node = reset($nodes);
    if (!$node instanceof NodeInterface) {
      throw new \RuntimeException('The story this result belongs to no longer exists.');
    }

    return $node;
  }

  /**
   * Load an image media entity by UUID.
   *
   * @param string $uuid
   *   The image media UUID.
   *
   * @return \Drupal\media\MediaInterface
   *   The image media entity.
   *
   * @throws \RuntimeException
   *   When no image media matches the UUID.
   */
  private function loadImageMedia(string $uuid): MediaInterface {
    $entities = $this->entityTypeManager
      ->getStorage('media')
      ->loadByProperties(['uuid' => $uuid, 'bundle' => 'image']);
    $media = reset($entities);
    if (!$media instanceof MediaInterface) {
      throw new \RuntimeException('The generated image no longer exists in the media library.');
    }

    return $media;
  }

}
