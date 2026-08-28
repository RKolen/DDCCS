<?php

declare(strict_types=1);

namespace Drupal\dnd_jobs\Plugin\AdvancedQueue\JobType;

use Drupal\advancedqueue\Attribute\AdvancedQueueJobType;
use Drupal\advancedqueue\Job;
use Drupal\advancedqueue\JobResult;
use Drupal\Core\StringTranslation\TranslatableMarkup;

/**
 * Suggests a story arc's relationships in the background.
 *
 * One model call per party member, so a full side takes minutes and closing
 * the tab would lose an interactive run. As a job the loop happens on the
 * server (console route "run-arc-relations").
 *
 * The suggestions are stored as the job's result rather than written to the
 * arc: saving replaces a whole relation side, so an unattended job must not
 * overwrite bonds the operator wrote by hand. The console applies them through
 * the same accept/reject review the interactive run uses.
 */
#[AdvancedQueueJobType(
  id: "dnd_arc_relations",
  label: new TranslatableMarkup("Arc relationship suggestion"),
  max_retries: 0,
)]
final class ArcRelationsJobType extends AiJobTypeBase {

  /**
   * {@inheritdoc}
   */
  public function process(Job $job): JobResult {
    $payload = $job->getPayload();

    try {
      $subjects = $this->arrayValue($payload, 'subjects');
      $candidates = $this->arrayValue($payload, 'candidates');
      if ($subjects === [] || $candidates === []) {
        return JobResult::failure('Both subjects and candidates are required.');
      }

      $side = $this->optionalString($payload, 'side') === 'npc' ? 'npc' : 'party';
      $arc_id = $this->requireString($payload, 'arcId');

      $response = $this->console->post('run-arc-relations', [
        'arcId' => $arc_id,
        'side' => $side,
        'subjects' => $subjects,
        'candidates' => $candidates,
        'roster' => $this->arrayValue($payload, 'roster'),
        'context' => $this->optionalString($payload, 'context') ?? '',
      ]);

      $suggested = is_array($response['suggested'] ?? NULL) ? $response['suggested'] : [];
      $this->storeResult($job, [
        'arcId' => $arc_id,
        'side' => $side,
        'subjectsRun' => is_int($response['subjectsRun'] ?? NULL) ? $response['subjectsRun'] : 0,
        'suggested' => $suggested,
      ]);

      return JobResult::success(sprintf(
        'Suggested %d %s relationship(s).',
        count($suggested),
        $side,
      ));
    }
    catch (\RuntimeException $e) {
      $this->logger->error('Arc relations job failed: @message', ['@message' => $e->getMessage()]);

      return JobResult::failure($e->getMessage());
    }
  }

}
