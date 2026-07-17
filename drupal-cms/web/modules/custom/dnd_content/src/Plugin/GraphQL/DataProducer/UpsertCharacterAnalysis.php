<?php

declare(strict_types=1);

namespace Drupal\dnd_content\Plugin\GraphQL\DataProducer;

use Drupal\Core\Entity\EntityTypeManagerInterface;
use Drupal\Core\Field\EntityReferenceFieldItemListInterface;
use Drupal\Core\Plugin\ContainerFactoryPluginInterface;
use Drupal\Core\Plugin\Context\ContextDefinition;
use Drupal\Core\Session\AccountInterface;
use Drupal\Core\StringTranslation\TranslatableMarkup;
use Drupal\graphql\Attribute\DataProducer;
use Drupal\graphql\GraphQL\Execution\FieldContext;
use Drupal\graphql\Plugin\GraphQL\DataProducer\DataProducerPluginBase;
use Drupal\node\NodeInterface;
use Drupal\paragraphs\Entity\Paragraph;
use Drupal\paragraphs\ParagraphInterface;
use Drupal\taxonomy\TermInterface;
use GraphQL\Error\UserError;
use Symfony\Component\DependencyInjection\ContainerInterface;

/**
 * Find-or-create a character_analysis node and upsert a story / summary.
 *
 * Keyed by (campaign, character): finds the existing analysis node or creates
 * one. When story_number + story_text are given, upserts that story's analysis
 * paragraph (session_summary: field_story_number + field_text). When summary is
 * given, replaces field_analysis_summary. Persisting each story as it completes
 * makes a long run crash-safe. Returns the analysis node.
 */
#[DataProducer(
  id: "upsert_character_analysis",
  name: new TranslatableMarkup("Upsert Character Analysis"),
  description: new TranslatableMarkup("Store a per-story analysis or summary on a character_analysis node."),
  produces: new ContextDefinition(
    data_type: "any",
    label: new TranslatableMarkup("Character analysis node"),
  ),
  consumes: [
    "campaign_id" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("Campaign term UUID"),
    ),
    "character_id" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("Character node UUID"),
    ),
    "story_number" => new ContextDefinition(
      data_type: "integer",
      label: new TranslatableMarkup("Story number"),
      required: FALSE,
    ),
    "story_text" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("Story analysis text"),
      required: FALSE,
    ),
    "datapoint" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("Story data point JSON"),
      required: FALSE,
    ),
    "summary" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("Synthesized summary"),
      required: FALSE,
    ),
  ],
)]
final class UpsertCharacterAnalysis extends DataProducerPluginBase implements ContainerFactoryPluginInterface {

  /**
   * The current user.
   *
   * @var \Drupal\Core\Session\AccountInterface
   */
  protected AccountInterface $currentUser;

  /**
   * The entity type manager.
   *
   * @var \Drupal\Core\Entity\EntityTypeManagerInterface
   */
  protected EntityTypeManagerInterface $entityTypeManager;

  /**
   * {@inheritdoc}
   *
   * @param \Symfony\Component\DependencyInjection\ContainerInterface $container
   *   The service container.
   * @param array<string, mixed> $configuration
   *   Plugin configuration.
   * @param string $plugin_id
   *   The plugin ID.
   * @param mixed $plugin_definition
   *   The plugin definition.
   */
  public static function create(
    ContainerInterface $container,
    array $configuration,
    $plugin_id,
    $plugin_definition,
  ): self {
    $instance = new self($configuration, $plugin_id, $plugin_definition);
    $instance->currentUser = $container->get('current_user');
    $instance->entityTypeManager = $container->get('entity_type.manager');
    return $instance;
  }

  /**
   * Upsert a story analysis or summary onto the character's analysis node.
   *
   * @param string $campaign_id
   *   The campaign term UUID.
   * @param string $character_id
   *   The character node UUID.
   * @param int|null $story_number
   *   The story number (with story_text) to upsert.
   * @param string|null $story_text
   *   The story's analysis text.
   * @param string|null $datapoint
   *   The story's structured data point as a JSON string.
   * @param string|null $summary
   *   The synthesized summary to store.
   * @param \Drupal\graphql\GraphQL\Execution\FieldContext $context
   *   The GraphQL field execution context.
   *
   * @return \Drupal\node\NodeInterface
   *   The character_analysis node.
   *
   * @throws \GraphQL\Error\UserError
   *   When the character is missing or access is denied.
   */
  public function resolve(
    string $campaign_id,
    string $character_id,
    ?int $story_number,
    ?string $story_text,
    ?string $datapoint,
    ?string $summary,
    FieldContext $context,
  ): NodeInterface {
    $node_storage = $this->entityTypeManager->getStorage('node');
    $term_storage = $this->entityTypeManager->getStorage('taxonomy_term');

    $characters = $node_storage->loadByProperties(['uuid' => $character_id, 'type' => 'character']);
    $character = reset($characters);
    if (!$character instanceof NodeInterface) {
      throw new UserError('Character not found.');
    }
    // The character is the stable key; the campaign is optional metadata (a
    // character may have no campaign of its own). An unresolvable campaign
    // simply means no campaign reference is stored.
    $campaigns = $term_storage->loadByProperties(['uuid' => $campaign_id, 'vid' => 'campaign']);
    $campaign = reset($campaigns);
    $campaign_tid = $campaign instanceof TermInterface ? $campaign->id() : NULL;
    $title = $campaign instanceof TermInterface
      ? $character->label() . ' · ' . $campaign->label()
      : (string) $character->label();
    $analysis = $this->findOrCreate($character->id(), $campaign_tid, $title);
    if (!$analysis->access('update', $this->currentUser)) {
      $context->addCacheableDependency($this->currentUser);
      throw new UserError('You do not have permission to update this analysis.');
    }

    if ($story_number !== NULL && $story_text !== NULL) {
      $this->upsertStory($analysis, $story_number, $story_text, $datapoint);
    }
    if ($summary !== NULL) {
      $analysis->set('field_analysis_summary', ['value' => $summary, 'format' => 'plain_text']);
    }
    $analysis->save();

    return $analysis;
  }

  /**
   * Load the analysis node for a character, creating it if absent.
   *
   * The character is the key: one analysis record per character. The campaign
   * (when known) is stored as metadata and kept current, and the title is
   * refreshed so records made before a campaign was known are corrected.
   *
   * @param int|string $character_nid
   *   The character node id.
   * @param int|string|null $campaign_tid
   *   The campaign term id, or NULL when no campaign is known.
   * @param string $title
   *   The title (character, plus campaign when known).
   *
   * @return \Drupal\node\NodeInterface
   *   The (possibly new, unsaved-until-caller) character_analysis node.
   */
  private function findOrCreate($character_nid, $campaign_tid, string $title): NodeInterface {
    $storage = $this->entityTypeManager->getStorage('node');
    $existing = $storage->loadByProperties([
      'type' => 'character_analysis',
      'field_character' => $character_nid,
    ]);
    $node = reset($existing);
    if ($node instanceof NodeInterface) {
      $node->set('title', $title);
      if ($campaign_tid !== NULL) {
        $node->set('field_campaign', ['target_id' => $campaign_tid]);
      }
      return $node;
    }
    $values = [
      'type' => 'character_analysis',
      'title' => $title,
      'field_character' => ['target_id' => $character_nid],
    ];
    if ($campaign_tid !== NULL) {
      $values['field_campaign'] = ['target_id' => $campaign_tid];
    }
    /** @var \Drupal\node\NodeInterface $node */
    $node = $storage->create($values);
    return $node;
  }

  /**
   * Upsert a session_summary paragraph for a story number.
   *
   * @param \Drupal\node\NodeInterface $analysis
   *   The analysis node.
   * @param int $story_number
   *   The story number.
   * @param string $text
   *   The story's analysis text.
   * @param string|null $datapoint
   *   The story's structured data point JSON, stored for re-aggregation.
   */
  private function upsertStory(
    NodeInterface $analysis,
    int $story_number,
    string $text,
    ?string $datapoint,
  ): void {
    $list = $analysis->get('field_story_analyses');
    if ($list instanceof EntityReferenceFieldItemListInterface) {
      foreach ($list->referencedEntities() as $paragraph) {
        if ($paragraph instanceof ParagraphInterface
          && (int) $paragraph->get('field_story_number')->value === $story_number) {
          $paragraph->set('field_text', ['value' => $text, 'format' => 'plain_text']);
          if ($datapoint !== NULL) {
            $paragraph->set('field_datapoint', $datapoint);
          }
          $paragraph->save();
          return;
        }
      }
    }
    $values = [
      'type' => 'session_summary',
      'field_story_number' => $story_number,
      'field_text' => ['value' => $text, 'format' => 'plain_text'],
    ];
    if ($datapoint !== NULL) {
      $values['field_datapoint'] = $datapoint;
    }
    $paragraph = Paragraph::create($values);
    $paragraph->save();
    $analysis->get('field_story_analyses')->appendItem([
      'target_id' => (int) $paragraph->id(),
      'target_revision_id' => (int) $paragraph->getRevisionId(),
    ]);
  }

}
