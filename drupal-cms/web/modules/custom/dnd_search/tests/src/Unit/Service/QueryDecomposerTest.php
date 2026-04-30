<?php

declare(strict_types=1);

namespace Drupal\Tests\dnd_search\Unit\Service;

use Drupal\Core\Logger\LoggerChannelFactoryInterface;
use Drupal\Core\Logger\LoggerChannelInterface;
use Drupal\dnd_search\Service\QueryDecomposer;
use Drupal\dnd_search\ValueObject\DecomposedQuery;
use PHPUnit\Framework\TestCase;

/**
 * Unit tests for QueryDecomposer response parsing.
 *
 * The AI provider is mocked for all tests so no real Ollama connection
 * is required. The private parseResponse() method is exercised via
 * reflection to verify JSON handling without triggering an HTTP call.
 *
 * @covers \Drupal\dnd_search\Service\QueryDecomposer
 */
class QueryDecomposerTest extends TestCase {

  /**
   * The QueryDecomposer under test.
   *
   * @var \Drupal\dnd_search\Service\QueryDecomposer
   */
  private QueryDecomposer $decomposer;

  /**
   * {@inheritdoc}
   */
  protected function setUp(): void {
    parent::setUp();

    $loggerChannel = $this->createMock(LoggerChannelInterface::class);
    $loggerFactory = $this->createMock(LoggerChannelFactoryInterface::class);
    $loggerFactory->method('get')->willReturn($loggerChannel);

    // AiProviderPluginManager is final and cannot be mocked by PHPUnit's
    // code-generator. Since parseResponse() only uses $loggerFactory (never
    // $aiProvider), skip the constructor entirely and inject the logger
    // directly via reflection.
    $reflection = new \ReflectionClass(QueryDecomposer::class);
    $this->decomposer = $reflection->newInstanceWithoutConstructor();

    $loggerProp = $reflection->getProperty('loggerFactory');
    $loggerProp->setValue($this->decomposer, $loggerFactory);
  }

  /**
   * Invokes the private parseResponse() method via reflection.
   *
   * @param string $responseText
   *   The raw AI response string to parse.
   * @param string $rawQuery
   *   The original user query (used for fallback).
   *
   * @return \Drupal\dnd_search\ValueObject\DecomposedQuery
   *   The parsed decomposition.
   */
  private function parse(string $responseText, string $rawQuery = 'test query'): DecomposedQuery {
    $method = new \ReflectionMethod(QueryDecomposer::class, 'parseResponse');
    /** @var \Drupal\dnd_search\ValueObject\DecomposedQuery $result */
    $result = $method->invoke($this->decomposer, $responseText, $rawQuery);
    return $result;
  }

  /**
   * Tests that a valid JSON response is parsed into a DecomposedQuery.
   */
  public function testParseResponseValidJsonReturnsDecomposition(): void {
    $json = json_encode([
      'backends' => ['entity_query', 'milvus'],
      'entity_types' => ['character'],
      'filters' => [
        'equipment' => ['Backpack'],
        'species' => [],
        'class' => [],
        'campaign' => [],
      ],
      'semantic_query' => 'adventurer character',
      'keyword_query' => '',
    ]);

    $result = $this->parse((string) $json, 'character who has a backpack');

    $this->assertSame(['entity_query', 'milvus'], $result->backends);
    $this->assertSame(['character'], $result->entityTypes);
    $this->assertSame(['Backpack'], $result->equipmentFilters);
    $this->assertSame('adventurer character', $result->semanticQuery);
  }

  /**
   * Tests that markdown-fenced JSON is unwrapped before parsing.
   */
  public function testParseResponseStripsMarkdownFences(): void {
    $raw = "```json\n" . json_encode([
      'backends' => ['milvus'],
      'entity_types' => [],
      'filters' => ['equipment' => [], 'species' => [], 'class' => [], 'campaign' => []],
      'semantic_query' => 'brooding dark ranger',
      'keyword_query' => '',
    ]) . "\n```";

    $result = $this->parse($raw, 'brooding ranger');

    $this->assertSame(['milvus'], $result->backends);
    $this->assertSame('brooding dark ranger', $result->semanticQuery);
  }

  /**
   * Tests that a JSON object embedded in prose is extracted and parsed.
   */
  public function testParseResponseExtractsEmbeddedJsonObject(): void {
    $embedded = 'Here is the decomposition: ' . json_encode([
      'backends' => ['solr'],
      'entity_types' => ['spell'],
      'filters' => ['equipment' => [], 'species' => [], 'class' => [], 'campaign' => []],
      'semantic_query' => '',
      'keyword_query' => 'Fireball',
    ]);

    $result = $this->parse($embedded, 'Fireball spell');

    $this->assertSame(['solr'], $result->backends);
    $this->assertSame('Fireball', $result->keywordQuery);
  }

  /**
   * Tests that invalid JSON falls back to a Milvus-only decomposition.
   */
  public function testParseResponseInvalidJsonReturnsFallback(): void {
    $result = $this->parse('not json at all', 'fireball');

    $this->assertSame(['milvus'], $result->backends);
    $this->assertSame('fireball', $result->semanticQuery);
  }

  /**
   * Tests that an empty backends list falls back to Milvus-only.
   */
  public function testParseResponseEmptyBackendsReturnsFallback(): void {
    $json = json_encode([
      'backends' => [],
      'entity_types' => [],
      'filters' => ['equipment' => [], 'species' => [], 'class' => [], 'campaign' => []],
      'semantic_query' => 'ranger',
      'keyword_query' => '',
    ]);

    $result = $this->parse((string) $json, 'ranger');

    $this->assertSame(['milvus'], $result->backends);
  }

  /**
   * Tests that unknown backends are stripped from the result.
   */
  public function testParseResponseFiltersUnknownBackends(): void {
    $json = json_encode([
      'backends' => ['milvus', 'elasticsearch', 'redis'],
      'entity_types' => [],
      'filters' => ['equipment' => [], 'species' => [], 'class' => [], 'campaign' => []],
      'semantic_query' => 'wizard',
      'keyword_query' => '',
    ]);

    $result = $this->parse((string) $json, 'wizard');

    $this->assertSame(['milvus'], $result->backends);
  }

  /**
   * Tests that unknown entity types are stripped from the result.
   */
  public function testParseResponseFiltersUnknownEntityTypes(): void {
    $json = json_encode([
      'backends' => ['entity_query'],
      'entity_types' => ['character', 'unknown_type', 'vehicle'],
      'filters' => ['equipment' => ['Sword'], 'species' => [], 'class' => [], 'campaign' => []],
      'semantic_query' => '',
      'keyword_query' => '',
    ]);

    $result = $this->parse((string) $json, 'character with sword');

    $this->assertSame(['character'], $result->entityTypes);
  }

  /**
   * Tests that all three backends are retained when all are valid.
   */
  public function testParseResponseAllBackendsRetained(): void {
    $json = json_encode([
      'backends' => ['entity_query', 'milvus', 'solr'],
      'entity_types' => ['character'],
      'filters' => ['equipment' => ['Torch'], 'species' => ['Elf'], 'class' => ['Wizard'], 'campaign' => []],
      'semantic_query' => 'tragic past',
      'keyword_query' => 'torch',
    ]);

    $result = $this->parse((string) $json, 'elvish wizard with torch and tragic past');

    $this->assertSame(['entity_query', 'milvus', 'solr'], $result->backends);
    $this->assertSame(['Torch'], $result->equipmentFilters);
    $this->assertSame(['Elf'], $result->speciesFilters);
    $this->assertSame(['Wizard'], $result->classFilters);
    $this->assertSame('tragic past', $result->semanticQuery);
    $this->assertSame('torch', $result->keywordQuery);
  }

  /**
   * Tests that non-string filter values are dropped.
   */
  public function testParseResponseDropsNonStringFilterValues(): void {
    $json = json_encode([
      'backends' => ['entity_query'],
      'entity_types' => [],
      'filters' => ['equipment' => [42, '', 'Sword', NULL], 'species' => [], 'class' => [], 'campaign' => []],
      'semantic_query' => '',
      'keyword_query' => '',
    ]);

    $result = $this->parse((string) $json, 'sword');

    $this->assertSame(['42', 'Sword'], $result->equipmentFilters);
  }

}
