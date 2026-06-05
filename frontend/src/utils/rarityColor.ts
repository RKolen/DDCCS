/** Maps a Drupal itemRarity string to the matching CSS token. */
/* Keys match the Drupal field_item_rarity allowed values exactly */
const RARITY_MAP: Record<string, string> = {
  common:    'var(--color-rarity-common)',
  uncommon:  'var(--color-rarity-uncommon)',
  rare:      'var(--color-rarity-rare)',
  very_rare: 'var(--color-rarity-very-rare)',
  legendary: 'var(--color-rarity-legendary)',
  artifact:  'var(--color-rarity-artifact)',
  vestige:   'var(--color-rarity-vestige)',
};

export function rarityColor(rarity: string | null | undefined): string {
  if (!rarity) return 'var(--color-gold-mid)';
  return RARITY_MAP[rarity.toLowerCase()] ?? 'var(--color-gold-mid)';
}
