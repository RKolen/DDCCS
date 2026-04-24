<?php

declare(strict_types=1);

namespace Drupal\dnd_migrate\Plugin\migrate\process;

use Drupal\migrate\MigrateExecutableInterface;
use Drupal\migrate\ProcessPluginBase;
use Drupal\migrate\Row;

/**
 * Joins a PHP array into a single string using a configurable separator.
 *
 * Use this process plugin when a migration source field holds an array
 * of strings that must be stored in a single Drupal text field.
 *
 * Example configuration using a newline separator:
 * @code
 * process:
 *   field_personality_traits:
 *     plugin: dnd_join_array
 *     source: personality_traits
 *     separator: "\n"
 * @endcode
 *
 * When the source value is already a string it is returned unchanged.
 * When the source value is NULL or an empty array an empty string is returned.
 *
 * @MigrateProcessPlugin(
 *   id = "dnd_join_array",
 *   handle_multiples = FALSE
 * )
 */
class DndJoinArray extends ProcessPluginBase {

  /**
   * {@inheritdoc}
   *
   * @param mixed $value
   *   The source value, expected to be an array or scalar.
   * @param \Drupal\migrate\MigrateExecutableInterface $migrate_executable
   *   The migration executable.
   * @param \Drupal\migrate\Row $row
   *   The current source row.
   * @param string $destination_property
   *   The destination property name.
   *
   * @return string
   *   The joined string, or the original value cast to string.
   */
  public function transform(
    $value,
    MigrateExecutableInterface $migrate_executable,
    Row $row,
    $destination_property,
  ): string {
    if ($value === NULL) {
      return '';
    }

    if (is_array($value)) {
      $separator = (string) ($this->configuration['separator'] ?? ', ');
      return implode($separator, array_filter(array_map('strval', $value)));
    }

    return (string) $value;
  }

}
