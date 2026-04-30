<?php

declare(strict_types=1);

namespace Drupal\dnd_search\Service;

use Drupal\Core\Entity\EntityTypeManagerInterface;
use Drupal\Core\Logger\LoggerChannelFactoryInterface;
use Drupal\dnd_search\ValueObject\DecomposedQuery;

/**
 * Resolves keyword queries against a Solr Search API index.
 *
 * Scores are normalised to [0.0, 1.0] relative to the top result so they are
 * comparable to Milvus cosine similarity scores. Falls back gracefully when the
 * Solr index is not yet configured.
 */
class SolrResolver {

  /**
   * The Search API index machine name for the Solr keyword index.
   *
   * Configure a dedicated Solr index in the Drupal admin and set this value
   * to match its machine name.
   */
  private const INDEX_ID = 'solr_content';

  /**
   * Constructs a SolrResolver.
   *
   * @param \Drupal\Core\Entity\EntityTypeManagerInterface $entityTypeManager
   *   The entity type manager.
   * @param \Drupal\Core\Logger\LoggerChannelFactoryInterface $loggerFactory
   *   The logger channel factory.
   */
  public function __construct(
    private readonly EntityTypeManagerInterface $entityTypeManager,
    private readonly LoggerChannelFactoryInterface $loggerFactory,
  ) {}

  /**
   * Searches Solr for the keyword_query in the decomposition.
   *
   * @param \Drupal\dnd_search\ValueObject\DecomposedQuery $query
   *   The decomposed query containing the keyword string.
   * @param int $limit
   *   Maximum number of raw results to fetch before normalisation.
   *
   * @return list<array{nid: int, score: float}>
   *   Results sorted by normalised score descending, or empty on any failure.
   */
  public function search(DecomposedQuery $query, int $limit): array {
    if ($query->keywordQuery === '') {
      return [];
    }

    $index = $this->entityTypeManager
      ->getStorage('search_api_index')
      ->load(self::INDEX_ID);

    if ($index === NULL) {
      $this->loggerFactory->get('dnd_search')->notice(
        'SolrResolver: index "@id" not found — Solr results skipped.',
        ['@id' => self::INDEX_ID],
      );
      return [];
    }

    try {
      /** @var \Drupal\search_api\IndexInterface $index */
      $apiQuery = $index->query();
      $apiQuery->keys($query->keywordQuery);
      $apiQuery->range(0, $limit);
      $results = $apiQuery->execute();
    }
    catch (\Exception $e) {
      $this->loggerFactory->get('dnd_search')->warning(
        'SolrResolver: query failed — @msg',
        ['@msg' => $e->getMessage()],
      );
      return [];
    }

    $rows = [];
    foreach ($results->getResultItems() as $item) {
      $nid = (int) ($item->getField('nid')?->getValues()[0] ?? 0);
      if ($nid === 0) {
        continue;
      }
      $rows[] = ['nid' => $nid, 'score' => (float) $item->getScore()];
    }

    if ($rows === []) {
      return [];
    }

    $maxScore = max(array_column($rows, 'score'));
    if ($maxScore > 0.0) {
      foreach ($rows as &$row) {
        $row['score'] = round($row['score'] / $maxScore, 4);
      }
      unset($row);
    }

    return $rows;
  }

}
