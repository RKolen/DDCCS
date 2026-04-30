<?php

declare(strict_types=1);

namespace Drupal\dnd_search\ValueObject;

/**
 * Immutable value object representing a decomposed search query.
 *
 * Produced by QueryDecomposer and consumed by SearchController to route
 * the query to the appropriate backend(s).
 */
final readonly class DecomposedQuery {

  /**
   * Constructs a DecomposedQuery.
   *
   * @param list<string> $backends
   *   Non-empty subset of: entity_query, milvus, solr.
   * @param list<string> $entityTypes
   *   Subset of: character, npc, spell, item, feat, monster. Empty means all.
   * @param list<string> $equipmentFilters
   *   Item names the entity must carry.
   * @param list<string> $speciesFilters
   *   Species/race names to filter on.
   * @param list<string> $classFilters
   *   D&D class names (Wizard, Fighter, etc.) to filter on.
   * @param list<string> $campaignFilters
   *   Campaign names to filter on.
   * @param string $semanticQuery
   *   Narrative intent string for Milvus. Empty when milvus not in backends.
   * @param string $keywordQuery
   *   Keyword string for Solr. Empty when solr not in backends.
   */
  public function __construct(
    public readonly array $backends,
    public readonly array $entityTypes,
    public readonly array $equipmentFilters,
    public readonly array $speciesFilters,
    public readonly array $classFilters,
    public readonly array $campaignFilters,
    public readonly string $semanticQuery,
    public readonly string $keywordQuery,
  ) {}

  /**
   * Creates a fallback decomposition that routes only to Milvus.
   *
   * Used when the AI decomposer is unavailable or returns invalid output.
   *
   * @param string $rawQuery
   *   The original raw query string.
   *
   * @return self
   *   A fallback decomposition using the raw query as the semantic query.
   */
  public static function fallback(string $rawQuery): self {
    return new self(
      backends: ['milvus'],
      entityTypes: [],
      equipmentFilters: [],
      speciesFilters: [],
      classFilters: [],
      campaignFilters: [],
      semanticQuery: $rawQuery,
      keywordQuery: '',
    );
  }

  /**
   * Returns TRUE when any structural attribute filter is present.
   *
   * @return bool
   *   TRUE if at least one filter list is non-empty.
   */
  public function hasFilters(): bool {
    return $this->equipmentFilters !== []
      || $this->speciesFilters !== []
      || $this->classFilters !== []
      || $this->campaignFilters !== [];
  }

  /**
   * Returns a serialisable array for inclusion in API responses.
   *
   * @return array<string, mixed>
   *   Decomposition data suitable for JSON encoding.
   */
  public function toArray(): array {
    return [
      'backends' => $this->backends,
      'entity_types' => $this->entityTypes,
      'filters' => [
        'equipment' => $this->equipmentFilters,
        'species' => $this->speciesFilters,
        'class' => $this->classFilters,
        'campaign' => $this->campaignFilters,
      ],
      'semantic_query' => $this->semanticQuery,
      'keyword_query' => $this->keywordQuery,
    ];
  }

}
