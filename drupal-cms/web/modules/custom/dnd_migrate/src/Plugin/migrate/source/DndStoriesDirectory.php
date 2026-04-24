<?php

declare(strict_types=1);

namespace Drupal\dnd_migrate\Plugin\migrate\source;

use Drupal\migrate\MigrateException;
use Drupal\migrate\Plugin\migrate\source\SourcePluginBase;

/**
 * Source plugin that reads story markdown files from campaign directories.
 *
 * Scans each subdirectory of the configured base_dir for main story files
 * matching the pattern \d+_*.md.  Companion session_results_* and
 * story_hooks_* files are located automatically and merged into each row.
 *
 * The row identifier is "<campaign_slug>__<story_slug>" (e.g.
 * "example_campaign__001_start").  Files containing "example" in their
 * basename are automatically skipped.
 *
 * Example plugin configuration:
 * @code
 * source:
 *   plugin: dnd_stories_directory
 *   base_dir: '/var/www/html/game_data/campaigns'
 * @endcode
 *
 * @MigrateSource(
 *   id = "dnd_stories_directory",
 *   source_module = "dnd_migrate"
 * )
 */
class DndStoriesDirectory extends SourcePluginBase {

  /**
   * {@inheritdoc}
   *
   * @return array<string, array<string, string>>
   *   Field IDs mapped to their type definitions.
   */
  public function getIds(): array {
    return [
      'file_id' => ['type' => 'string'],
    ];
  }

  /**
   * {@inheritdoc}
   *
   * @return array<string, string>
   *   Field names mapped to their human-readable labels.
   */
  public function fields(): array {
    return [
      'file_id' => (string) $this->t('Unique file identifier (campaign__story_slug)'),
      'campaign_name' => (string) $this->t('Campaign name (from directory name)'),
      'campaign_slug' => (string) $this->t('Campaign directory slug'),
      'story_slug' => (string) $this->t('Story slug (filename without .md)'),
      'story_number' => (string) $this->t('Story number (leading digits from filename)'),
      'story_title' => (string) $this->t('Story title (first H1/H2 from markdown)'),
      'body' => (string) $this->t('Full markdown body of the story file'),
      'session_results' => (string) $this->t('Contents of the matching session_results file'),
      'story_hooks' => (string) $this->t('Contents of the matching story_hooks file'),
      'session_date' => (string) $this->t('Session date extracted from session_results header'),
    ];
  }

  /**
   * {@inheritdoc}
   */
  public function __toString(): string {
    return $this->configuration['base_dir'] ?? 'dnd_stories_directory';
  }

  /**
   * {@inheritdoc}
   *
   * @throws \Drupal\migrate\MigrateException
   *   Thrown when base_dir is missing or invalid.
   */
  protected function initializeIterator(): \Iterator {
    $base_dir = $this->configuration['base_dir'] ?? '';

    if ($base_dir === '') {
      throw new MigrateException('The dnd_stories_directory source plugin requires a "base_dir" configuration key.');
    }

    if (!is_dir($base_dir)) {
      throw new MigrateException(sprintf('The configured base_dir "%s" does not exist or is not a directory.', $base_dir));
    }

    $campaign_dirs = glob($base_dir . '/*', GLOB_ONLYDIR);
    if ($campaign_dirs === FALSE || $campaign_dirs === []) {
      return;
    }

    foreach ($campaign_dirs as $campaign_dir) {
      $campaign_slug = basename($campaign_dir);

      $campaign_name = $this->slugToName($campaign_slug);

      // Find main story files: filenames starting with digits.
      // For example: 001_start.md.
      $story_files = glob($campaign_dir . '/*.md');
      if ($story_files === FALSE) {
        continue;
      }

      foreach ($story_files as $filepath) {
        $basename = basename($filepath, '.md');

        // Only process main story files (start with digits).
        if (!preg_match('/^\d+_/', $basename)) {
          continue;
        }

        // Skip example or template files.
        if (str_contains(strtolower($basename), 'example')) {
          continue;
        }

        $body = $this->readFile($filepath);
        if ($body === NULL) {
          continue;
        }

        $story_number = $this->extractStoryNumber($basename);
        $story_title = $this->extractTitle($body) ?? $this->slugToName($basename);
        $file_id = $campaign_slug . '__' . $basename;

        // Find companion files by matching the story slug at the end.
        $session_results = $this->readCompanionFile($campaign_dir, 'session_results_', $basename);
        $story_hooks = $this->readCompanionFile($campaign_dir, 'story_hooks_', $basename);
        $session_date = $this->extractSessionDate($session_results);

        yield [
          'file_id' => $file_id,
          'campaign_name' => $campaign_name,
          'campaign_slug' => $campaign_slug,
          'story_slug' => $basename,
          'story_number' => $story_number,
          'story_title' => $story_title,
          'body' => $body,
          'session_results' => $session_results ?? '',
          'story_hooks' => $story_hooks ?? '',
          'session_date' => $session_date ?? '',
        ];
      }
    }
  }

  /**
   * Read a file and return its contents, or NULL on failure.
   *
   * @param string $filepath
   *   Absolute path to the file.
   *
   * @return string|null
   *   File contents or NULL if unreadable.
   */
  private function readFile(string $filepath): ?string {
    $raw = file_get_contents($filepath);
    if ($raw === FALSE) {
      return NULL;
    }
    // Strip BOM if present.
    return ltrim($raw, "\xEF\xBB\xBF");
  }

  /**
   * Find and read a companion file by prefix and story slug.
   *
   * Companion files follow the naming convention:
   * <prefix><date>_<story_slug>.md
   * e.g. session_results_2025-11-23_001_start.md.
   *
   * @param string $campaign_dir
   *   Directory to search in.
   * @param string $prefix
   *   File prefix (e.g. 'session_results_').
   * @param string $story_slug
   *   The story slug to match at the end (e.g. '001_start').
   *
   * @return string|null
   *   File contents or NULL if not found.
   */
  private function readCompanionFile(string $campaign_dir, string $prefix, string $story_slug): ?string {
    $pattern = $campaign_dir . '/' . $prefix . '*_' . $story_slug . '.md';
    $matches = glob($pattern);
    if ($matches === FALSE || $matches === []) {
      return NULL;
    }
    return $this->readFile(reset($matches));
  }

  /**
   * Extract the leading numeric story number from a slug like "001_start".
   *
   * @param string $slug
   *   The story slug.
   *
   * @return int
   *   The story number, or 0 if none found.
   */
  private function extractStoryNumber(string $slug): int {
    if (preg_match('/^(\d+)/', $slug, $matches)) {
      return (int) $matches[1];
    }
    return 0;
  }

  /**
   * Extract the first H1 or H2 heading from markdown content.
   *
   * @param string $body
   *   Markdown content.
   *
   * @return string|null
   *   Heading text without the # prefix, or NULL if none found.
   */
  private function extractTitle(string $body): ?string {
    if (preg_match('/^#{1,2}\s+(.+)/m', $body, $matches)) {
      return trim($matches[1]);
    }
    return NULL;
  }

  /**
   * Extract the session date from a session_results file header.
   *
   * Looks for a line matching "**Date:** YYYY-MM-DD".
   *
   * @param string|null $session_results
   *   Session results file contents.
   *
   * @return string|null
   *   Date string or NULL if not found.
   */
  private function extractSessionDate(?string $session_results): ?string {
    if ($session_results === NULL || $session_results === '') {
      return NULL;
    }
    if (preg_match('/\*\*Date:\*\*\s+(\d{4}-\d{2}-\d{2})/', $session_results, $matches)) {
      return $matches[1];
    }
    return NULL;
  }

  /**
   * Convert a filesystem slug to a human-readable name.
   *
   * Replaces underscores with spaces and title-cases each word.
   *
   * @param string $slug
   *   The slug to convert (e.g. "example_campaign").
   *
   * @return string
   *   Human-readable name (e.g. "Example Campaign").
   */
  private function slugToName(string $slug): string {
    return ucwords(str_replace('_', ' ', $slug));
  }

}
