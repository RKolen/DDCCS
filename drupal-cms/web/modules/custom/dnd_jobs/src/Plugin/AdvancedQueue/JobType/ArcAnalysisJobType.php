<?php

declare(strict_types=1);

namespace Drupal\dnd_jobs\Plugin\AdvancedQueue\JobType;

use Drupal\advancedqueue\Attribute\AdvancedQueueJobType;
use Drupal\advancedqueue\Job;
use Drupal\advancedqueue\JobResult;
use Drupal\Core\StringTranslation\TranslatableMarkup;

/**
 * Runs a character's arc analysis to completion in the background.
 *
 * The console used to loop passage by passage in the browser, so closing the
 * tab lost a run that can take many minutes. As a job the loop happens on the
 * server (console route "run-arc-analysis"), each story is persisted as it
 * finishes, and the arc is saved onto the character at the end.
 */
#[AdvancedQueueJobType(
  id: "dnd_arc_analysis",
  label: new TranslatableMarkup("Character arc analysis"),
  max_retries: 0,
)]
final class ArcAnalysisJobType extends AiJobTypeBase {

  /**
   * {@inheritdoc}
   */
  public function process(Job $job): JobResult {
    $payload = $job->getPayload();

    try {
      $story_ids = array_values(array_filter(
        $this->arrayValue($payload, 'storyIds'),
        static fn (mixed $id): bool => is_string($id) && trim($id) !== '',
      ));
      if ($story_ids === []) {
        return JobResult::failure('No stories were supplied to analyse.');
      }

      $character_name = $this->requireString($payload, 'characterName');
      $response = $this->console->post('run-arc-analysis', [
        'characterName' => $character_name,
        'campaignId' => $this->optionalString($payload, 'campaignId') ?? '',
        'characterId' => $this->requireString($payload, 'characterId'),
        'pronouns' => $this->optionalString($payload, 'pronouns') ?? '',
        'storyIds' => $story_ids,
      ]);

      $analysed = is_int($response['storiesAnalysed'] ?? NULL) ? $response['storiesAnalysed'] : 0;
      $this->storeResult($job, [
        'characterId' => $this->requireString($payload, 'characterId'),
        'storiesAnalysed' => $analysed,
        'direction' => $response['direction'] ?? NULL,
        'stage' => $response['stage'] ?? NULL,
        'summary' => $response['summary'] ?? NULL,
      ]);

      return JobResult::success(sprintf('Arc analysed for %s (%d stories).', $character_name, $analysed));
    }
    catch (\RuntimeException $e) {
      $this->logger->error('Arc analysis job failed: @message', ['@message' => $e->getMessage()]);

      return JobResult::failure($e->getMessage());
    }
  }

}
