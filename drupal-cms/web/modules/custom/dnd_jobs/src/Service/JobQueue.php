<?php

declare(strict_types=1);

namespace Drupal\dnd_jobs\Service;

use Drupal\advancedqueue\Entity\QueueInterface;
use Drupal\advancedqueue\Job;
use Drupal\Core\Database\Connection;
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
   * Constructs a JobQueue.
   *
   * @param \Drupal\Core\Entity\EntityTypeManagerInterface $entityTypeManager
   *   The entity type manager.
   * @param \Drupal\Core\Database\Connection $database
   *   The database connection.
   */
  public function __construct(
    private readonly EntityTypeManagerInterface $entityTypeManager,
    private readonly Connection $database,
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

    $rows = $query->execute()?->fetchAll(\PDO::FETCH_ASSOC) ?? [];

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
      'created' => (int) ($row['available'] ?? 0),
      'processed' => (int) ($row['processed'] ?? 0),
    ];
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
