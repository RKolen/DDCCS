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
 * Updates a character node's voice settings.
 *
 * Sets the voice reference (field_voice_id_ref, resolved from the voice_ids
 * vocabulary by name), pitch, and speed. Only the arguments that are supplied
 * are changed. Returns the updated character node.
 */
#[DataProducer(
  id: "update_character",
  name: new TranslatableMarkup("Update Character"),
  description: new TranslatableMarkup("Updates a character's voice id, pitch, and speed."),
  produces: new ContextDefinition(
    data_type: "any",
    label: new TranslatableMarkup("Updated character node"),
  ),
  consumes: [
    "id" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("Character node UUID"),
    ),
    "voice_id" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("Voice id (voice_ids term name)"),
      required: FALSE,
    ),
    "voice_pitch" => new ContextDefinition(
      data_type: "float",
      label: new TranslatableMarkup("Voice pitch"),
      required: FALSE,
    ),
    "voice_speed" => new ContextDefinition(
      data_type: "float",
      label: new TranslatableMarkup("Voice speed"),
      required: FALSE,
    ),
  ],
)]
final class UpdateCharacter extends DataProducerPluginBase implements ContainerFactoryPluginInterface {

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
   * Update the character's voice settings.
   *
   * @param string $id
   *   The character node UUID.
   * @param string|null $voice_id
   *   The voice id (a voice_ids term name), or NULL to leave unchanged.
   * @param float|null $voice_pitch
   *   The voice pitch, or NULL to leave unchanged.
   * @param float|null $voice_speed
   *   The voice speed, or NULL to leave unchanged.
   * @param \Drupal\graphql\GraphQL\Execution\FieldContext $context
   *   The GraphQL field execution context.
   *
   * @return \Drupal\node\NodeInterface
   *   The updated character node.
   *
   * @throws \GraphQL\Error\UserError
   *   When the character is not found or permission is denied.
   */
  public function resolve(
    string $id,
    ?string $voice_id,
    ?float $voice_pitch,
    ?float $voice_speed,
    FieldContext $context,
  ): NodeInterface {
    $nodes = $this->entityTypeManager
      ->getStorage('node')
      ->loadByProperties(['uuid' => $id, 'type' => 'character']);

    $node = reset($nodes);
    if (!$node instanceof NodeInterface) {
      throw new UserError('Character not found.');
    }

    if (!$node->access('update', $this->currentUser)) {
      $context->addCacheableDependency($this->currentUser);
      throw new UserError('You do not have permission to update this character.');
    }

    if ($voice_id !== NULL && trim($voice_id) !== '') {
      $terms = $this->entityTypeManager
        ->getStorage('taxonomy_term')
        ->loadByProperties(['vid' => 'voice_ids', 'name' => trim($voice_id)]);
      $term = reset($terms);
      if ($term instanceof TermInterface) {
        $node->set('field_voice_id_ref', ['target_id' => $term->id()]);
      }
    }
    if ($voice_pitch !== NULL) {
      $node->set('field_voice_pitch', $voice_pitch);
    }
    if ($voice_speed !== NULL) {
      $node->set('field_voice_speed', $voice_speed);
    }

    $violations = $node->validate();
    if ($violations->count() > 0) {
      throw new UserError((string) $violations->get(0)->getMessage());
    }
    $node->save();

    return $node;
  }

}
