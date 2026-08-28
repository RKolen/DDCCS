<?php

declare(strict_types=1);

namespace Drupal\dnd_jobs\Plugin\AdvancedQueue\JobType;

use Drupal\advancedqueue\Attribute\AdvancedQueueJobType;
use Drupal\advancedqueue\Job;
use Drupal\advancedqueue\JobResult;
use Drupal\Core\StringTranslation\TranslatableMarkup;
use Drupal\dnd_jobs\Service\JobReview;

/**
 * Drafts a story arc for an already-played campaign, in the background.
 *
 * A campaign that predates the arc feature has to be summarised session by
 * session before its arc can be read out of it, which is one model call per
 * session and far too long to hold a browser open. As a job the loop happens
 * on the server (console route "run-arc-backfill").
 *
 * The proposal is stored as the job's result rather than written: an arc is
 * the plan a campaign's stories hang off, so an unattended job must never
 * create one nobody has read. The console reviews and edits it, and only an
 * explicit accept creates the node.
 */
#[AdvancedQueueJobType(
  id: "dnd_arc_backfill",
  label: new TranslatableMarkup("Story arc backfill"),
  max_retries: 0,
)]
final class ArcBackfillJobType extends AiJobTypeBase {

  /**
   * {@inheritdoc}
   */
  public function process(Job $job): JobResult {
    $payload = $job->getPayload();

    try {
      $stories = $this->arrayValue($payload, 'stories');
      if ($stories === []) {
        return JobResult::failure('The campaign has no stories to draft an arc from.');
      }

      $campaign_id = $this->requireString($payload, 'campaignId');
      $response = $this->console->post('run-arc-backfill', [
        'campaignId' => $campaign_id,
        'campaignName' => $this->optionalString($payload, 'campaignName') ?? '',
        'stories' => $stories,
        'party' => $this->arrayValue($payload, 'party'),
        'npcs' => $this->arrayValue($payload, 'npcs'),
      ]);

      $draft = is_array($response['draft'] ?? NULL) ? $response['draft'] : NULL;
      $summarised = is_int($response['summarised'] ?? NULL) ? $response['summarised'] : 0;
      $this->storeResult($job, [
        'review' => JobReview::PENDING,
        'campaignId' => $campaign_id,
        'summarised' => $summarised,
        'recapsUsed' => is_int($response['recapsUsed'] ?? NULL) ? $response['recapsUsed'] : 0,
        'draft' => $draft,
        'cast' => is_array($response['cast'] ?? NULL) ? $response['cast'] : [],
      ]);

      if ($draft === NULL) {
        return JobResult::failure(sprintf(
          'Summarised %d session(s) but the model proposed no arc.',
          $summarised,
        ));
      }

      return JobResult::success(sprintf(
        'Drafted an arc from %d session(s); %d newly summarised.',
        is_int($response['recapsUsed'] ?? NULL) ? $response['recapsUsed'] : 0,
        $summarised,
      ));
    }
    catch (\RuntimeException $e) {
      $this->logger->error('Arc backfill job failed: @message', ['@message' => $e->getMessage()]);

      return JobResult::failure($e->getMessage());
    }
  }

}
