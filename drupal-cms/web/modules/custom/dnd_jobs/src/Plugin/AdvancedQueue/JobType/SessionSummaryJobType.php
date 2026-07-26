<?php

declare(strict_types=1);

namespace Drupal\dnd_jobs\Plugin\AdvancedQueue\JobType;

use Drupal\advancedqueue\Attribute\AdvancedQueueJobType;
use Drupal\advancedqueue\Job;
use Drupal\advancedqueue\JobResult;
use Drupal\Core\StringTranslation\TranslatableMarkup;

/**
 * Summarises one session and stores it on the campaign, in the background.
 *
 * A summary is a derived field rather than something to review, so the console
 * route "store-session-summary" both writes it and saves it; the job carries
 * the text back only so the console can show what landed.
 */
#[AdvancedQueueJobType(
  id: "dnd_session_summary",
  label: new TranslatableMarkup("Session summary"),
  max_retries: 0,
)]
final class SessionSummaryJobType extends AiJobTypeBase {

  /**
   * {@inheritdoc}
   */
  public function process(Job $job): JobResult {
    $payload = $job->getPayload();

    try {
      $story_number = $this->optionalInt($payload, 'storyNumber');
      if ($story_number === NULL) {
        return JobResult::failure('Job payload is missing "storyNumber".');
      }

      $response = $this->console->post('store-session-summary', [
        'campaignId' => $this->requireString($payload, 'campaignId'),
        'storyNumber' => $story_number,
        'storyBody' => $this->requireString($payload, 'storyBody'),
      ]);

      $summary = is_string($response['summary'] ?? NULL) ? trim((string) $response['summary']) : '';
      if ($summary === '') {
        return JobResult::failure('The model returned no summary.');
      }

      $this->storeResult($job, [
        'campaignId' => $this->requireString($payload, 'campaignId'),
        'storyNumber' => $story_number,
        'summary' => $summary,
      ]);

      return JobResult::success(sprintf('Session %d summarised.', $story_number));
    }
    catch (\RuntimeException $e) {
      $this->logger->error('Session summary job failed: @message', ['@message' => $e->getMessage()]);

      return JobResult::failure($e->getMessage());
    }
  }

}
