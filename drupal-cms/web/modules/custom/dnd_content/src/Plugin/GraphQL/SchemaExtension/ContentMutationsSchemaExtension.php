<?php

declare(strict_types=1);

namespace Drupal\dnd_content\Plugin\GraphQL\SchemaExtension;

use Drupal\Core\StringTranslation\TranslatableMarkup;
use Drupal\graphql\Attribute\SchemaExtension;
use Drupal\graphql\GraphQL\ResolverBuilder;
use Drupal\graphql\GraphQL\ResolverRegistryInterface;
use Drupal\graphql\Plugin\GraphQL\SchemaExtension\SdlSchemaExtensionPluginBase;
use GraphQL\Language\Source;

/**
 * Extends the GraphQL Compose schema with D&D content creation mutations.
 */
#[SchemaExtension(
  id: "dnd_content_mutations",
  name: new TranslatableMarkup("D&D Content Mutations"),
  description: new TranslatableMarkup("Mutations for creating D&D campaign content from the Gatsby frontend."),
  schema: "graphql_compose",
  priority: 0,
)]
class ContentMutationsSchemaExtension extends SdlSchemaExtensionPluginBase {

  /**
   * {@inheritdoc}
   *
   * No base SDL file — this extension only adds fields to existing types.
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
      'createCampaign',
      $builder->produce('create_campaign')
        ->map('name', $builder->fromArgument('name'))
        ->map('status', $builder->fromArgument('status')),
    );
  }

}
