"""CLI commands for story tools.

Provides command-line interface for story tools functionality including
search, statistics, comparison, validation, import, export, and templates.
"""

import argparse
import os
import sys
from typing import Optional

from src.stories.tools.story_export_helpers import StoryExportFormat, StoryExportOptions
from src.stories.tools.story_import_helpers import ImportOptions
from src.stories.tools.story_search import SearchScope, SearchType
from src.stories.tools.story_tools import StoryTools
from src.utils.terminal_display import print_error, print_info, print_success


def create_story_tools_parser() -> argparse.ArgumentParser:
    """Create argument parser for story tools commands.

    Returns:
        Configured ArgumentParser with all story-tool subcommands.
    """
    parser = argparse.ArgumentParser(
        prog="story",
        description="Story tools for the D&D Character Consultant",
    )
    subparsers = parser.add_subparsers(dest="command", help="Story tool commands")

    # -- diff --
    diff_parser = subparsers.add_parser("diff", help="Compare two story files")
    diff_parser.add_argument("source", help="Source story file path")
    diff_parser.add_argument("target", help="Target story file path")
    diff_parser.add_argument("--output", help="Write diff report to this file")
    diff_parser.add_argument(
        "--format",
        choices=["markdown", "text"],
        default="markdown",
        dest="output_format",
        help="Report output format",
    )

    # -- search --
    search_parser = subparsers.add_parser("search", help="Search stories for content")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument(
        "--type",
        choices=["text", "character", "location", "regex"],
        default="text",
        dest="search_type",
    )
    search_parser.add_argument(
        "--scope",
        choices=["current", "series", "all"],
        default="series",
    )
    search_parser.add_argument("--campaign", help="Campaign name for series scope")

    # -- stats --
    stats_parser = subparsers.add_parser("stats", help="Show story statistics")
    stats_parser.add_argument("story", help="Story file path")
    stats_parser.add_argument(
        "--characters",
        nargs="*",
        help="Character names to track",
    )

    # -- stats-series --
    series_stats_parser = subparsers.add_parser(
        "stats-series", help="Show series-level statistics"
    )
    series_stats_parser.add_argument("series", help="Series (campaign) name")
    series_stats_parser.add_argument(
        "--characters",
        nargs="*",
        help="Character names to track",
    )

    # -- export --
    export_parser = subparsers.add_parser("export", help="Export a story")
    export_parser.add_argument("story", help="Story file path")
    export_parser.add_argument(
        "export_format",
        choices=["html", "md", "txt"],
        help="Export format",
    )
    export_parser.add_argument("--output", help="Output file path")

    # -- export-series --
    export_series_parser = subparsers.add_parser(
        "export-series", help="Export an entire series"
    )
    export_series_parser.add_argument("series", help="Series (campaign) name")
    export_series_parser.add_argument(
        "export_format",
        choices=["html", "md", "txt"],
        help="Export format",
    )
    export_series_parser.add_argument("--output", required=True, help="Output path")
    export_series_parser.add_argument(
        "--no-combine",
        action="store_true",
        help="Export each story to a separate file",
    )

    # -- bundle --
    bundle_parser = subparsers.add_parser(
        "bundle", help="Create a campaign zip bundle"
    )
    bundle_parser.add_argument("campaign", help="Campaign name")
    bundle_parser.add_argument("--output", required=True, help="Output zip file path")
    bundle_parser.add_argument(
        "--no-characters",
        action="store_true",
        help="Exclude character files",
    )
    bundle_parser.add_argument(
        "--no-npcs",
        action="store_true",
        help="Exclude NPC files",
    )

    # -- import --
    import_parser = subparsers.add_parser("import", help="Import a story from file")
    import_parser.add_argument("file", help="Source file to import")
    import_parser.add_argument("--series", help="Target series name")

    # -- template --
    template_parser = subparsers.add_parser("template", help="Template operations")
    template_parser.add_argument(
        "action",
        choices=["list", "apply"],
        help="Template action",
    )
    template_parser.add_argument("--name", help="Template name (required for apply)")
    template_parser.add_argument("--output", help="Output file for apply action")

    # -- validate --
    validate_parser = subparsers.add_parser("validate", help="Validate a story file")
    validate_parser.add_argument("story", help="Story file path")
    validate_parser.add_argument(
        "--strict",
        action="store_true",
        help="Enable strict validation (includes style checks)",
    )
    validate_parser.add_argument(
        "--format",
        choices=["markdown", "text"],
        default="markdown",
        dest="output_format",
    )

    return parser


def handle_story_tools_command(
    args: argparse.Namespace,
    workspace_path: str,
) -> int:
    """Route a parsed command to the appropriate story tool handler.

    Args:
        args: Parsed command-line arguments.
        workspace_path: Root workspace path.

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    campaign = getattr(args, "campaign", None)
    tools = StoryTools(workspace_path, campaign_name=campaign)

    handlers = {
        "diff": _handle_diff,
        "search": _handle_search,
        "stats": _handle_stats,
        "stats-series": _handle_stats_series,
        "export": _handle_export,
        "export-series": _handle_export_series,
        "bundle": _handle_bundle,
        "import": _handle_import,
        "template": _handle_template,
        "validate": _handle_validate,
    }

    handler = handlers.get(args.command)
    if handler is None:
        print_error("Unknown story tools command. Use --help for usage.")
        return 1
    return handler(args, tools)


# ------------------------------------------------------------------
# Individual command handlers
# ------------------------------------------------------------------


def _handle_diff(args: argparse.Namespace, tools: StoryTools) -> int:
    """Handle the diff command.

    Args:
        args: Parsed arguments.
        tools: StoryTools facade.

    Returns:
        Exit code.
    """
    diff = tools.diff(args.source, args.target)
    report = tools.comparator.generate_change_report(diff, args.output_format)
    if args.output:
        _write_output(args.output, report)
        print_success(f"Diff report written to {args.output}")
    else:
        print(report)
    return 0


def _handle_search(args: argparse.Namespace, tools: StoryTools) -> int:
    """Handle the search command.

    Args:
        args: Parsed arguments.
        tools: StoryTools facade.

    Returns:
        Exit code.
    """
    type_map = {
        "text": SearchType.TEXT,
        "character": SearchType.CHARACTER,
        "location": SearchType.LOCATION,
        "regex": SearchType.REGEX,
    }
    scope_map = {
        "current": SearchScope.CURRENT_STORY,
        "series": SearchScope.CURRENT_SERIES,
        "all": SearchScope.ALL_CAMPAIGNS,
    }
    campaign = getattr(args, "campaign", None)
    search_tools = tools.searcher
    if campaign:
        search_tools.campaign_name = campaign

    search_type = type_map.get(args.search_type, SearchType.TEXT)
    scope = scope_map.get(args.scope, SearchScope.CURRENT_SERIES)
    results = search_tools.search(args.query, search_type, scope)

    print_info(
        f"Found {results.total_matches} matches in {results.files_searched} files."
    )
    grouped = results.group_by_file()
    for filepath, file_results in sorted(grouped.items()):
        print(f"\n{os.path.basename(filepath)}:")
        for res in file_results:
            print(f"  Line {res.line_number}: {res.line_content[:120]}")
    return 0


def _handle_stats(args: argparse.Namespace, tools: StoryTools) -> int:
    """Handle the stats command.

    Args:
        args: Parsed arguments.
        tools: StoryTools facade.

    Returns:
        Exit code.
    """
    character_names: Optional[list[str]] = getattr(args, "characters", None)
    metrics = tools.story_stats(args.story, character_names)
    report = tools.statistics.generate_statistics_report(metrics)
    print(report)
    return 0


def _handle_stats_series(args: argparse.Namespace, tools: StoryTools) -> int:
    """Handle the stats-series command.

    Args:
        args: Parsed arguments.
        tools: StoryTools facade.

    Returns:
        Exit code.
    """
    character_names: Optional[list[str]] = getattr(args, "characters", None)
    series_metrics = tools.series_stats(args.series, character_names)
    summary = series_metrics.summary
    print(f"Series: {series_metrics.series_name}")
    print(f"  Stories: {summary.total_stories}")
    print(f"  Total words: {summary.total_word_count:,}")
    print(f"  Reading time: {summary.total_reading_time_minutes:.1f} min")
    print(f"  Average length: {summary.average_story_length:.0f} words")
    if series_metrics.character_appearances:
        print("  Character appearances:")
        for name, count in sorted(
            series_metrics.character_appearances.items(),
            key=lambda x: x[1],
            reverse=True,
        ):
            print(f"    {name}: {count}")
    return 0


def _handle_export(args: argparse.Namespace, tools: StoryTools) -> int:
    """Handle the export command.

    Args:
        args: Parsed arguments.
        tools: StoryTools facade.

    Returns:
        Exit code.
    """
    format_map = {
        "html": StoryExportFormat.HTML,
        "md": StoryExportFormat.MARKDOWN,
        "txt": StoryExportFormat.PLAIN_TEXT,
    }
    export_format = format_map.get(args.export_format, StoryExportFormat.PLAIN_TEXT)
    output = args.output or os.path.splitext(args.story)[0] + f".{args.export_format}"
    options = StoryExportOptions(export_format=export_format)
    result_path = tools.export_story(args.story, output, options)
    print_success(f"Exported to {result_path}")
    return 0


def _handle_export_series(args: argparse.Namespace, tools: StoryTools) -> int:
    """Handle the export-series command.

    Args:
        args: Parsed arguments.
        tools: StoryTools facade.

    Returns:
        Exit code.
    """
    from src.stories.tools.story_export_helpers import SeriesExportOptions  # pylint: disable=import-outside-toplevel

    format_map = {
        "html": StoryExportFormat.HTML,
        "md": StoryExportFormat.MARKDOWN,
        "txt": StoryExportFormat.PLAIN_TEXT,
    }
    export_format = format_map.get(args.export_format, StoryExportFormat.PLAIN_TEXT)
    story_opts = StoryExportOptions(export_format=export_format)
    series_opts = SeriesExportOptions(
        export_format=export_format,
        combine_stories=not args.no_combine,
        story_options=story_opts,
    )
    result_path = tools.export_series(args.series, args.output, series_opts)
    print_success(f"Series exported to {result_path}")
    return 0


def _handle_bundle(args: argparse.Namespace, tools: StoryTools) -> int:
    """Handle the bundle command.

    Args:
        args: Parsed arguments.
        tools: StoryTools facade.

    Returns:
        Exit code.
    """
    result_path = tools.exporter.export_campaign_bundle(
        args.campaign,
        args.output,
        include_characters=not args.no_characters,
        include_npcs=not args.no_npcs,
    )
    print_success(f"Bundle created at {result_path}")
    return 0


def _handle_import(args: argparse.Namespace, tools: StoryTools) -> int:
    """Handle the import command.

    Args:
        args: Parsed arguments.
        tools: StoryTools facade.

    Returns:
        Exit code.
    """
    series: Optional[str] = getattr(args, "series", None)
    options = ImportOptions(target_series=series)
    result = tools.import_story(args.file, series, options)
    if result.success:
        print_success(f"Story imported to {result.story_path}")
        if result.locations_detected:
            print_info(f"Locations detected: {', '.join(result.locations_detected)}")
        return 0
    for error in result.errors:
        print_error(error)
    return 1


def _handle_template(args: argparse.Namespace, tools: StoryTools) -> int:
    """Handle the template command.

    Args:
        args: Parsed arguments.
        tools: StoryTools facade.

    Returns:
        Exit code.
    """
    if args.action == "list":
        templates = tools.list_templates()
        if not templates:
            print_info("No templates available.")
            return 0
        for tmpl in sorted(templates, key=lambda t: t.name):
            desc = f" - {tmpl.description}" if tmpl.description else ""
            print(f"  {tmpl.name} [{tmpl.category.value}]{desc}")
        return 0

    if args.action == "apply":
        if not args.name:
            print_error("--name is required for the apply action.")
            return 1
        content = tools.apply_template(args.name, {})
        if args.output:
            _write_output(args.output, content)
            print_success(f"Template applied and written to {args.output}")
        else:
            print(content)
        return 0

    print_error(f"Unknown template action: {args.action}")
    return 1


def _handle_validate(args: argparse.Namespace, tools: StoryTools) -> int:
    """Handle the validate command.

    Args:
        args: Parsed arguments.
        tools: StoryTools facade.

    Returns:
        Exit code (0 if valid, 1 if errors found).
    """
    result = tools.validate(args.story, args.strict)
    report = tools.validator.generate_validation_report(result, args.output_format)
    print(report)
    return 0 if result.is_valid else 1


def _write_output(output_path: str, content: str) -> None:
    """Write content to an output file.

    Args:
        output_path: Destination file path.
        content: Content to write.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(content)


def main(argv: Optional[list[str]] = None) -> int:
    """Entry point for the story tools CLI.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:]).

    Returns:
        Exit code.
    """
    parser = create_story_tools_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    workspace_path = os.getcwd()
    return handle_story_tools_command(args, workspace_path)


if __name__ == "__main__":
    sys.exit(main())
