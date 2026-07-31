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
use Symfony\Component\DependencyInjection\ContainerInterface;

/**
 * Delete the cached wiki page for a URL hash.
 *
 * Deleting an entry that is not there is a success, not an error: the caller
 * wanted the cache to not hold that URL, and it does not.
 */
#[DataProducer(
  id: "delete_wiki_cache_entry",
  name: new TranslatableMarkup("Delete Wiki Cache Entry"),
  description: new TranslatableMarkup("Delete a cached wiki page by URL hash."),
  produces: new ContextDefinition(
    data_type: "boolean",
    label: new TranslatableMarkup("Whether the cache no longer holds the entry"),
  ),
  consumes: [
    "url_hash" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("MD5 hash of the page URL"),
    ),
  ],
)]
final class DeleteWikiCacheEntry extends DataProducerPluginBase implements ContainerFactoryPluginInterface {

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
   * Delete the cache entry.
   *
   * @param string $url_hash
   *   MD5 hash of the page URL, used as the node title.
   * @param \Drupal\graphql\GraphQL\Execution\FieldContext $context
   *   The GraphQL field execution context.
   *
   * @return bool
   *   TRUE when the cache no longer holds the entry, FALSE when access is
   *   denied.
   */
  public function resolve(string $url_hash, FieldContext $context): bool {
    $storage = $this->entityTypeManager->getStorage('node');
    $nodes = $storage->loadByProperties([
      'type' => 'wiki_cache',
      'title' => $url_hash,
    ]);
    $node = reset($nodes);
    if (!$node instanceof NodeInterface) {
      return TRUE;
    }
    if (!$node->access('delete', $this->currentUser)) {
      $context->addCacheableDependency($this->currentUser);
      return FALSE;
    }
    $node->delete();

    return TRUE;
  }

}
