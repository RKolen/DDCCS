<?php

declare(strict_types=1);

namespace Drupal\dnd_search\Controller;

use Drupal\Core\Controller\ControllerBase;
use Drupal\Core\Entity\EntityStorageInterface;
use Drupal\Core\Logger\LoggerChannelInterface;
use Drupal\dnd_search\Service\QueryDecomposer;
use Drupal\dnd_search\Service\SolrResolver;
use Drupal\dnd_search\Service\StructuredFilterResolver;
use Drupal\dnd_search\ValueObject\DecomposedQuery;
use Drupal\node\NodeInterface;
use Drupal\taxonomy\TermInterface;
use Symfony\Component\DependencyInjection\ContainerInterface;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;

/**
 * Exposes a multi-backend JSON search endpoint for the Gatsby frontend.
 *
 * Each incoming query is decomposed by the AI-powered QueryDecomposer, which
 * selects one or more backends (EntityQuery, Solr, Milvus) and extracts
 * structured filters. Results from all active backends are merged in priority
 * order: exact EntityQuery matches first, then Solr keyword results, then
 * Milvus semantic results. Duplicates are removed by Search API item id.
 */
class SearchController extends ControllerBase {

  /**
   * The query decomposer service.
   *
   * @var \Drupal\dnd_search\Service\QueryDecomposer
   */
  private QueryDecomposer $queryDecomposer;

  /**
   * The structured filter resolver service.
   *
   * @var \Drupal\dnd_search\Service\StructuredFilterResolver
   */
  private StructuredFilterResolver $structuredFilterResolver;

  /**
   * The Solr resolver service.
   *
   * @var \Drupal\dnd_search\Service\SolrResolver
   */
  private SolrResolver $solrResolver;

  /**
   * The node entity storage.
   *
   * @var \Drupal\Core\Entity\EntityStorageInterface
   */
  private EntityStorageInterface $nodeStorage;

  /**
   * The taxonomy term entity storage.
   *
   * @var \Drupal\Core\Entity\EntityStorageInterface
   */
  private EntityStorageInterface $termStorage;

  /**
   * The Search API index entity storage.
   *
   * @var \Drupal\Core\Entity\EntityStorageInterface
   */
  private EntityStorageInterface $indexStorage;

  /**
   * The dnd_search logger channel.
   *
   * @var \Drupal\Core\Logger\LoggerChannelInterface
   */
  private LoggerChannelInterface $dndLogger;

  /**
   * {@inheritdoc}
   *
   * @throws \Drupal\Component\Plugin\Exception\InvalidPluginDefinitionException
   * @throws \Drupal\Component\Plugin\Exception\PluginNotFoundException
   */
  public static function create(ContainerInterface $container): static {
    $instance = parent::create($container);
    $instance->queryDecomposer = $container->get('dnd_search.query_decomposer');
    $instance->structuredFilterResolver = $container->get('dnd_search.structured_filter_resolver');
    $instance->solrResolver = $container->get('dnd_search.solr_resolver');
    /** @var \Drupal\Core\Logger\LoggerChannelInterface $dndLogger */
    $dndLogger = $container->get('logger.channel.dnd_search');
    $instance->dndLogger = $dndLogger;

    /** @var \Drupal\Core\Entity\EntityTypeManagerInterface $etm */
    $etm = $container->get('entity_type.manager');
    $instance->nodeStorage = $etm->getStorage('node');
    $instance->termStorage = $etm->getStorage('taxonomy_term');
    $instance->indexStorage = $etm->getStorage('search_api_index');

    return $instance;
  }

  /**
   * Performs a multi-backend search and returns merged, ranked results.
   *
   * GET /api/content-search?q=<query>&type=<content_type>&limit=<n>
   *
   * The optional `type` parameter overrides the AI-inferred entity type.
   *
   * @param \Symfony\Component\HttpFoundation\Request $request
   *   The incoming HTTP request.
   *
   * @return \Symfony\Component\HttpFoundation\JsonResponse
   *   JSON response with query, decomposition metadata, count, and results.
   */
  public function search(Request $request): JsonResponse {
    $rawQuery = trim((string) $request->query->get('q', ''));
    $typeOverride = trim((string) $request->query->get('type', ''));
    $limit = max(1, min(50, (int) $request->query->get('limit', 20)));

    if ($rawQuery === '') {
      return new JsonResponse(['results' => [], 'query' => '', 'count' => 0]);
    }

    $totalStart = microtime(TRUE);

    // Step 1: Decompose the query into structured intent.
    $decomposeStart = microtime(TRUE);
    $decomposition = $this->queryDecomposer->decompose($rawQuery);
    $decomposeMs = (int) round((microtime(TRUE) - $decomposeStart) * 1000);

    // A caller-supplied type parameter overrides the AI-inferred entity types.
    $entityTypes = $typeOverride !== '' ? [$typeOverride] : $decomposition->entityTypes;

    // Step 2: Run all selected backends and collect raw results.
    $entityQueryStart = microtime(TRUE);
    $exactNids = $this->runEntityQuery($decomposition);
    $entityQueryMs = (in_array('entity_query', $decomposition->backends, TRUE) && $decomposition->hasFilters())
      ? (int) round((microtime(TRUE) - $entityQueryStart) * 1000)
      : NULL;

    $solrStart = microtime(TRUE);
    $solrRows = $this->runSolrQuery($decomposition, $limit);
    $solrMs = in_array('solr', $decomposition->backends, TRUE)
      ? (int) round((microtime(TRUE) - $solrStart) * 1000)
      : NULL;

    $milvusStart = microtime(TRUE);
    $milvusItems = $this->runMilvusQuery($decomposition, $rawQuery, $limit);
    $milvusMs = in_array('milvus', $decomposition->backends, TRUE)
      ? (int) round((microtime(TRUE) - $milvusStart) * 1000)
      : NULL;

    // Step 3: Merge in priority order, deduplicating by Search API item id.
    $output = [];
    $seen = [];

    foreach ($exactNids as $nid) {
      $node = $this->nodeStorage->load($nid);
      if (!$node instanceof NodeInterface) {
        continue;
      }
      $key = $this->dedupeKey('entity:node/' . $nid);
      $row = $this->buildRowFromEntity($node, 1.0, 'exact', $entityTypes);
      if ($row !== NULL) {
        $seen[$key] = TRUE;
        $output[] = $row;
      }
    }

    foreach ($solrRows as ['id' => $itemId, 'score' => $score]) {
      $key = $this->dedupeKey($itemId);
      if (isset($seen[$key])) {
        continue;
      }
      $entity = $this->entityFromItemId($itemId);
      if ($entity === NULL) {
        continue;
      }
      $row = $this->buildRowFromEntity($entity, $score, 'keyword', $entityTypes, $itemId);
      if ($row !== NULL) {
        $seen[$key] = TRUE;
        $output[] = $row;
      }
    }

    foreach ($milvusItems as $item) {
      $itemId = $item->getId();
      $key = $this->dedupeKey($itemId);
      if (isset($seen[$key])) {
        continue;
      }
      $entity = $this->entityFromItemId($itemId);
      if ($entity === NULL) {
        continue;
      }
      $row = $this->buildRowFromEntity(
        $entity,
        round((float) $item->getScore(), 4),
        'semantic',
        $entityTypes,
        $itemId,
      );
      if ($row !== NULL) {
        $seen[$key] = TRUE;
        $output[] = $row;
      }
    }

    $output = array_slice($output, 0, $limit);

    $totalMs = (int) round((microtime(TRUE) - $totalStart) * 1000);

    $decompositionData = $decomposition->toArray();
    $decompositionData['timings'] = [
      'decompose_ms' => $decomposeMs,
      'entity_query_ms' => $entityQueryMs,
      'solr_ms' => $solrMs,
      'milvus_ms' => $milvusMs,
      'total_ms' => $totalMs,
    ];

    return new JsonResponse([
      'query' => $rawQuery,
      'count' => count($output),
      'decomposition' => $decompositionData,
      'results' => $output,
    ]);
  }

  /**
   * Runs the EntityQuery backend and returns exact-match nids.
   *
   * @param \Drupal\dnd_search\ValueObject\DecomposedQuery $decomposition
   *   The decomposed query.
   *
   * @return list<int>
   *   Nids of nodes matching all structured filters, or empty array.
   */
  private function runEntityQuery(DecomposedQuery $decomposition): array {
    if (!in_array('entity_query', $decomposition->backends, TRUE)
      || !$decomposition->hasFilters()
    ) {
      return [];
    }

    try {
      return $this->structuredFilterResolver->resolve($decomposition) ?? [];
    }
    catch (\Exception $e) {
      $this->dndLogger->warning(
        'EntityQuery backend failed: @msg',
        ['@msg' => $e->getMessage()],
      );
      return [];
    }
  }

  /**
   * Runs the Solr keyword backend.
   *
   * @param \Drupal\dnd_search\ValueObject\DecomposedQuery $decomposition
   *   The decomposed query.
   * @param int $limit
   *   The user-requested result limit.
   *
   * @return list<array{id: string, score: float}>
   *   Solr results sorted by normalised score, or empty array.
   */
  private function runSolrQuery(DecomposedQuery $decomposition, int $limit): array {
    if (!in_array('solr', $decomposition->backends, TRUE)) {
      return [];
    }
    return $this->solrResolver->search($decomposition, $limit * 5);
  }

  /**
   * Runs the Milvus semantic backend.
   *
   * @param \Drupal\dnd_search\ValueObject\DecomposedQuery $decomposition
   *   The decomposed query.
   * @param string $rawQuery
   *   The original user query, used as fallback when semantic_query is empty.
   * @param int $limit
   *   The user-requested result limit.
   *
   * @return list<\Drupal\search_api\Item\ItemInterface>
   *   Search API result items, or empty array on any failure.
   */
  private function runMilvusQuery(
    DecomposedQuery $decomposition,
    string $rawQuery,
    int $limit,
  ): array {
    if (!in_array('milvus', $decomposition->backends, TRUE)) {
      return [];
    }

    $semanticQuery = $decomposition->semanticQuery !== ''
      ? $decomposition->semanticQuery
      : $rawQuery;

    /** @var \Drupal\search_api\IndexInterface|null $index */
    $index = $this->indexStorage->load('milvus_ai_content');
    if (!$index) {
      return [];
    }

    $fetchLimit = $decomposition->entityTypes !== []
      ? min(200, $limit * 10)
      : $limit * 3;

    try {
      $apiQuery = $index->query();
      $apiQuery->keys($semanticQuery);
      $apiQuery->range(0, $fetchLimit);
      return iterator_to_array($apiQuery->execute()->getResultItems(), FALSE);
    }
    catch (\Exception $e) {
      $this->dndLogger->warning(
        'Milvus backend failed: @msg',
        ['@msg' => $e->getMessage()],
      );
      return [];
    }
  }

  /**
   * Builds a result row from a node or spells term.
   *
   * Spell terms report type "spell" so the frontend filter matches the
   * decomposer's entity_types. `nid` is the node id or the term id.
   *
   * @param \Drupal\node\NodeInterface|\Drupal\taxonomy\TermInterface $entity
   *   The matched entity.
   * @param float $relevance
   *   Relevance score in [0.0, 1.0].
   * @param string $matchType
   *   One of: exact, keyword, semantic.
   * @param list<string> $entityTypes
   *   Active entity type filter. Empty means all types are accepted.
   * @param string|null $id
   *   Optional Search API item ID.
   *
   * @return array<string, mixed>|null
   *   Result row array, or NULL if the entity is excluded by the type filter.
   */
  private function buildRowFromEntity(
    NodeInterface|TermInterface $entity,
    float $relevance,
    string $matchType,
    array $entityTypes,
    ?string $id = NULL,
  ): ?array {
    if ($entity instanceof TermInterface) {
      if ($entity->bundle() !== 'spells') {
        return NULL;
      }
      $type = 'spell';
      $entity_id = (int) $entity->id();
      $row_id = $id ?? 'entity:taxonomy_term/' . $entity_id;
    }
    else {
      $type = $entity->bundle();
      $entity_id = (int) $entity->id();
      $row_id = $id ?? 'entity:node/' . $entity_id;
    }

    if ($entityTypes !== [] && !in_array($type, $entityTypes, TRUE)) {
      return NULL;
    }

    return [
      'id' => $row_id,
      'nid' => $entity_id,
      'title' => (string) $entity->label(),
      'type' => $type,
      'relevance' => $relevance,
      'match_type' => $matchType,
    ];
  }

  /**
   * Load a node or term from a Search API item id.
   *
   * @param string $itemId
   *   Item id such as entity:node/12:en or entity:taxonomy_term/34:en.
   *
   * @return \Drupal\node\NodeInterface|\Drupal\taxonomy\TermInterface|null
   *   The entity, or NULL when the id is not recognised or the load fails.
   */
  private function entityFromItemId(string $itemId): NodeInterface|TermInterface|null {
    if (preg_match('#^entity:(node|taxonomy_term)/(\d+)#', $itemId, $matches) !== 1) {
      return NULL;
    }
    $storage = $matches[1] === 'node' ? $this->nodeStorage : $this->termStorage;
    $entity = $storage->load((int) $matches[2]);
    if ($entity instanceof NodeInterface || $entity instanceof TermInterface) {
      return $entity;
    }
    return NULL;
  }

  /**
   * Normalise a Search API item id for duplicate detection.
   *
   * @param string $itemId
   *   Raw item id, possibly with a language suffix.
   *
   * @return string
   *   entity:{type}/{id} without the language suffix.
   */
  private function dedupeKey(string $itemId): string {
    if (preg_match('#^(entity:[^/]+/\d+)#', $itemId, $matches) === 1) {
      return $matches[1];
    }
    return $itemId;
  }

}
