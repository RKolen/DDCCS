<?php

declare(strict_types=1);

namespace Drupal\dnd_jobs\Service;

use Drupal\advancedqueue\Entity\QueueInterface;
use Drupal\advancedqueue\Job;
use Drupal\Component\Datetime\TimeInterface;
use Drupal\Core\Database\Connection;
use Drupal\Core\Database\Statement\FetchAs;
use Drupal\Core\Entity\EntityTypeManagerInterface;

/**
 * Enqueues and reads back the D&D AI jobs.
 *
 * Everything heavy goes through the single "dnd_ai" queue, which is what
 * serializes the work: one processor claims one job at a time, so two large
 * models are never resident at once on this CPU-only box.
 *
 * Listing jobs is a direct table read because the Advanced Queue backends only
 * expose counting and single-job loading; the module's own admin views read the
 * same table the same way.
 */
final class JobQueue {

  /**
   * The queue every heavy AI job is enqueued on.
   */
  public const QUEUE_ID = 'dnd_ai';

  /**
   * The Advanced Queue job table.
   */
  private const TABLE = 'advancedqueue';

  /**
   * How many times a stalled job is automatically put back on the queue.
   *
   * A job that stalls once deserves another go: the usual cause is a restarted
   * sidecar or a host hiccup, and the work itself is fine. A job that stalls
   * every time is different - requeueing it forever would park it at the
   * head of a single-threaded queue and starve everything behind it. After
   * this many attempts it is failed with a timeout message instead.
   */
  public const MAX_STALL_RETRIES = 2;

  /**
   * Constructs a JobQueue.
   *
   * @param \Drupal\Core\Entity\EntityTypeManagerInterface $entityTypeManager
   *   The entity type manager.
   * @param \Drupal\Core\Database\Connection $database
   *   The database connection.
   * @param \Drupal\Component\Datetime\TimeInterface $time
   *   The time service, used to date requeued jobs and spot expired leases.
   */
  public function __construct(
    private readonly EntityTypeManagerInterface $entityTypeManager,
    private readonly Connection $database,
    private readonly TimeInterface $time,
  ) {}

  /**
   * Enqueue a job of the given type.
   *
   * @param string $type
   *   The job type plugin id (e.g. "dnd_portrait").
   * @param array<string, mixed> $payload
   *   The job payload. A "label" key is used as the job's display name in the
   *   console activity bar.
   *
   * @return array<string, mixed>
   *   The normalised job record, as returned by describe().
   *
   * @throws \RuntimeException
   *   When the queue is missing or the job cannot be enqueued.
   */
  public function enqueue(string $type, array $payload): array {
    $job = Job::create($type, $payload);
    $this->queue()->enqueueJob($job);

    return $this->describe($job);
  }

  /**
   * Load a single job by id.
   *
   * @param string $job_id
   *   The job id.
   *
   * @return array<string, mixed>|null
   *   The normalised job record, or NULL when no such job exists.
   */
  public function load(string $job_id): ?array {
    $row = $this->database->select(self::TABLE, 'aq')
      ->fields('aq')
      ->condition('queue_id', self::QUEUE_ID)
      ->condition('job_id', $job_id)
      ->execute()
      ?->fetchAssoc();

    return is_array($row) ? $this->describeRow($row) : NULL;
  }

  /**
   * Put a job back on the queue, whatever state it is in.
   *
   * The safety valve for a job whose worker went away mid-run: the processor
   * claims a job, calls out to the host, and if that call never returns (the
   * sidecar restarted, the host rebooted) the row sits in "processing"
   * holding a lease nobody is honouring. Requeueing clears the claim so the
   * next processor pass runs it again.
   *
   * The payload is left alone, including any result from an earlier attempt:
   * the job type overwrites it when it next succeeds.
   *
   * @param string $job_id
   *   The job id.
   * @param int|null $attempts
   *   The attempt count to record, when this recovery should count against
   *   MAX_STALL_RETRIES. NULL leaves the count alone, which is what an operator
   *   pressing Requeue gets: a deliberate retry is not the queue giving up on
   *   its own.
   *
   * @return array<string, mixed>|null
   *   The requeued job record, or NULL when no such job exists.
   */
  public function requeue(string $job_id, ?int $attempts = NULL): ?array {
    $fields = [
      'state' => Job::STATE_QUEUED,
      'available' => $this->time->getRequestTime(),
      'expires' => 0,
      'processed' => 0,
      'message' => '',
    ];
    if ($attempts !== NULL) {
      $fields['num_retries'] = $attempts;
    }

    $affected = $this->database->update(self::TABLE)
      ->fields($fields)
      ->condition('queue_id', self::QUEUE_ID)
      ->condition('job_id', $job_id)
      ->execute();

    return $affected > 0 ? $this->load($job_id) : NULL;
  }

  /**
   * Recover every job whose processing lease has expired.
   *
   * Runs on cron so a job orphaned by a dead worker recovers on its own rather
   * than waiting for somebody to notice it in the activity bar. A job that is
   * genuinely still running holds an unexpired lease and is left alone, so this
   * cannot start a second copy of live work - the lease length is what has
   * to be longer than the slowest legitimate run.
   *
   * Each recovery counts against MAX_STALL_RETRIES. Past that the job is failed
   * rather than requeued, because a job that always stalls would otherwise sit
   * at the head of this single-threaded queue and block every job behind it.
   *
   * @return array{requeued: string[], failed: string[]}
   *   The ids given another attempt, and the ids failed for good.
   */
  public function requeueStalled(): array {
    $now = $this->time->getRequestTime();
    $query = $this->database->select(self::TABLE, 'aq')
      ->fields('aq', ['job_id', 'num_retries'])
      ->condition('queue_id', self::QUEUE_ID)
      ->condition('state', Job::STATE_PROCESSING);
    // Expired lease, or no lease at all - see isStalled(). Both mean nothing
    // is working on it, and a lease-less claim is the worse of the two:
    // neither the claim loop nor contrib's cleanup looks at it again.
    $orphaned = $query->orConditionGroup()
      ->condition('expires', 0)
      ->condition('expires', $now, '<');
    $stalled = $query->condition($orphaned)
      ->execute()
      ?->fetchAll(FetchAs::Associative) ?? [];

    $recovered = ['requeued' => [], 'failed' => []];
    foreach ($stalled as $row) {
      $job_id = (string) ($row['job_id'] ?? '');
      $attempts = (int) ($row['num_retries'] ?? 0);
      if ($attempts >= self::MAX_STALL_RETRIES) {
        $this->failStalled($job_id, $attempts + 1);
        $recovered['failed'][] = $job_id;
        continue;
      }
      if ($this->requeue($job_id, $attempts + 1) !== NULL) {
        $recovered['requeued'][] = $job_id;
      }
    }

    return $recovered;
  }

  /**
   * Give up on a job that keeps stalling.
   *
   * Written as a plain failure so it reads like any other in the activity bar,
   * with a message that says what actually went wrong: the work never reported
   * back, rather than the model refusing or the payload being wrong.
   *
   * @param string $job_id
   *   The job id.
   * @param int $attempts
   *   How many attempts were made, for the message.
   */
  private function failStalled(string $job_id, int $attempts): void {
    $this->database->update(self::TABLE)
      ->fields([
        'state' => Job::STATE_FAILURE,
        'expires' => 0,
        'processed' => $this->time->getRequestTime(),
        'message' => sprintf(
          'Timed out after %d attempts: the host stopped responding before the work finished.',
          $attempts
        ),
      ])
      ->condition('queue_id', self::QUEUE_ID)
      ->condition('job_id', $job_id)
      ->execute();
  }

  /**
   * Delete finished jobs, clearing the activity log.
   *
   * Nothing prunes this table on its own, so the console's "Clear completed"
   * needs an actual delete: the activity bar is a view of these rows and has no
   * copy of its own to forget.
   *
   * Two things are protected. Only terminal states can be cleared, so live
   * or waiting work is never deleted out from under the processor. And a
   * successful job whose result is still awaiting a decision is kept:
   * deleting it would strand the thing it produced - a rendered portrait
   * sitting in the media library with nothing left to attach it.
   *
   * @param string[] $states
   *   Terminal states to clear. Empty means every terminal state.
   *
   * @return array{cleared: int, kept: int}
   *   How many jobs were deleted, and how many were kept back for review.
   *
   * @throws \InvalidArgumentException
   *   When a state that is not terminal is asked for.
   */
  public function clearFinished(array $states): array {
    $terminal = [Job::STATE_SUCCESS, Job::STATE_FAILURE];
    $wanted = $states === [] ? $terminal : $states;
    $invalid = array_diff($wanted, $terminal);
    if ($invalid !== []) {
      throw new \InvalidArgumentException(sprintf(
        'Only finished jobs can be cleared; refusing to clear: %s.',
        implode(', ', $invalid)
      ));
    }

    $rows = $this->database->select(self::TABLE, 'aq')
      ->fields('aq', ['job_id', 'payload'])
      ->condition('queue_id', self::QUEUE_ID)
      ->condition('state', $wanted, 'IN')
      ->execute()
      ?->fetchAll(FetchAs::Associative) ?? [];

    // The review marker lives inside the JSON payload, and the column is a
    // blob, so this is decided in PHP rather than in the query.
    $deletable = [];
    $kept = 0;
    foreach ($rows as $row) {
      if ($this->awaitsReview($row)) {
        $kept++;
        continue;
      }
      $deletable[] = (string) ($row['job_id'] ?? '');
    }

    $cleared = 0;
    if ($deletable !== []) {
      $cleared = (int) $this->database->delete(self::TABLE)
        ->condition('queue_id', self::QUEUE_ID)
        ->condition('job_id', $deletable, 'IN')
        ->execute();
    }

    return ['cleared' => $cleared, 'kept' => $kept];
  }

  /**
   * Decide whether a job still owes the operator a decision.
   *
   * @param array<string, mixed> $row
   *   The raw job row.
   *
   * @return bool
   *   TRUE when the job's result is marked pending review.
   */
  private function awaitsReview(array $row): bool {
    $payload = json_decode((string) ($row['payload'] ?? ''), TRUE);
    if (!is_array($payload) || !is_array($payload['result'] ?? NULL)) {
      return FALSE;
    }

    return ($payload['result']['review'] ?? NULL) === JobReview::PENDING;
  }

  /**
   * Merge values into a finished job's stored result.
   *
   * Records what happened to a result after the processor was done with it -
   * whether a render was accepted or dropped - so the activity bar stops
   * offering a decision that has already been made. Only the payload column is
   * touched; the job's own state is the processor's to own.
   *
   * @param string $job_id
   *   The job id.
   * @param array<string, mixed> $changes
   *   Values to merge into the payload's "result" object.
   *
   * @return array<string, mixed>|null
   *   The updated job record, or NULL when no such job exists.
   */
  public function updateResult(string $job_id, array $changes): ?array {
    $row = $this->database->select(self::TABLE, 'aq')
      ->fields('aq', ['payload'])
      ->condition('queue_id', self::QUEUE_ID)
      ->condition('job_id', $job_id)
      ->execute()
      ?->fetchAssoc();
    if (!is_array($row)) {
      return NULL;
    }

    $payload = json_decode((string) ($row['payload'] ?? ''), TRUE);
    $payload = is_array($payload) ? $payload : [];
    $result = $payload['result'] ?? NULL;
    $payload['result'] = array_merge(is_array($result) ? $result : [], $changes);

    $this->database->update(self::TABLE)
      ->fields(['payload' => (string) json_encode($payload)])
      ->condition('queue_id', self::QUEUE_ID)
      ->condition('job_id', $job_id)
      ->execute();

    return $this->load($job_id);
  }

  /**
   * List jobs, most recent first.
   *
   * @param string[] $states
   *   Job states to include. An empty array means every state.
   * @param int $limit
   *   The maximum number of jobs to return.
   *
   * @return array<int, array<string, mixed>>
   *   The normalised job records.
   */
  public function list(array $states, int $limit): array {
    $query = $this->database->select(self::TABLE, 'aq')
      ->fields('aq')
      ->condition('queue_id', self::QUEUE_ID)
      ->orderBy('job_id', 'DESC')
      ->range(0, max(1, $limit));
    if ($states !== []) {
      $query->condition('state', $states, 'IN');
    }

    $rows = $query->execute()?->fetchAll(FetchAs::Associative) ?? [];

    return array_map(fn (array $row): array => $this->describeRow($row), $rows);
  }

  /**
   * Load the queue entity every job is enqueued on.
   *
   * @return \Drupal\advancedqueue\Entity\QueueInterface
   *   The queue.
   *
   * @throws \RuntimeException
   *   When the queue config entity is missing (module config not imported).
   */
  private function queue(): QueueInterface {
    $queue = $this->entityTypeManager
      ->getStorage('advancedqueue_queue')
      ->load(self::QUEUE_ID);
    if (!$queue instanceof QueueInterface) {
      throw new \RuntimeException(sprintf('The "%s" queue does not exist.', self::QUEUE_ID));
    }
    return $queue;
  }

  /**
   * Normalise a freshly enqueued job object into the GraphQL-facing shape.
   *
   * @param \Drupal\advancedqueue\Job $job
   *   The job.
   *
   * @return array<string, mixed>
   *   The normalised job record.
   */
  private function describe(Job $job): array {
    $payload = $job->getPayload();

    return [
      'id' => (string) $job->getId(),
      'type' => $job->getType(),
      'state' => $job->getState(),
      'label' => is_string($payload['label'] ?? NULL) ? $payload['label'] : $job->getType(),
      'message' => $job->getMessage(),
      'result' => $this->encodeResult($payload),
      'subjectId' => $this->subjectId($payload),
      'stalled' => FALSE,
      'created' => (int) $job->getAvailableTime(),
      'processed' => (int) $job->getProcessedTime(),
    ];
  }

  /**
   * Normalise a job table row into the GraphQL-facing shape.
   *
   * @param array<string, mixed> $row
   *   The raw job row.
   *
   * @return array<string, mixed>
   *   The normalised job record.
   */
  private function describeRow(array $row): array {
    $payload = json_decode((string) ($row['payload'] ?? ''), TRUE);
    $payload = is_array($payload) ? $payload : [];

    return [
      'id' => (string) ($row['job_id'] ?? ''),
      'type' => (string) ($row['type'] ?? ''),
      'state' => (string) ($row['state'] ?? ''),
      'label' => is_string($payload['label'] ?? NULL) ? $payload['label'] : (string) ($row['type'] ?? ''),
      'message' => $row['message'] === NULL ? NULL : (string) $row['message'],
      'result' => $this->encodeResult($payload),
      'subjectId' => $this->subjectId($payload),
      'stalled' => $this->isStalled($row),
      'created' => (int) ($row['available'] ?? 0),
      'processed' => (int) ($row['processed'] ?? 0),
    ];
  }

  /**
   * Decide whether a claimed job has been abandoned by its worker.
   *
   * A job in "processing" holds a lease. Past its expiry nothing is working on
   * it any more - the processor that claimed it is gone - so the console can
   * offer a requeue instead of leaving the operator watching a spinner that
   * will never finish.
   *
   * @param array<string, mixed> $row
   *   The raw job row.
   *
   * @return bool
   *   TRUE when the job is claimed but its lease has expired.
   */
  private function isStalled(array $row): bool {
    if ((string) ($row['state'] ?? '') !== Job::STATE_PROCESSING) {
      return FALSE;
    }
    $expires = (int) ($row['expires'] ?? 0);

    // No lease at all counts as stalled. The backend sets state and lease in
    // a single claim, and only ever claims rows with expires = 0, so a claimed
    // row without a lease cannot arise from normal processing - and nothing
    // will ever pick it up again: the claim loop only looks at queued jobs,
    // and contrib's own cleanup only resets leases that exist. Left out, such
    // a row spins in the activity bar forever.
    return $expires === 0 || $expires < $this->time->getRequestTime();
  }

  /**
   * Read the id of the content a job is about, from its request payload.
   *
   * Taken from the payload rather than the result so it is available from the
   * moment the job is queued. That is what lets the console's activity bar link
   * a still-running job to the screen its output will land on, instead of only
   * once it has finished.
   *
   * @param array<string, mixed> $payload
   *   The job payload.
   *
   * @return string|null
   *   The character UUID the job concerns, or NULL for job types that are not
   *   about one character.
   */
  private function subjectId(array $payload): ?string {
    $value = $payload['characterId'] ?? NULL;

    return is_string($value) && trim($value) !== '' ? trim($value) : NULL;
  }

  /**
   * Encode a finished job's result for transport.
   *
   * Job types write what the console needs on completion (a new image URL, a
   * created node id) back into the payload under "result"; the processor
   * persists the mutated payload, so it survives to the next poll.
   *
   * @param array<string, mixed> $payload
   *   The job payload.
   *
   * @return string|null
   *   The JSON-encoded result, or NULL when the job has produced none.
   */
  private function encodeResult(array $payload): ?string {
    $result = $payload['result'] ?? NULL;
    if (!is_array($result) || $result === []) {
      return NULL;
    }
    $encoded = json_encode($result);

    return $encoded === FALSE ? NULL : $encoded;
  }

}
