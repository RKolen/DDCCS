<?php

declare(strict_types=1);

namespace Drupal\dnd_jobs\Plugin\AdvancedQueue\JobType;

use Drupal\advancedqueue\Attribute\AdvancedQueueJobType;
use Drupal\advancedqueue\Job;
use Drupal\advancedqueue\JobResult;
use Drupal\Core\StringTranslation\TranslatableMarkup;

/**
 * Generates a session story in the background.
 *
 * The streamed version needs the console to stay open for the whole run. As a
 * job the story is written by the console route "generate-story-text" and
 * stored on the job, so it is waiting to be reviewed and saved whenever you
 * come back - the review step is unchanged, only the waiting is.
 */
#[AdvancedQueueJobType(
  id: "dnd_story_generation",
  label: new TranslatableMarkup("Story generation"),
  max_retries: 0,
)]
final class StoryGenerationJobType extends AiJobTypeBase {

  /**
   * {@inheritdoc}
   */
  public function process(Job $job): JobResult {
    $payload = $job->getPayload();

    try {
      $request = $this->arrayValue($payload, 'story');
      if ($request === []) {
        return JobResult::failure('Job payload is missing the story request.');
      }

      $response = $this->console->post('generate-story-text', $request);
      $text = is_string($response['text'] ?? NULL) ? trim((string) $response['text']) : '';
      if ($text === '') {
        return JobResult::failure('The model returned no story text.');
      }

      $this->storeResult($job, [
        'campaignId' => $this->optionalString($payload, 'campaignId'),
        'storyNumber' => $this->optionalInt($payload, 'storyNumber'),
        'text' => $text,
      ]);

      return JobResult::success(sprintf('Story generated (%d characters).', mb_strlen($text)));
    }
    catch (\RuntimeException $e) {
      $this->logger->error('Story generation job failed: @message', ['@message' => $e->getMessage()]);

      return JobResult::failure($e->getMessage());
    }
  }

}
