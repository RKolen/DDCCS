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
      'upsertCharacterAnalysis',
      $builder->produce('upsert_character_analysis')
        ->map('campaign_id', $builder->fromArgument('campaignId'))
        ->map('character_id', $builder->fromArgument('characterId'))
        ->map('story_number', $builder->fromArgument('storyNumber'))
        ->map('story_text', $builder->fromArgument('storyText'))
        ->map('datapoint', $builder->fromArgument('datapoint'))
        ->map('summary', $builder->fromArgument('summary')),
    );

    $registry->addFieldResolver(
      'Mutation',
      'deleteCharacterAnalysis',
      $builder->produce('delete_character_analysis')
        ->map('campaign_id', $builder->fromArgument('campaignId'))
        ->map('character_id', $builder->fromArgument('characterId')),
    );

    $registry->addFieldResolver(
      'Mutation',
      'createCharacter',
      $builder->produce('create_character')
        ->map('payload', $builder->fromArgument('payload')),
    );

    $registry->addFieldResolver(
      'Mutation',
      'saveCharacterArc',
      $builder->produce('save_character_arc')
        ->map('id', $builder->fromArgument('id'))
        ->map('payload', $builder->fromArgument('payload')),
    );

    $registry->addFieldResolver(
      'Mutation',
      'setCharacterPortrait',
      $builder->produce('set_character_portrait')
        ->map('id', $builder->fromArgument('id'))
        ->map('image_base64', $builder->fromArgument('imageBase64'))
        ->map('alt', $builder->fromArgument('alt')),
    );

    $registry->addFieldResolver(
      'Mutation',
      'setCharacterImage',
      $builder->produce('set_character_image')
        ->map('id', $builder->fromArgument('id'))
        ->map('media_id', $builder->fromArgument('mediaId')),
    );

    $registry->addFieldResolver(
      'Mutation',
      'updateCharacter',
      $builder->produce('update_character')
        ->map('id', $builder->fromArgument('id'))
        ->map('voice_id', $builder->fromArgument('voiceId'))
        ->map('voice_pitch', $builder->fromArgument('voicePitch'))
        ->map('voice_speed', $builder->fromArgument('voiceSpeed')),
    );

    $registry->addFieldResolver(
      'Mutation',
      'createCampaign',
      $builder->produce('create_campaign')
        ->map('name', $builder->fromArgument('name'))
        ->map('status', $builder->fromArgument('status')),
    );

    $registry->addFieldResolver(
      'Mutation',
      'setSessionSummary',
      $builder->produce('set_campaign_summary')
        ->map('campaign_id', $builder->fromArgument('campaignId'))
        ->map('story_number', $builder->fromArgument('storyNumber'))
        ->map('summary', $builder->fromArgument('summary'))
        ->map('overview', $builder->fromArgument('overview')),
    );

    $registry->addFieldResolver(
      'Mutation',
      'addCharacterToCampaign',
      $builder->produce('add_character_to_campaign')
        ->map('campaign_id', $builder->fromArgument('campaignId'))
        ->map('character_id', $builder->fromArgument('characterId')),
    );

    $registry->addFieldResolver(
      'Mutation',
      'createStory',
      $builder->produce('create_story')
        ->map('campaign_id', $builder->fromArgument('campaignId'))
        ->map('title', $builder->fromArgument('title'))
        ->map('body', $builder->fromArgument('body'))
        ->map('story_number', $builder->fromArgument('storyNumber'))
        ->map('session_date', $builder->fromArgument('sessionDate')),
    );
  }

}
