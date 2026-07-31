<?php

declare(strict_types=1);

namespace Drupal\dnd_jobs\Drush\Commands;

use Drupal\dnd_jobs\Service\JobQueue;
use Drush\Attributes\Command;
use Drush\Attributes\Usage;
use Drush\Commands\DrushCommands;
use Symfony\Component\DependencyInjection\ContainerInterface;

/**
 * Drush access to the AI queue's stall recovery.
 *
 * The same sweep hook_cron() runs, callable directly. That matters because cron
 * is not guaranteed to run here: this site is headless, has no automated_cron,
 * and nothing schedules drush cron - so relying on cron alone would leave a
 * job orphaned by a dead worker stuck until somebody noticed it. start.sh
 * calls this from the queue processor's restart loop, which fires at exactly
 * the moment a worker has died.
 */
final class JobRecoveryCommands extends DrushCommands {

  /**
   * Constructs a JobRecoveryCommands object.
   *
   * @param \Drupal\dnd_jobs\Service\JobQueue $jobQueue
   *   The AI job queue.
   */
  public function __construct(private readonly JobQueue $jobQueue) {
    parent::__construct();
  }

  /**
   * Creates the command from the container.
   *
   * @param \Symfony\Component\DependencyInjection\ContainerInterface $container
   *   The service container.
   *
   * @return self
   *   The command instance.
   */
  public static function create(ContainerInterface $container): self {
    return new self($container->get('dnd_jobs.job_queue'));
  }

  /**
   * Requeues AI jobs whose worker went away, failing ones that keep stalling.
   *
   * @return int
   *   The command exit code.
   */
  #[Command(name: 'dnd-jobs:recover', aliases: ['dndjr'])]
  #[Usage(
    name: 'drush dnd-jobs:recover',
    description: 'Recover AI jobs orphaned by a dead queue worker.'
  )]
  public function recover(): int {
    $recovered = $this->jobQueue->requeueStalled();

    if ($recovered['requeued'] === [] && $recovered['failed'] === []) {
      $this->logger()->success('No stalled jobs to recover.');

      return self::EXIT_SUCCESS;
    }

    if ($recovered['requeued'] !== []) {
      $this->logger()->warning(dt('Requeued: @ids', [
        '@ids' => implode(', ', $recovered['requeued']),
      ]));
    }
    if ($recovered['failed'] !== []) {
      $this->logger()->error(dt('Failed after @max stalls: @ids', [
        '@max' => JobQueue::MAX_STALL_RETRIES,
        '@ids' => implode(', ', $recovered['failed']),
      ]));
    }

    return self::EXIT_SUCCESS;
  }

}
