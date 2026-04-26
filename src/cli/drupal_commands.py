"""CLI commands for Drupal CMS sync.

Provides run_sync_drupal() which is invoked by the --sync-drupal flag in
dnd_consultant.py. Pushes character and story updates to Drupal via JSON:API
and optionally triggers a Gatsby incremental build.
"""

from pathlib import Path

from src.config.config_loader import load_config
from src.integration.drupal_sync import DrupalSync, DrupalSyncError
from src.utils.path_utils import get_characters_dir
from src.utils.terminal_display import print_error, print_info, print_warning


def run_sync_drupal(campaign: str = "") -> None:
    """Push character and story updates to Drupal via JSON:API.

    Pushes all character files from game_data/characters/. When a campaign
    name is given, also pushes story Markdown files from
    game_data/campaigns/<campaign>/. Triggers a Gatsby incremental build if
    a webhook URL is configured.

    Args:
        campaign: Optional campaign name. Story files are only synced when
            this is non-empty.
    """
    cfg = load_config().drupal
    if not cfg.base_url:
        print_error(
            "DRUPAL_BASE_URL is not configured."
            " Set it in .env or game_data/config.json."
        )
        return

    sync = DrupalSync(cfg)
    total_chars = 0
    total_stories = 0
    errors = 0

    print_info(f"Syncing to Drupal: {cfg.base_url}")

    for json_file in sorted(Path(get_characters_dir()).glob("*.json")):
        try:
            uuid = sync.push_character(json_file)
            print_info(f"  character: {json_file.stem} ({uuid})")
            total_chars += 1
        except DrupalSyncError as exc:
            print_warning(f"  character: {json_file.stem} - {exc}")
            errors += 1

    if campaign:
        story_dir = Path("game_data/campaigns") / campaign
        if not story_dir.exists():
            print_warning(f"Campaign directory not found: {story_dir}")
        else:
            for md_file in sorted(story_dir.glob("*.md")):
                try:
                    uuid = sync.push_story(md_file, campaign)
                    print_info(f"  story: {md_file.stem} ({uuid})")
                    total_stories += 1
                except DrupalSyncError as exc:
                    print_warning(f"  story: {md_file.stem} - {exc}")
                    errors += 1

    summary = f"Sync complete: {total_chars} characters, {total_stories} stories"
    if errors:
        summary += f", {errors} errors"
    print_info(summary)

    if cfg.gatsby_webhook_url:
        try:
            sync.trigger_gatsby_build()
            print_info("Gatsby incremental build triggered.")
        except DrupalSyncError as exc:
            print_warning(f"Gatsby webhook failed: {exc}")
