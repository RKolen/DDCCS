<?php

declare(strict_types=1);

namespace Drupal\Tests\dnd_search\Unit\ValueObject;

use Drupal\dnd_search\ValueObject\DecomposedQuery;
use PHPUnit\Framework\TestCase;

/**
 * Unit tests for DecomposedQuery value object.
 *
 * @covers \Drupal\dnd_search\ValueObject\DecomposedQuery
 */
class DecomposedQueryTest extends TestCase {

  /**
   * Tests that fallback() routes exclusively to Milvus with the raw query.
   */
  public function testFallbackRoutesMilvusOnly(): void {
    $query = DecomposedQuery::fallback('brooding ranger');

    $this->assertSame(['milvus'], $query->backends);
    $this->assertSame('brooding ranger', $query->semanticQuery);
    $this->assertSame('brooding ranger', $query->semanticQuery);
    $this->assertSame([], $query->entityTypes);
    $this->assertSame([], $query->equipmentFilters);
    $this->assertSame([], $query->speciesFilters);
    $this->assertSame([], $query->classFilters);
    $this->assertSame([], $query->campaignFilters);
    $this->assertSame('', $query->keywordQuery);
  }

  /**
   * Tests that hasFilters() returns TRUE when equipment is specified.
   */
  public function testHasFiltersReturnsTrueWithEquipment(): void {
    $query = new DecomposedQuery(
      backends: ['entity_query'],
      entityTypes: ['character'],
      equipmentFilters: ['Backpack'],
      speciesFilters: [],
      classFilters: [],
      campaignFilters: [],
      semanticQuery: '',
      keywordQuery: '',
    );

    $this->assertTrue($query->hasFilters());
  }

  /**
   * Tests that hasFilters() returns TRUE when any filter list is non-empty.
   */
  #[\PHPUnit\Framework\Attributes\DataProvider('provideFilterCombinations')]
  public function testHasFiltersReturnsTrueForAnyNonEmptyFilter(
    array $equipment,
    array $species,
    array $classes,
    array $campaigns,
  ): void {
    $query = new DecomposedQuery(
      backends: ['entity_query'],
      entityTypes: [],
      equipmentFilters: $equipment,
      speciesFilters: $species,
      classFilters: $classes,
      campaignFilters: $campaigns,
      semanticQuery: '',
      keywordQuery: '',
    );

    $this->assertTrue($query->hasFilters());
  }

  /**
   * Data provider for filter combination tests.
   *
   * @return array<string, array<array<string>>>
   *   Sets of filter combinations, each with one non-empty list.
   */
  public static function provideFilterCombinations(): array {
    return [
      'equipment only' => [['Backpack'], [], [], []],
      'species only'   => [[], ['Elf'], [], []],
      'class only'     => [[], [], ['Wizard'], []],
      'campaign only'  => [[], [], [], ['Dragon Heist']],
    ];
  }

  /**
   * Tests that hasFilters() returns FALSE when all filter lists are empty.
   */
  public function testHasFiltersReturnsFalseWhenAllEmpty(): void {
    $query = new DecomposedQuery(
      backends: ['milvus'],
      entityTypes: [],
      equipmentFilters: [],
      speciesFilters: [],
      classFilters: [],
      campaignFilters: [],
      semanticQuery: 'brooding ranger',
      keywordQuery: '',
    );

    $this->assertFalse($query->hasFilters());
  }

  /**
   * Tests that toArray() produces the correct shape.
   */
  public function testToArrayShape(): void {
    $query = new DecomposedQuery(
      backends: ['entity_query', 'milvus'],
      entityTypes: ['character'],
      equipmentFilters: ['Backpack'],
      speciesFilters: ['Elf'],
      classFilters: ['Wizard'],
      campaignFilters: [],
      semanticQuery: 'adventurer',
      keywordQuery: '',
    );

    $array = $query->toArray();

    $this->assertSame(['entity_query', 'milvus'], $array['backends']);
    $this->assertSame(['character'], $array['entity_types']);
    $this->assertSame(['Backpack'], $array['filters']['equipment']);
    $this->assertSame(['Elf'], $array['filters']['species']);
    $this->assertSame(['Wizard'], $array['filters']['class']);
    $this->assertSame([], $array['filters']['campaign']);
    $this->assertSame('adventurer', $array['semantic_query']);
    $this->assertSame('', $array['keyword_query']);
  }

}
