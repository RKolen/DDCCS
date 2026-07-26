<?php

declare(strict_types=1);

namespace Drupal\dnd_jobs\Plugin\GraphQL\SchemaExtension;

use Drupal\Core\StringTranslation\TranslatableMarkup;
use Drupal\graphql\Attribute\SchemaExtension;
use Drupal\graphql\GraphQL\ResolverBuilder;
use Drupal\graphql\GraphQL\ResolverRegistryInterface;
use Drupal\graphql\Plugin\GraphQL\SchemaExtension\SdlSchemaExtensionPluginBase;
use GraphQL\Language\Source;

/**
 * Extends the GraphQL Compose schema with the AI job queue surface.
 *
 * One mutation to enqueue work and two queries to follow it: the console gets a
 * job id back instantly and polls, instead of holding a request open for the
 * minutes a CPU model run takes.
 */
#[SchemaExtension(
  id: "dnd_jobs",
  name: new TranslatableMarkup("D&D AI Jobs"),
  description: new TranslatableMarkup("Enqueue and poll the queued heavy AI jobs."),
  schema: "graphql_compose",
  priority: 0,
)]
class JobsSchemaExtension extends SdlSchemaExtensionPluginBase {

  /**
   * {@inheritdoc}
   *
   * No base SDL file - this extension only adds to the composed schema.
   */
  public function getBaseDefinition(): ?Source {
    return NULL;
  }

  /**
   * {@inheritdoc}
   */
  public function registerResolvers(ResolverRegistryInterface $registry): void {
    $builder = new ResolverBuilder();

    $registry->addFieldResolver(
      'Mutation',
      'enqueueAiJob',
      $builder->produce('enqueue_ai_job')
        ->map('type', $builder->fromArgument('type'))
        ->map('payload', $builder->fromArgument('payload'))
        ->map('label', $builder->fromArgument('label')),
    );

    $registry->addFieldResolver(
      'Query',
      'aiJob',
      $builder->produce('ai_job')
        ->map('id', $builder->fromArgument('id')),
    );

    $registry->addFieldResolver(
      'Query',
      'aiJobs',
      $builder->produce('ai_jobs')
        ->map('states', $builder->fromArgument('states'))
        ->map('limit', $builder->fromArgument('limit')),
    );

    // Job records are plain arrays from the queue service, so every field is a
    // key lookup on the parent.
    foreach (['id', 'type', 'state', 'label', 'message', 'result', 'created', 'processed'] as $field) {
      $registry->addFieldResolver(
        'AiJob',
        $field,
        $builder->produce('ai_job_field')
          ->map('job', $builder->fromParent())
          ->map('field', $builder->fromValue($field)),
      );
    }
  }

}
