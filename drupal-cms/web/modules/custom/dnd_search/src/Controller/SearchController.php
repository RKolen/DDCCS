<?php

declare(strict_types=1);

namespace Drupal\dnd_search\Controller;

use Drupal\Core\Controller\ControllerBase;
use Drupal\node\Entity\Node;
use Drupal\search_api\Entity\Index;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;

/**
 * Exposes the Milvus search index as a JSON endpoint for the Gatsby frontend.
 */
class SearchController extends ControllerBase {

  /**
   * Performs a fulltext search against the Milvus AI content index.
   *
   * GET /api/content-search?q=<query>&type=<content_type>&limit=<n>
   *
   * Milvus does not support pre-filtering by metadata field, so content-type
   * filtering is applied in PHP after fetching a larger candidate set.
   *
   * @param \Symfony\Component\HttpFoundation\Request $request
   *   The incoming HTTP request.
   *
   * @return \Symfony\Component\HttpFoundation\JsonResponse
   *   JSON array of matching results with title, type, nid, and relevance.
   */
  public function search(Request $request): JsonResponse {
    $query_string = trim((string) $request->query->get('q', ''));
    $content_type = trim((string) $request->query->get('type', ''));
    $limit = max(1, min(50, (int) $request->query->get('limit', 20)));

    if ($query_string === '') {
      return new JsonResponse(['results' => [], 'query' => '', 'count' => 0]);
    }

    $index = Index::load('milvus_ai_content');
    if (!$index) {
      return new JsonResponse(['error' => 'Search index not available.'], 503);
    }

    // Fetch a larger candidate pool when type filtering is active so we have
    // enough results after PHP-side filtering.
    $fetch_limit = $content_type !== '' ? min(200, $limit * 10) : $limit;

    $api_query = $index->query();
    $api_query->keys($query_string);
    $api_query->range(0, $fetch_limit);

    try {
      $results = $api_query->execute();
    }
    catch (\Exception $e) {
      return new JsonResponse(['error' => 'Search failed: ' . $e->getMessage()], 500);
    }

    $output = [];
    foreach ($results->getResultItems() as $item) {
      $nid = (int) ($item->getField('nid')?->getValues()[0] ?? 0);
      $node = $nid ? Node::load($nid) : NULL;
      $bundle = $node ? $node->bundle() : '';

      if ($content_type !== '' && $bundle !== $content_type) {
        continue;
      }

      $output[] = [
        'id' => $item->getId(),
        'nid' => $nid,
        'title' => (string) ($item->getField('title')?->getValues()[0] ?? ''),
        'type' => $bundle,
        'relevance' => round((float) $item->getScore(), 4),
      ];

      if (count($output) >= $limit) {
        break;
      }
    }

    return new JsonResponse([
      'query' => $query_string,
      'count' => count($output),
      'results' => $output,
    ]);
  }

}
