<?php

declare(strict_types=1);

namespace Drupal\dnd_search\Service;

use Drupal\ai\AiProviderPluginManager;
use Drupal\ai\OperationType\Chat\ChatInput;
use Drupal\ai\OperationType\Chat\ChatMessage;
use Drupal\ai\OperationType\Chat\ChatOutput;
use Drupal\Core\Logger\LoggerChannelFactoryInterface;
use Drupal\dnd_search\ValueObject\DecomposedQuery;

/**
 * Decomposes a natural-language search query using the configured AI provider.
 *
 * Sends the raw query to Ollama (or any configured chat provider) and parses
 * the structured JSON response into a DecomposedQuery value object. Falls back
 * gracefully to a Milvus-only decomposition on any failure.
 */
class QueryDecomposer {

  private const VALID_BACKENDS = ['entity_query', 'milvus', 'solr'];

  private const VALID_ENTITY_TYPES = [
    'character',
    'npc',
    'spell',
    'item',
    'feat',
    'monster',
  ];

  /**
   * Constructs a QueryDecomposer.
   *
   * @param \Drupal\ai\AiProviderPluginManager $aiProvider
   *   The AI provider plugin manager.
   * @param \Drupal\Core\Logger\LoggerChannelFactoryInterface $loggerFactory
   *   The logger channel factory.
   */
  public function __construct(
    private readonly AiProviderPluginManager $aiProvider,
    private readonly LoggerChannelFactoryInterface $loggerFactory,
  ) {}

  /**
   * Decomposes a raw query into structured search intent.
   *
   * @param string $rawQuery
   *   The raw natural-language search query from the user.
   *
   * @return \Drupal\dnd_search\ValueObject\DecomposedQuery
   *   Structured decomposition, or a Milvus-only fallback on any failure.
   */
  public function decompose(string $rawQuery): DecomposedQuery {
    $default = $this->aiProvider->getDefaultProviderForOperationType('chat');
    if (!is_array($default) || empty($default['provider_id'])) {
      return DecomposedQuery::fallback($rawQuery);
    }

    try {
      // getDefaultProviderForOperationType('chat') already guarantees the
      // provider supports chat. ProviderProxy delegates via __call(); the call
      // is safe at runtime — see phpstan.neon ignoreErrors for the suppression.
      $provider = $this->aiProvider->createInstance($default['provider_id']);
      $input = new ChatInput([
        new ChatMessage('system', $this->buildSystemPrompt()),
        new ChatMessage('user', $rawQuery),
      ]);
      $output = $this->executeChat($provider, $input, (string) $default['model_id']);
      $text = $output->getNormalized()->getText();
      return $this->parseResponse((string) $text, $rawQuery);
    }
    catch (\Throwable $e) {
      $this->loggerFactory->get('dnd_search')->warning(
        'QueryDecomposer: AI call failed — @msg',
        ['@msg' => $e->getMessage()],
      );
      return DecomposedQuery::fallback($rawQuery);
    }
  }

  /**
   * Parses the raw AI response string into a DecomposedQuery.
   *
   * @param string $text
   *   Raw text returned by the AI provider.
   * @param string $rawQuery
   *   The original query, used for fallback.
   *
   * @return \Drupal\dnd_search\ValueObject\DecomposedQuery
   *   Parsed decomposition, or Milvus-only fallback on parse failure.
   */
  private function parseResponse(string $text, string $rawQuery): DecomposedQuery {
    $cleaned = (string) preg_replace('/```(?:json)?\s*|\s*```/', '', $text);
    $cleaned = trim($cleaned);

    if (preg_match('/\{.*\}/s', $cleaned, $matches)) {
      $cleaned = $matches[0];
    }

    try {
      $data = json_decode($cleaned, TRUE, 512, JSON_THROW_ON_ERROR);
    }
    catch (\JsonException $e) {
      $this->loggerFactory->get('dnd_search')->warning(
        'QueryDecomposer: malformed JSON — @msg',
        ['@msg' => $e->getMessage()],
      );
      return DecomposedQuery::fallback($rawQuery);
    }

    if (!is_array($data) || empty($data['backends'])) {
      return DecomposedQuery::fallback($rawQuery);
    }

    $backends = array_values(
      array_intersect((array) $data['backends'], self::VALID_BACKENDS)
    );

    if ($backends === []) {
      return DecomposedQuery::fallback($rawQuery);
    }

    $entityTypes = array_values(
      array_intersect(
        (array) ($data['entity_types'] ?? []),
        self::VALID_ENTITY_TYPES,
      )
    );

    $filters = is_array($data['filters'] ?? NULL) ? (array) $data['filters'] : [];

    return new DecomposedQuery(
      backends: $backends,
      entityTypes: $entityTypes,
      equipmentFilters: $this->toStringList($filters['equipment'] ?? []),
      speciesFilters: $this->toStringList($filters['species'] ?? []),
      classFilters: $this->toStringList($filters['class'] ?? []),
      campaignFilters: $this->toStringList($filters['campaign'] ?? []),
      semanticQuery: (string) ($data['semantic_query'] ?? ''),
      keywordQuery: (string) ($data['keyword_query'] ?? ''),
    );
  }

  /**
   * Coerces a value to a list of non-empty strings.
   *
   * @param mixed $value
   *   Raw value from the decoded JSON.
   *
   * @return list<string>
   *   Filtered list of non-empty strings.
   */
  private function toStringList(mixed $value): array {
    if (!is_array($value)) {
      return [];
    }
    return array_values(
      array_filter(
        array_map('strval', $value),
        static fn(string $s): bool => $s !== '',
      )
    );
  }

  /**
   * Invokes chat() on the provider proxy and returns a typed ChatOutput.
   *
   * ProviderProxy delegates all methods via __call() (see phpstan.neon for the
   * suppressed "undefined method" error). This wrapper isolates the call so
   * PHPStan can verify callers receive a properly-typed return value.
   *
   * @param mixed $provider
   *   The provider proxy returned by AiProviderPluginManager::createInstance().
   * @param \Drupal\ai\OperationType\Chat\ChatInput $input
   *   The chat input containing system and user messages.
   * @param string $modelId
   *   The model identifier to use for the request.
   *
   * @return \Drupal\ai\OperationType\Chat\ChatOutput
   *   The chat completion output from the provider.
   */
  private function executeChat(mixed $provider, ChatInput $input, string $modelId): ChatOutput {
    /** @var ChatOutput $output */
    $output = $provider->chat($input, $modelId, ['dnd_search']);
    return $output;
  }

  /**
   * Returns the system prompt for the query decomposer.
   *
   * @return string
   *   The system prompt instructing the AI how to decompose queries.
   */
  private function buildSystemPrompt(): string {
    return <<<'PROMPT'
You are a D&D database query parser. Given a natural language search query,
extract structured filters, choose which search backends to use, and produce
search strings for each active backend.

Available backends:
- "entity_query": exact structured attribute matching (equipment carried,
  species/race, class, campaign). Use when the query references specific
  attributes an entity must have.
- "milvus": semantic/vector search for narrative intent, personality,
  backstory, vibe, similarity. Use when the query describes a character
  concept, feeling, or asks for similarity.
- "solr": full-text keyword search. Use when the query contains specific
  names, game terms, or exact phrases that should match text literally.

Return ONLY valid JSON in this exact shape — no prose, no markdown fences:
{
  "backends": [],
  "entity_types": [],
  "filters": {
    "equipment": [],
    "species": [],
    "class": [],
    "campaign": []
  },
  "semantic_query": "",
  "keyword_query": ""
}

Examples:
  Input:  "find character who has a backpack"
  Output: {"backends":["entity_query","milvus"],"entity_types":["character"],"filters":{"equipment":["Backpack"],"species":[],"class":[],"campaign":[]},"semantic_query":"adventurer character","keyword_query":""}

  Input:  "brooding ranger with a dark past"
  Output: {"backends":["milvus"],"entity_types":[],"filters":{"equipment":[],"species":[],"class":[],"campaign":[]},"semantic_query":"brooding dark troubled past ranger","keyword_query":""}

  Input:  "Fireball spell"
  Output: {"backends":["solr"],"entity_types":["spell"],"filters":{"equipment":[],"species":[],"class":[],"campaign":[]},"semantic_query":"","keyword_query":"Fireball"}

  Input:  "list all Wizards"
  Output: {"backends":["entity_query"],"entity_types":[],"filters":{"equipment":[],"species":[],"class":["Wizard"],"campaign":[]},"semantic_query":"","keyword_query":""}

  Input:  "spells that deal cold damage"
  Output: {"backends":["solr","milvus"],"entity_types":["spell"],"filters":{"equipment":[],"species":[],"class":[],"campaign":[]},"semantic_query":"cold damage spells ice frost","keyword_query":"cold damage"}

  Input:  "Elvish wizard with a tragic past who carries a torch"
  Output: {"backends":["entity_query","milvus"],"entity_types":[],"filters":{"equipment":[],"species":["Elf"],"class":["Wizard"],"campaign":[]},"semantic_query":"tragic past mysterious dark","keyword_query":""}
PROMPT;
  }

}
