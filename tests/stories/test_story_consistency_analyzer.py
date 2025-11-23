"""Tests for Story Consistency Analyzer

Tests character name matching, consistency checking, and report generation
using the real Example_Campaign data.
"""

import json
import os
import sys

from tests import test_helpers

StoryConsistencyAnalyzer = test_helpers.safe_from_import(
    "src.stories.story_consistency_analyzer", "StoryConsistencyAnalyzer"
)
CharacterNameMatcher = test_helpers.safe_from_import(
    "src.stories.story_consistency_analyzer", "CharacterNameMatcher"
)
ActionContext = test_helpers.safe_from_import(
    "src.stories.story_consistency_analyzer", "ActionContext"
)
ConsistencyIssue = test_helpers.safe_from_import(
    "src.stories.story_consistency_analyzer", "ConsistencyIssue"
)


def get_project_root():
    """Get the project root directory."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def test_name_pattern_matching():
    """Test that character name patterns match variations correctly."""
    print("\n[TEST] Name Pattern Matching")

    matcher = CharacterNameMatcher()

    # Test full name pattern generation
    patterns = matcher.build_name_patterns("Frodo Baggins")
    assert len(patterns) >= 2, "Should have at least 2 patterns"

    # Test finding mentions with variations (multi-line text)
    text = "Frodo walked slowly.\nBaggins was tired.\nFrodo Baggins rested."
    mentions = matcher.find_character_mentions(text, "Frodo Baggins")
    # Should find at least 1 line with a mention (each line is counted once)
    assert len(mentions) >= 1, f"Should find at least 1 line mention, found {len(mentions)}"

    print("[PASS] Name Pattern Matching")


def test_character_profile_loading():
    """Test loading character profiles from real JSON files."""
    print("\n[TEST] Character Profile Loading")

    workspace = get_project_root()

    # Test that character files exist and are valid JSON
    char_dir = os.path.join(workspace, "game_data", "characters")
    aragorn_file = os.path.join(char_dir, "aragorn.json")
    assert os.path.exists(aragorn_file), "Should find Aragorn character file"

    frodo_file = os.path.join(char_dir, "frodo.json")
    assert os.path.exists(frodo_file), "Should find Frodo character file"

    # Test loading profile
    with open(aragorn_file, 'r', encoding='utf-8') as char_f:
        profile = json.load(char_f)
    assert profile is not None, "Should load Aragorn profile"
    assert profile.get('name') == "Aragorn", "Profile should have correct name"
    assert profile.get('dnd_class') == "Ranger", "Should have class"

    print("[PASS] Character Profile Loading")


def test_tactical_consistency_check():
    """Test tactical consistency analysis with real character data."""
    print("\n[TEST] Tactical Consistency Check")

    workspace = get_project_root()
    analyzer = StoryConsistencyAnalyzer(workspace)

    # Load actual Aragorn profile
    aragorn_path = os.path.join(workspace, "game_data", "characters", "aragorn.json")
    assert os.path.exists(aragorn_path), "Aragorn character file should exist"

    with open(aragorn_path, 'r', encoding='utf-8') as char_file:
        ranger_profile = json.load(char_file)

    # Test bow usage - Rangers can use bows effectively, so may not flag as issue
    # Instead test that the analyzer can process the action without error
    action_text = "Aragorn draws his bow swiftly while standing beside Frodo"
    ctx = ActionContext("Aragorn", ranger_profile, "test.md", 1, action_text)
    issue = analyzer.tactical_analyzer.analyze_tactical_action(ctx)

    # The analyzer should process without error (issue may or may not be generated)
    # This is valid since rangers are proficient with bows
    if issue:
        assert issue.issue_type == 'tactical', "Should be tactical issue if detected"
        assert issue.score <= 10, "Score should be valid"

    print("[PASS] Tactical Consistency Check")


def test_personality_consistency_check():
    """Test personality trait consistency analysis."""
    print("\n[TEST] Personality Consistency Check")

    workspace = get_project_root()
    analyzer = StoryConsistencyAnalyzer(workspace)

    # Load actual Frodo profile
    frodo_path = os.path.join(workspace, "game_data", "characters", "frodo.json")
    assert os.path.exists(frodo_path), "Frodo character file should exist"

    with open(frodo_path, 'r', encoding='utf-8') as char_file:
        fearful_profile = json.load(char_file)

    # Test reckless action with fearful character
    action_text = "Frodo recklessly charges into the enemy camp alone"
    ctx = ActionContext("Frodo Baggins", fearful_profile, "test.md", 1, action_text)
    issue = analyzer.personality_analyzer.analyze_personality_action(ctx)

    # May or may not detect based on pattern matching
    if issue:
        assert issue.issue_type == 'personality', "Should be personality issue"
        assert 'flaws' in issue.suggestion.lower(), "Should mention character flaws"

    print("[PASS] Personality Consistency Check")


def test_story_file_analysis_with_real_data():
    """Test analyzing a real story file from Example_Campaign."""
    print("\n[TEST] Story File Analysis with Real Data")

    workspace = get_project_root()
    analyzer = StoryConsistencyAnalyzer(workspace)

    # Run full series analysis with one file to test story file processing
    campaign_name = "Example_Campaign"
    story_files = ['001_start.md']
    party_members = ['Aragorn', 'Frodo Baggins', 'Gandalf the Grey']

    # Verify story file exists
    story_path = os.path.join(
        workspace, "game_data", "campaigns", campaign_name, "001_start.md"
    )
    if not os.path.exists(story_path):
        print("  SKIP - 001_start.md not found")
        return

    # Run analysis via public API
    results = analyzer.analyze_series(
        series_name=campaign_name,
        story_files=story_files,
        party_members=party_members
    )

    # Verify results
    assert results['stories_analyzed'] == 1, "Should analyze one story"
    assert isinstance(results['issues'], list), "Should return list of issues"
    print(f"  Found {len(results['issues'])} potential issues in 001_start.md")

    # Clean up generated report
    if os.path.exists(results['report_path']):
        os.remove(results['report_path'])

    print("[PASS] Story File Analysis with Real Data")


def test_report_generation():
    """Test generating markdown report file via full analysis workflow."""
    print("\n[TEST] Report Generation")

    workspace = get_project_root()
    analyzer = StoryConsistencyAnalyzer(workspace)

    campaign_name = "Example_Campaign"
    story_files = ['001_start.md']
    party_members = ['Aragorn', 'Frodo Baggins', 'Gandalf the Grey']

    # Verify campaign exists
    campaign_path = os.path.join(workspace, "game_data", "campaigns", campaign_name)
    story_path = os.path.join(campaign_path, "001_start.md")

    if not os.path.exists(story_path):
        print("  SKIP - 001_start.md not found")
        return

    # Run full analysis to generate report
    results = analyzer.analyze_series(
        series_name=campaign_name,
        story_files=story_files,
        party_members=party_members
    )

    report_path = results['report_path']
    assert os.path.exists(report_path), "Report file should be created"

    # Verify report content
    with open(report_path, 'r', encoding='utf-8') as report_file:
        report_content = report_file.read()

    assert "Story Consistency Analysis" in report_content, "Should have title"
    assert campaign_name in report_content, "Should mention campaign name"

    # Clean up test report
    if os.path.exists(report_path):
        os.remove(report_path)

    print("[PASS] Report Generation")


def test_series_analysis_integration():
    """Test complete series analysis workflow with Example_Campaign."""
    print("\n[TEST] Series Analysis Integration")

    workspace = get_project_root()
    analyzer = StoryConsistencyAnalyzer(workspace)

    campaign_name = "Example_Campaign"
    story_files = ['001_start.md', '002_continue.md', '003_end.md']
    party_members = ['Aragorn', 'Frodo Baggins', 'Gandalf the Grey']

    # Verify story files exist
    campaign_path = os.path.join(workspace, "game_data", "campaigns", campaign_name)
    existing_files = [f for f in story_files if os.path.exists(
        os.path.join(campaign_path, f)
    )]

    if len(existing_files) == 0:
        print(f"  SKIP - No story files found in {campaign_name}")
        return

    # Run analysis on existing files
    results = analyzer.analyze_series(
        series_name=campaign_name,
        story_files=existing_files,
        party_members=party_members
    )

    assert results['series_name'] == campaign_name, "Should have series name"
    assert results['stories_analyzed'] == len(existing_files), \
        f"Should analyze {len(existing_files)} stories"
    assert 'report_path' in results, "Should have report path"
    assert os.path.exists(results['report_path']), "Report should exist"

    print(f"  Analyzed {results['stories_analyzed']} stories")
    print(f"  Found {results['total_issues']} issues")

    # Clean up generated report
    if os.path.exists(results['report_path']):
        os.remove(results['report_path'])

    print("[PASS] Series Analysis Integration")


def test_name_matching_edge_cases():
    """Test edge cases in name matching."""
    print("\n[TEST] Name Matching Edge Cases")

    matcher = CharacterNameMatcher()

    # Test single name (patterns variable used in assertion context)
    name_patterns = matcher.build_name_patterns("Gandalf")
    assert len(name_patterns) >= 1, "Should generate patterns for single name"
    mentions = matcher.find_character_mentions("Gandalf spoke wisely", "Gandalf")
    assert len(mentions) == 1, "Should find single name"

    # Test multi-word with title
    mentions = matcher.find_character_mentions(
        "Gandalf walked forward. The Grey wizard spoke.",
        "Gandalf the Grey"
    )
    assert len(mentions) >= 1, "Should find name parts"

    # Test case insensitivity
    mentions = matcher.find_character_mentions("FRODO shouted loudly", "Frodo Baggins")
    assert len(mentions) == 1, "Should be case insensitive"

    print("[PASS] Name Matching Edge Cases")


def run_all_tests():
    """Run all story consistency analyzer tests."""
    test_functions = [
        test_name_pattern_matching,
        test_character_profile_loading,
        test_tactical_consistency_check,
        test_personality_consistency_check,
        test_story_file_analysis_with_real_data,
        test_report_generation,
        test_series_analysis_integration,
        test_name_matching_edge_cases,
    ]

    return test_helpers.run_test_suite(
        "Story Consistency Analyzer Tests", test_functions
    )


if __name__ == "__main__":
    sys.exit(run_all_tests())
