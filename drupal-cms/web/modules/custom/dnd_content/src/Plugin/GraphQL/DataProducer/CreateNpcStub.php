<?php

declare(strict_types=1);

namespace Drupal\dnd_content\Plugin\GraphQL\DataProducer;

use Drupal\Core\Entity\EntityTypeManagerInterface;
use Drupal\Core\Plugin\ContainerFactoryPluginInterface;
use Drupal\Core\Plugin\Context\ContextDefinition;
use Drupal\Core\Session\AccountInterface;
use Drupal\Core\StringTranslation\TranslatableMarkup;
use Drupal\graphql\Attribute\DataProducer;
use Drupal\graphql\GraphQL\Execution\FieldContext;
use Drupal\graphql\Plugin\GraphQL\DataProducer\DataProducerPluginBase;
use Drupal\node\NodeInterface;
use Drupal\taxonomy\TermInterface;
use GraphQL\Error\UserError;
use Symfony\Component\DependencyInjection\ContainerInterface;

/**
 * Creates a minimal NPC character node.
 *
 * The counterpart to create_character, which derives a full player sheet from
 * the sidecar and hardcodes ``field_character_type = TRUE``. An NPC read out
 * of a campaign's session recaps has a name and a line about who they are, and
 * nothing else worth inventing: the stories rarely give a stat block, and
 * fabricating one would put invented numbers on record as though they were
 * canon. The node is created scoped to its campaign so the NPC roster can tell
 * one campaign's cast from another's.
 *
 * Everything else is filled in later through the ordinary character editor.
 */
#[DataProducer(
  id: "create_npc_stub",
  name: new TranslatableMarkup("Create NPC Stub"),
  description: new TranslatableMarkup("Creates a minimal NPC character node for a campaign."),
  produces: new ContextDefinition(
    data_type: "any",
    label: new TranslatableMarkup("Created NPC node"),
  ),
  consumes: [
    "campaign_id" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("Campaign term UUID"),
      required: FALSE,
    ),
    "name" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("NPC name"),
    ),
    "role" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("One line on who they are"),
      required: FALSE,
    ),
    "note" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("Where the NPC came from"),
      required: FALSE,
    ),
  ],
)]
final class CreateNpcStub extends DataProducerPluginBase implements ContainerFactoryPluginInterface {

  /**
   * The entity type manager.
   *
   * @var \Drupal\Core\Entity\EntityTypeManagerInterface
   */
  protected EntityTypeManagerInterface $entityTypeManager;

  /**
   * The current user.
   *
   * @var \Drupal\Core\Session\AccountInterface
   */
  protected AccountInterface $currentUser;

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
  ): static {
    $instance = new static($configuration, $plugin_id, $plugin_definition);
    $instance->entityTypeManager = $container->get('entity_type.manager');
    $instance->currentUser = $container->get('current_user');

    return $instance;
  }

  /**
   * Create the NPC node.
   *
   * @param string|null $campaign_id
   *   UUID of the campaign term to scope the NPC to, if any.
   * @param string $name
   *   The NPC's name.
   * @param string|null $role
   *   One line on who they are.
   * @param string|null $note
   *   Provenance, e.g. which sessions named them.
   * @param \Drupal\graphql\GraphQL\Execution\FieldContext $context
   *   The GraphQL field execution context.
   *
   * @return \Drupal\node\NodeInterface
   *   The newly created NPC node.
   *
   * @throws \GraphQL\Error\UserError
   *   When the name is blank, permission is denied, or the save fails.
   */
  public function resolve(
    ?string $campaign_id,
    string $name,
    ?string $role,
    ?string $note,
    FieldContext $context,
  ): NodeInterface {
    $title = trim($name);
    if ($title === '') {
      throw new UserError('An NPC name is required.');
    }

    if (!$this->currentUser->hasPermission('create character content')) {
      $context->addCacheableDependency($this->currentUser);
      throw new UserError('You do not have permission to create characters.');
    }

    $existing = $this->findExisting($title, $campaign_id);
    if ($existing !== NULL) {
      return $existing;
    }

    $values = [
      'type' => 'character',
      'title' => $title,
      'status' => 1,
      // A stub is canon for the campaign, not a clone of anything.
      'field_source_character' => TRUE,
      'field_character_type' => FALSE,
    ];

    $role = $role === NULL ? '' : trim($role);
    if ($role !== '') {
      $values['field_role'] = $role;
    }
    $note = $note === NULL ? '' : trim($note);
    if ($note !== '') {
      $values['field_notes'] = ['value' => $note, 'format' => 'plain_text'];
    }

    $campaign = $this->loadCampaign($campaign_id);
    if ($campaign !== NULL) {
      $values['field_campaign'] = ['target_id' => $campaign->id()];
    }

    $node = $this->entityTypeManager->getStorage('node')->create($values);
    $node->save();

    return $node;
  }

  /**
   * Find an NPC that already carries this name in this campaign.
   *
   * Creation is driven by a model reading recaps, so the same name can be
   * offered twice across reruns. Returning the existing node keeps a rerun
   * from filling the roster with duplicates.
   *
   * @param string $title
   *   The NPC name.
   * @param string|null $campaign_id
   *   UUID of the campaign term, if any.
   *
   * @return \Drupal\node\NodeInterface|null
   *   The existing NPC, or NULL when there is none.
   */
  private function findExisting(string $title, ?string $campaign_id): ?NodeInterface {
    $properties = [
      'type' => 'character',
      'title' => $title,
      'field_character_type' => 0,
    ];
    $campaign = $this->loadCampaign($campaign_id);
    if ($campaign !== NULL) {
      $properties['field_campaign'] = $campaign->id();
    }
    $nodes = $this->entityTypeManager->getStorage('node')->loadByProperties($properties);
    $node = reset($nodes);

    return $node instanceof NodeInterface ? $node : NULL;
  }

  /**
   * Load a campaign term by UUID.
   *
   * @param string|null $campaign_id
   *   The campaign term UUID, if any.
   *
   * @return \Drupal\taxonomy\TermInterface|null
   *   The term, or NULL when none was given or it does not exist.
   */
  private function loadCampaign(?string $campaign_id): ?TermInterface {
    $uuid = $campaign_id === NULL ? '' : trim($campaign_id);
    if ($uuid === '') {
      return NULL;
    }
    $terms = $this->entityTypeManager
      ->getStorage('taxonomy_term')
      ->loadByProperties(['uuid' => $uuid, 'vid' => 'campaign']);
    $term = reset($terms);

    return $term instanceof TermInterface ? $term : NULL;
  }

}
