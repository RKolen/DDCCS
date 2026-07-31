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
 * Look up a cached wiki page by the MD5 hash of its URL.
 *
 * Returns a flat array rather than the node so the WikiCacheEntry type stays
 * decoupled from the storage shape. A missing entry is not an error: callers
 * treat NULL as a cache miss and re-fetch the page.
 */
#[DataProducer(
  id: "wiki_cache_lookup",
  name: new TranslatableMarkup("Wiki Cache Lookup"),
  description: new TranslatableMarkup("Look up a cached wiki page by URL hash."),
  produces: new ContextDefinition(
    data_type: "any",
    label: new TranslatableMarkup("The wiki cache entry"),
  ),
  consumes: [
    "url_hash" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("MD5 hash of the page URL"),
    ),
  ],
)]
final class WikiCacheLookup extends DataProducerPluginBase implements ContainerFactoryPluginInterface {

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
   * Look up the cache entry.
   *
   * @param string $url_hash
   *   MD5 hash of the page URL, used as the node title.
   * @param \Drupal\graphql\GraphQL\Execution\FieldContext $context
   *   The GraphQL field execution context.
   *
   * @return array<string, mixed>|null
   *   The cache entry, or NULL on a miss or when access is denied.
   */
  public function resolve(string $url_hash, FieldContext $context): ?array {
    // Tag every result - hits and misses alike - with the bundle list tag, so
    // writing an entry invalidates a previously cached miss. Without this a
    // miss would be cached indefinitely and the cache could never warm up.
    $context->addCacheTags(['node_list:wiki_cache']);

    $storage = $this->entityTypeManager->getStorage('node');
    $nodes = $storage->loadByProperties([
      'type' => 'wiki_cache',
      'title' => $url_hash,
    ]);
    $node = reset($nodes);
    if (!$node instanceof NodeInterface) {
      return NULL;
    }
    // A denied read is reported as a miss rather than an error: the caller's
    // only sensible response either way is to re-fetch the page.
    if (!$node->access('view', $this->currentUser)) {
      $context->addCacheableDependency($this->currentUser);
      return NULL;
    }
    $context->addCacheableDependency($node);

    return [
      'url' => (string) $node->get('field_wiki_url')->value,
      'fetchedAt' => (float) $node->get('field_wiki_fetched_at')->value,
      'content' => (string) $node->get('field_wiki_content')->value,
    ];
  }

}
