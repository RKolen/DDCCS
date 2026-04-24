<?php

declare(strict_types=1);

namespace Drupal\dnd_migrate\Plugin\migrate\source;

use Drupal\migrate\MigrateException;
use Drupal\migrate\Plugin\migrate\source\SourcePluginBase;

/**
 * Source plugin that reads one JSON file per row from a directory.
 *
 * Each .json file in the configured directory becomes one source row.
 * The row identifier is the filename without the .json extension.
 * Files containing "example" in their basename are automatically skipped.
 *
 * All nested objects (ai_config, voice, ability_scores, equipment,
 * relationships, specialized_abilities) are pre-flattened into dedicated
 * source properties so that process pipelines can reference them directly
 * without triggering handle_multiples edge-cases in the extract plugin.
 *
 * Optional configuration:
 *   profile_type_filter: When set, only rows whose profile_type matches this
 *   value are yielded.  Use the empty string "" to match player characters
 *   (files with no profile_type key).
 *
 * Example plugin configuration:
 * @code
 * source:
 *   plugin: dnd_json_directory
 *   data_dir: '/var/www/html/game_data/characters'
 *   profile_type_filter: ''        # player characters only
 * @endcode
 *
 * @MigrateSource(
 *   id = "dnd_json_directory",
 *   source_module = "dnd_migrate"
 * )
 */
class DndJsonDirectory extends SourcePluginBase {

  /**
   * {@inheritdoc}
   *
   * @return array<string, array<string, string>>
   *   Source ID definitions keyed by property name.
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
   *   Human-readable field labels keyed by property name.
   */
  public function fields(): array {
    return [
      // Identity.
      'file_id'             => (string) $this->t('File identifier (filename without .json)'),
      'name'                => (string) $this->t('Full name'),
      'first_name'          => (string) $this->t('First name'),
      'last_name'           => (string) $this->t('Last name'),
      'nickname'            => (string) $this->t('Nickname'),
      'pronouns'            => (string) $this->t('Pronouns string'),
      // Derived identity.
      'gender'              => (string) $this->t('Gender derived from pronouns (female/male/other)'),
      'character_type_is_pc' => (string) $this->t('TRUE when this is a player character'),
      'npc_type_is_simple'  => (string) $this->t('TRUE when NPC profile_type is simplified'),
      // Character sheet.
      'species'             => (string) $this->t('Species name'),
      'lineage'             => (string) $this->t('Lineage name'),
      'dnd_class'           => (string) $this->t('D&D class name'),
      'subclass'            => (string) $this->t('Subclass / archetype'),
      'level'               => (string) $this->t('Character level'),
      'background'          => (string) $this->t('Background name'),
      'max_hit_points'      => (string) $this->t('Maximum hit points'),
      'armor_class'         => (string) $this->t('Armor class'),
      'movement_speed'      => (string) $this->t('Movement speed in feet'),
      'proficiency_bonus'   => (string) $this->t('Proficiency bonus'),
      // Flattened ability scores.
      'ability_str'         => (string) $this->t('Strength score'),
      'ability_dex'         => (string) $this->t('Dexterity score'),
      'ability_con'         => (string) $this->t('Constitution score'),
      'ability_int'         => (string) $this->t('Intelligence score'),
      'ability_wis'         => (string) $this->t('Wisdom score'),
      'ability_cha'         => (string) $this->t('Charisma score'),
      // Skills: flat list of proficient skill names.
      'skill_names'         => (string) $this->t('List of proficient skill names'),
      // Equipment.
      'gold'                => (string) $this->t('Gold pieces from equipment object'),
      'magic_items'         => (string) $this->t('Top-level magic items list'),
      'inert_item_names'    => (string) $this->t('Magic items with (Inert) in name'),
      // Spells / abilities.
      'known_spells'        => (string) $this->t('Known spell names'),
      'spell_slots'         => (string) $this->t('Spell slots keyed by level'),
      'feats'               => (string) $this->t('Feat name strings'),
      'class_abilities'     => (string) $this->t('Class ability name strings'),
      // Normalized specialized_abilities: list of "Name: Description" strings.
      'specialized_abilities_normalized' => (string) $this->t('Specialized abilities as plain strings'),
      // Personality.
      'personality_traits'  => (string) $this->t('Personality traits array'),
      'ideals'              => (string) $this->t('Ideals array'),
      'bonds'               => (string) $this->t('Bonds array'),
      'flaws'               => (string) $this->t('Flaws array'),
      'backstory'           => (string) $this->t('Backstory text'),
      'major_plot_actions'  => (string) $this->t('Major plot actions'),
      // Relationships: array of {target, description} dicts.
      'relationships_list'  => (string) $this->t('Relationships as list of {target, description} arrays'),
      // Flattened AI config.
      'ai_enabled'          => (string) $this->t('AI enabled flag'),
      'ai_model'            => (string) $this->t('AI model name'),
      'ai_temperature'      => (string) $this->t('AI temperature'),
      'ai_max_tokens'       => (string) $this->t('AI max tokens'),
      'ai_system_prompt'    => (string) $this->t('AI system prompt'),
      // Flattened voice config.
      'voice_piper_id'      => (string) $this->t('Piper TTS voice ID'),
      'voice_speed'         => (string) $this->t('Voice speed'),
      'voice_pitch'         => (string) $this->t('Voice pitch shift'),
      // NPC-specific.
      'profile_type'        => (string) $this->t('NPC profile_type (simplified/major)'),
      'faction'             => (string) $this->t('Faction name'),
      'role'                => (string) $this->t('NPC role description'),
      'personality'         => (string) $this->t('NPC personality description'),
      'key_traits'          => (string) $this->t('Key traits array'),
      'recurring'           => (string) $this->t('Whether NPC recurs'),
      'notes'               => (string) $this->t('Free-form notes'),
      'abilities'           => (string) $this->t('NPC generic abilities list'),
      'encounter_tactics'   => (string) $this->t('Encounter tactics'),
      'plot_hooks'          => (string) $this->t('Plot hooks'),
      'defeat_conditions'   => (string) $this->t('Defeat conditions'),
      'legendary_actions'   => (string) $this->t('Legendary actions'),
      'lair_actions'        => (string) $this->t('Lair actions'),
      'regional_effects'    => (string) $this->t('Regional effects'),
    ];
  }

  /**
   * {@inheritdoc}
   */
  public function __toString(): string {
    return $this->configuration['data_dir'] ?? 'dnd_json_directory';
  }

  /**
   * {@inheritdoc}
   *
   * @throws \Drupal\migrate\MigrateException
   */
  protected function initializeIterator(): \Iterator {
    $data_dir = $this->configuration['data_dir'] ?? '';

    if ($data_dir === '') {
      throw new MigrateException('The dnd_json_directory source plugin requires a "data_dir" configuration key.');
    }

    if (!is_dir($data_dir)) {
      throw new MigrateException(sprintf('The configured data_dir "%s" does not exist.', $data_dir));
    }

    $files = glob($data_dir . '/*.json');
    if ($files === FALSE || $files === []) {
      return;
    }

    foreach ($files as $filepath) {
      $basename = basename($filepath, '.json');

      if (str_contains(strtolower($basename), 'example')) {
        continue;
      }

      $raw = file_get_contents($filepath);
      if ($raw === FALSE) {
        continue;
      }

      $data = json_decode($raw, TRUE);
      if (!is_array($data)) {
        continue;
      }

      // Optional: filter by profile_type.
      if (array_key_exists('profile_type_filter', $this->configuration)) {
        $expected = (string) $this->configuration['profile_type_filter'];
        $actual   = (string) ($data['profile_type'] ?? '');
        if ($actual !== $expected) {
          continue;
        }
      }

      yield ['file_id' => $basename] + $data + $this->flatten($data);
    }
  }

  /**
   * Flatten all nested structures into top-level source properties.
   *
   * @param array<string, mixed> $data
   *   Decoded JSON object for one row.
   *
   * @return array<string, mixed>
   *   Flat properties to merge into the source row.
   */
  private function flatten(array $data): array {
    return array_merge(
          $this->flattenIdentity($data),
          $this->flattenAbilityScores($data),
          $this->flattenSkills($data),
          $this->flattenEquipment($data),
          $this->flattenSpecializedAbilities($data),
          $this->flattenRelationships($data),
          $this->flattenAiConfig($data),
          $this->flattenVoice($data),
      );
  }

  /**
   * Derive gender and NPC type flags from JSON metadata.
   *
   * @param array<string, mixed> $data
   *   Source row data.
   *
   * @return array<string, mixed>
   *   Derived identity properties.
   */
  private function flattenIdentity(array $data): array {
    $pronouns = strtolower((string) ($data['pronouns'] ?? ''));
    if (str_contains($pronouns, 'she')) {
      $gender = 'female';
    }
    elseif (str_contains($pronouns, 'he')) {
      $gender = 'male';
    }
    else {
      $gender = 'other';
    }

    // profile_type absent → player character.
    $profile_type = (string) ($data['profile_type'] ?? '');
    $is_pc = ($profile_type === '');
    $is_simple = ($profile_type === 'simplified');

    return [
      'gender'              => $gender,
      'character_type_is_pc' => $is_pc,
      'npc_type_is_simple'  => $is_simple,
    ];
  }

  /**
   * Flatten ability_scores dict into six individual properties.
   *
   * @param array<string, mixed> $data
   *   Source row data.
   *
   * @return array<string, int|null>
   *   Flattened ability score properties.
   */
  private function flattenAbilityScores(array $data): array {
    $scores = is_array($data['ability_scores'] ?? NULL) ? $data['ability_scores'] : [];
    $pick = static function (array $scores, string ...$keys): ?int {
      foreach ($keys as $k) {
        if (isset($scores[$k]) && is_numeric($scores[$k])) {
          return (int) $scores[$k];
        }
      }
      return NULL;
    };

    return [
      'ability_str' => $pick($scores, 'strength', 'str'),
      'ability_dex' => $pick($scores, 'dexterity', 'dex'),
      'ability_con' => $pick($scores, 'constitution', 'con'),
      'ability_int' => $pick($scores, 'intelligence', 'int'),
      'ability_wis' => $pick($scores, 'wisdom', 'wis'),
      'ability_cha' => $pick($scores, 'charisma', 'cha'),
    ];
  }

  /**
   * Extract proficient skill names from the skills dict.
   *
   * Both character format (skill→bool) and NPC format (skill→int modifier)
   * are supported.  All keys present in the dict are treated as proficiencies.
   *
   * @param array<string, mixed> $data
   *   Source row data.
   *
   * @return array<string, list<string>>
   *   Single-key array with 'skill_names' => [...].
   */
  private function flattenSkills(array $data): array {
    $skills = $data['skills'] ?? [];
    if (!is_array($skills) || $skills === []) {
      return ['skill_names' => []];
    }
    return ['skill_names' => array_keys($skills)];
  }

  /**
   * Extract gold and inert magic items from the equipment object.
   *
   * @param array<string, mixed> $data
   *   Source row data.
   *
   * @return array<string, mixed>
   *   Equipment-derived properties.
   */
  private function flattenEquipment(array $data): array {
    $equipment = is_array($data['equipment'] ?? NULL) ? $data['equipment'] : [];
    $gold = isset($equipment['gold']) && is_numeric($equipment['gold'])
        ? (int) $equipment['gold']
        : NULL;

    // Top-level magic_items list (present in both PC and NPC JSON).
    $magic_items = is_array($data['magic_items'] ?? NULL)
        ? array_values(array_filter($data['magic_items'], 'is_string'))
        : [];

    // Inert items: any magic item whose name contains "(Inert)".
    $inert = array_values(array_filter($magic_items, static function (string $name): bool {
        return str_contains($name, '(Inert)');
    }));

    return [
      'gold'            => $gold,
      'magic_items'     => $magic_items,
      'inert_item_names' => $inert,
    ];
  }

  /**
   * Normalize specialized_abilities to a flat list of strings.
   *
   * Character JSON uses a dict (name → description); NPC JSON uses a list.
   * Dict entries are joined as "Name: Description" so no information is lost.
   *
   * @param array<string, mixed> $data
   *   Source row data.
   *
   * @return array<string, list<string>>
   *   Normalized list under 'specialized_abilities_normalized'.
   */
  private function flattenSpecializedAbilities(array $data): array {
    $raw = $data['specialized_abilities'] ?? [];
    if (!is_array($raw) || $raw === []) {
      return ['specialized_abilities_normalized' => []];
    }

    $normalized = [];
    foreach ($raw as $key => $value) {
      if (is_int($key)) {
        // List format (NPC): value is the full string.
        if (is_string($value) && $value !== '') {
          $normalized[] = $value;
        }
      }
      else {
        // Dict format (PC): key = name, value = description.
        $entry = (string) $key;
        if (is_string($value) && $value !== '') {
          $entry .= ': ' . $value;
        }
        $normalized[] = $entry;
      }
    }

    return ['specialized_abilities_normalized' => $normalized];
  }

  /**
   * Convert the relationships dict to a list of arrays for paragraph migration.
   *
   * @param array<string, mixed> $data
   *   Source row data.
   *
   * @return array<string, list<array<string, string>>>
   *   List of {target, description} arrays under 'relationships_list'.
   */
  private function flattenRelationships(array $data): array {
    $raw = $data['relationships'] ?? [];
    if (!is_array($raw) || $raw === []) {
      return ['relationships_list' => []];
    }

    $list = [];
    foreach ($raw as $target => $description) {
      if (!is_string($target) || $target === '') {
        continue;
      }
      $list[] = [
        'target'      => $target,
        'description' => is_string($description) ? $description : '',
      ];
    }

    return ['relationships_list' => $list];
  }

  /**
   * Flatten the ai_config nested object into scalar source properties.
   *
   * @param array<string, mixed> $data
   *   Source row data.
   *
   * @return array<string, mixed>
   *   Flattened AI config properties.
   */
  private function flattenAiConfig(array $data): array {
    $ai = is_array($data['ai_config'] ?? NULL) ? $data['ai_config'] : [];

    return [
      'ai_enabled'      => $ai['enabled'] ?? NULL,
      'ai_model'        => $ai['model'] ?? NULL,
      'ai_temperature'  => isset($ai['temperature']) && is_numeric($ai['temperature'])
        ? (float) $ai['temperature'] : NULL,
      'ai_max_tokens'   => isset($ai['max_tokens']) && is_numeric($ai['max_tokens'])
        ? (int) $ai['max_tokens'] : NULL,
      'ai_system_prompt' => $ai['system_prompt'] ?? NULL,
    ];
  }

  /**
   * Flatten the voice nested object into scalar source properties.
   *
   * @param array<string, mixed> $data
   *   Source row data.
   *
   * @return array<string, mixed>
   *   Flattened voice properties.
   */
  private function flattenVoice(array $data): array {
    $voice = is_array($data['voice'] ?? NULL) ? $data['voice'] : [];
    $vs    = is_array($voice['voice_settings'] ?? NULL) ? $voice['voice_settings'] : [];

    return [
      'voice_piper_id' => $voice['piper_voice_id'] ?? NULL,
      'voice_speed'    => isset($vs['speed']) && is_numeric($vs['speed'])
        ? (float) $vs['speed'] : NULL,
      'voice_pitch'    => isset($vs['pitch_shift']) && is_numeric($vs['pitch_shift'])
        ? (float) $vs['pitch_shift'] : NULL,
    ];
  }

}
