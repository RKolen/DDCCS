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
use GraphQL\Error\UserError;
use Symfony\Component\DependencyInjection\ContainerInterface;

/**
 * Create or replace the cached wiki page for a URL hash.
 *
 * Keyed by the hash, which is stored as the node title: an existing entry is
 * overwritten in place so the cache never accumulates duplicates for one URL.
 */
#[DataProducer(
  id: "set_wiki_cache_entry",
  name: new TranslatableMarkup("Set Wiki Cache Entry"),
  description: new TranslatableMarkup("Create or replace a cached wiki page."),
  produces: new ContextDefinition(
    data_type: "any",
    label: new TranslatableMarkup("The stored wiki cache entry"),
  ),
  consumes: [
    "url_hash" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("MD5 hash of the page URL"),
    ),
    "url" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("The original page URL"),
    ),
    "fetched_at" => new ContextDefinition(
      data_type: "float",
      label: new TranslatableMarkup("Unix timestamp of the fetch"),
    ),
    "content" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("Serialized JSON of the page sections"),
    ),
  ],
)]
final class SetWikiCacheEntry extends DataProducerPluginBase implements ContainerFactoryPluginInterface {

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
   * Store the cache entry.
   *
   * @param string $url_hash
   *   MD5 hash of the page URL, used as the node title.
   * @param string $url
   *   The original page URL.
   * @param float $fetched_at
   *   Unix timestamp of when the page was fetched.
   * @param string $content
   *   Serialized JSON of the page's parsed sections.
   * @param \Drupal\graphql\GraphQL\Execution\FieldContext $context
   *   The GraphQL field execution context.
   *
   * @return array<string, mixed>
   *   The stored cache entry.
   *
   * @throws \GraphQL\Error\UserError
   *   When access is denied.
   */
  public function resolve(
    string $url_hash,
    string $url,
    float $fetched_at,
    string $content,
    FieldContext $context,
  ): array {
    $storage = $this->entityTypeManager->getStorage('node');
    $existing = $storage->loadByProperties([
      'type' => 'wiki_cache',
      'title' => $url_hash,
    ]);
    $node = reset($existing);

    if ($node instanceof NodeInterface) {
      if (!$node->access('update', $this->currentUser)) {
        $context->addCacheableDependency($this->currentUser);
        throw new UserError('You do not have permission to update the wiki cache.');
      }
    }
    else {
      /** @var \Drupal\node\NodeInterface $node */
      $node = $storage->create([
        'type' => 'wiki_cache',
        'title' => $url_hash,
      ]);
      if (!$node->access('create', $this->currentUser)) {
        $context->addCacheableDependency($this->currentUser);
        throw new UserError('You do not have permission to create wiki cache entries.');
      }
    }

    $node->set('field_wiki_url', $url);
    $node->set('field_wiki_fetched_at', $fetched_at);
    $node->set('field_wiki_content', [
      'value' => $content,
      'format' => 'plain_text',
    ]);
    $node->save();

    return [
      'url' => $url,
      'fetchedAt' => $fetched_at,
      'content' => $content,
    ];
  }

}
