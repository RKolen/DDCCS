<?php

declare(strict_types=1);

namespace Drupal\dnd_search\Service;

use Drupal\Core\Entity\EntityTypeManagerInterface;
use Drupal\dnd_search\ValueObject\DecomposedQuery;

/**
 * Resolves structured attribute filters to node IDs using Drupal EntityQuery.
 *
 * All filter conditions are AND-combined: every specified attribute must match.
 * Returns NULL when no filters are present, signalling that the entity_query
 * backend can be skipped.
 */
class StructuredFilterResolver {

  /**
   * Constructs a StructuredFilterResolver.
   *
   * @param \Drupal\Core\Entity\EntityTypeManagerInterface $entityTypeManager
   *   The entity type manager.
   */
  public function __construct(
    private readonly EntityTypeManagerInterface $entityTypeManager,
  ) {}

  /**
   * Returns nids matching all active filters, or NULL when no filters are set.
   *
   * @param \Drupal\dnd_search\ValueObject\DecomposedQuery $query
   *   The decomposed query containing filter lists.
   *
   * @return list<int>|null
   *   Array of matching nids with relevance 1.0 (exact match), or NULL when
   *   the entity_query backend should be skipped.
   *
   * @throws \Drupal\Component\Plugin\Exception\InvalidPluginDefinitionException
   * @throws \Drupal\Component\Plugin\Exception\PluginNotFoundException
   */
  public function resolve(DecomposedQuery $query): ?array {
    if (!$query->hasFilters()) {
      return NULL;
    }

    $nodeQuery = $this->entityTypeManager
      ->getStorage('node')
      ->getQuery()
      ->accessCheck(FALSE)
      ->condition('status', 1);

    if ($query->entityTypes !== []) {
      $nodeQuery->condition('type', $query->entityTypes, 'IN');
    }

    foreach ($query->equipmentFilters as $item) {
      $nodeQuery->condition(
        'field_equipment_items.entity.title',
        '%' . $item . '%',
        'LIKE',
      );
    }

    foreach ($query->speciesFilters as $species) {
      $nodeQuery->condition(
        'field_species.entity.name',
        '%' . $species . '%',
        'LIKE',
      );
    }

    foreach ($query->classFilters as $class) {
      $nodeQuery->condition(
        'field_class.entity.field_character_class.entity.name',
        '%' . $class . '%',
        'LIKE',
      );
    }

    foreach ($query->campaignFilters as $campaign) {
      $nodeQuery->condition(
        'field_campaign.entity.title',
        '%' . $campaign . '%',
        'LIKE',
      );
    }

    $nids = $nodeQuery->execute();
    return array_map('intval', array_values((array) $nids));
  }

}
