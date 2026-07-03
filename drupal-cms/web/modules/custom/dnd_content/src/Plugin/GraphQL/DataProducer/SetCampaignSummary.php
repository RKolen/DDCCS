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
use Drupal\paragraphs\Entity\Paragraph;
use Drupal\paragraphs\ParagraphInterface;
use Drupal\taxonomy\TermInterface;
use GraphQL\Error\UserError;
use Symfony\Component\DependencyInjection\ContainerInterface;

/**
 * Stores a session summary and the synthesized overview on a campaign term.
 *
 * Upserts the session_summary paragraph identified by its story number in
 * field_session_summaries, and replaces field_campaign_overview with a wysiwyg
 * paragraph holding the synthesized "story so far" (when supplied). Returns the
 * updated campaign term.
 */
#[DataProducer(
  id: "set_campaign_summary",
  name: new TranslatableMarkup("Set Campaign Summary"),
  description: new TranslatableMarkup("Upserts a session summary + campaign overview on a campaign term."),
  produces: new ContextDefinition(
    data_type: "any",
    label: new TranslatableMarkup("Updated campaign term"),
  ),
  consumes: [
    "campaign_id" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("Campaign term UUID"),
    ),
    "story_number" => new ContextDefinition(
      data_type: "integer",
      label: new TranslatableMarkup("Story number"),
    ),
    "summary" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("Session summary"),
    ),
    "overview" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("Synthesized campaign overview"),
      required: FALSE,
    ),
  ],
)]
final class SetCampaignSummary extends DataProducerPluginBase implements ContainerFactoryPluginInterface {

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
   * Upsert the session summary and overview on the campaign.
   *
   * @param string $campaign_id
   *   The campaign term UUID.
   * @param int $story_number
   *   The story number the summary belongs to.
   * @param string $summary
   *   The session summary text.
   * @param string|null $overview
   *   The synthesized campaign overview, or NULL to leave it unchanged.
   * @param \Drupal\graphql\GraphQL\Execution\FieldContext $context
   *   The GraphQL field execution context.
   *
   * @return \Drupal\taxonomy\TermInterface
   *   The updated campaign term.
   *
   * @throws \GraphQL\Error\UserError
   *   When the campaign is not found or permission is denied.
   */
  public function resolve(
    string $campaign_id,
    int $story_number,
    string $summary,
    ?string $overview,
    FieldContext $context,
  ): TermInterface {
    $terms = $this->entityTypeManager
      ->getStorage('taxonomy_term')
      ->loadByProperties(['uuid' => $campaign_id, 'vid' => 'campaign']);
    $term = reset($terms);
    if (!$term instanceof TermInterface) {
      throw new UserError('Campaign not found.');
    }
    if (!$term->access('update', $this->currentUser)) {
      $context->addCacheableDependency($this->currentUser);
      throw new UserError('You do not have permission to update this campaign.');
    }

    $this->upsertSessionSummary($term, $story_number, $summary);
    if ($overview !== NULL && trim($overview) !== '') {
      $term->set('field_campaign_overview', $this->wysiwyg($overview));
    }
    $term->save();

    return $term;
  }

  /**
   * Upsert the session_summary paragraph for a story number.
   *
   * @param \Drupal\taxonomy\TermInterface $term
   *   The campaign term.
   * @param int $story_number
   *   The story number.
   * @param string $summary
   *   The summary text.
   */
  private function upsertSessionSummary(TermInterface $term, int $story_number, string $summary): void {
    $list = $term->get('field_session_summaries');
    if ($list instanceof EntityReferenceFieldItemListInterface) {
      foreach ($list->referencedEntities() as $paragraph) {
        if ($paragraph instanceof ParagraphInterface
          && (int) $paragraph->get('field_story_number')->value === $story_number) {
          $paragraph->set('field_text', ['value' => $summary, 'format' => 'plain_text']);
          $paragraph->save();
          return;
        }
      }
    }
    $paragraph = Paragraph::create([
      'type' => 'session_summary',
      'field_story_number' => $story_number,
      'field_text' => ['value' => $summary, 'format' => 'plain_text'],
    ]);
    $paragraph->save();
    $term->get('field_session_summaries')->appendItem([
      'target_id' => (int) $paragraph->id(),
      'target_revision_id' => (int) $paragraph->getRevisionId(),
    ]);
  }

  /**
   * Build a wysiwyg paragraph reference value for the given text.
   *
   * @param string $text
   *   The paragraph text.
   *
   * @return array{target_id: int, target_revision_id: int}
   *   The entity-reference-revisions value.
   */
  private function wysiwyg(string $text): array {
    $paragraph = Paragraph::create([
      'type' => 'wysiwyg',
      'field_text' => ['value' => $text, 'format' => 'plain_text'],
    ]);
    $paragraph->save();
    return [
      'target_id' => (int) $paragraph->id(),
      'target_revision_id' => (int) $paragraph->getRevisionId(),
    ];
  }

}
