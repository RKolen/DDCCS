<?php

declare(strict_types=1);

namespace Drupal\dnd_jobs\Plugin\AdvancedQueue\JobType;

use Drupal\advancedqueue\Attribute\AdvancedQueueJobType;
use Drupal\advancedqueue\Job;
use Drupal\advancedqueue\JobResult;
use Drupal\Core\StringTranslation\TranslatableMarkup;
use Drupal\dnd_jobs\Service\JobReview;
use Drupal\node\NodeInterface;

/**
 * Extracts selectable key events from a story body.
 *
 * A session will not fit a local context window, so the sidecar chunks it.
 * The result is a list of events for the console to pick from; nothing is
 * written onto the story.
 */
#[AdvancedQueueJobType(
  id: "dnd_story_events",
  label: new TranslatableMarkup("Story event extraction"),
  max_retries: 0,
)]
final class StoryEventsJobType extends AiJobTypeBase {

  /**
   * {@inheritdoc}
   */
  public function process(Job $job): JobResult {
    $payload = $job->getPayload();

    try {
      $node = $this->loadNode($this->requireString($payload, 'storyId'), 'story');
      $body = $this->storyBody($node);
      if (trim($body) === '') {
        return JobResult::failure('This story has no text to illustrate.');
      }

      $response = $this->sidecar->post('/story/events', [
        'body' => $body,
        'title' => (string) $node->label(),
        'roster' => $this->arrayValue($payload, 'roster'),
      ]);

      $events = is_array($response['events'] ?? NULL) ? $response['events'] : [];
      $this->storeResult($job, [
        'review' => JobReview::PENDING,
        'storyId' => $node->uuid(),
        'title' => (string) $node->label(),
        'events' => $events,
      ]);

      // Proposing nothing is an empty result, not a failure: the console falls
      // back to letting the operator pick a passage themselves.
      if ($events === []) {
        return JobResult::success(sprintf(
          'No events proposed in %s; pick a passage yourself.',
          $node->label(),
        ));
      }

      return JobResult::success(sprintf(
        'Found %d event(s) in %s.',
        count($events),
        $node->label(),
      ));
    }
    catch (\RuntimeException $e) {
      $this->logger->error('Story events job failed: @message', ['@message' => $e->getMessage()]);

      return JobResult::failure($e->getMessage());
    }
  }

  /**
   * Read a story node's body as HTML or plain text.
   *
   * @param \Drupal\node\NodeInterface $node
   *   The story node.
   *
   * @return string
   *   The body, empty when the field is missing or blank.
   */
  private function storyBody(NodeInterface $node): string {
    if (!$node->hasField('field_body') || $node->get('field_body')->isEmpty()) {
      return '';
    }
    $item = $node->get('field_body')->first();
    if ($item === NULL) {
      return '';
    }
    $processed = $item->processed ?? NULL;
    if (is_string($processed) && trim($processed) !== '') {
      return $processed;
    }
    $value = $item->value ?? '';

    return is_string($value) ? $value : '';
  }

}
