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
 * Milvus semantic results. Duplicates are removed by nid.
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

    // Step 3: Merge in priority order, deduplicating by nid.
    $output = [];
    $seen = [];

    foreach ($exactNids as $nid) {
      $row = $this->buildRow($nid, 1.0, 'exact', $entityTypes);
      if ($row !== NULL) {
        $seen[$nid] = TRUE;
        $output[] = $row;
      }
    }

    foreach ($solrRows as ['nid' => $nid, 'score' => $score]) {
      if (isset($seen[$nid])) {
        continue;
      }
      $row = $this->buildRow($nid, $score, 'keyword', $entityTypes);
      if ($row !== NULL) {
        $seen[$nid] = TRUE;
        $output[] = $row;
      }
    }

    foreach ($milvusItems as $item) {
      $nid = (int) ($item->getField('nid')?->getValues()[0] ?? 0);
      if ($nid === 0 || isset($seen[$nid])) {
        continue;
      }
      $row = $this->buildRow(
        $nid,
        round((float) $item->getScore(), 4),
        'semantic',
        $entityTypes,
        $item->getId(),
        (string) ($item->getField('title')?->getValues()[0] ?? ''),
      );
      if ($row !== NULL) {
        $seen[$nid] = TRUE;
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
   * @return list<array{nid: int, score: float}>
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
   * Loads a node and builds a result row, or returns NULL if filtered out.
   *
   * @param int $nid
   *   The node ID.
   * @param float $relevance
   *   Relevance score in [0.0, 1.0].
   * @param string $matchType
   *   One of: exact, keyword, semantic.
   * @param list<string> $entityTypes
   *   Active entity type filter. Empty means all types are accepted.
   * @param string|null $id
   *   Optional Search API item ID; falls back to "entity:node/<nid>".
   * @param string|null $titleFallback
   *   Optional pre-fetched title.
   *
   * @return array<string, mixed>|null
   *   Result row array, or NULL if the node is excluded by the type filter.
   */
  private function buildRow(
    int $nid,
    float $relevance,
    string $matchType,
    array $entityTypes,
    ?string $id = NULL,
    ?string $titleFallback = NULL,
  ): ?array {
    $node = $this->nodeStorage->load($nid);
    if (!$node) {
      return NULL;
    }

    $bundle = $node->bundle();
    if ($entityTypes !== [] && !in_array($bundle, $entityTypes, TRUE)) {
      return NULL;
    }

    return [
      'id' => $id ?? "entity:node/$nid",
      'nid' => $nid,
      'title' => ($titleFallback !== NULL && $titleFallback !== '')
        ? $titleFallback
        : (string) $node->label(),
      'type' => $bundle,
      'relevance' => $relevance,
      'match_type' => $matchType,
    ];
  }

}
