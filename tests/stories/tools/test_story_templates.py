"""Tests for src/stories/tools/story_templates.py.

Uses temporary workspaces to test custom template loading and saving.
"""

import os
import tempfile

from src.stories.tools.story_templates import (
    TemplateCategory,
    TemplateManager,
)


def test_builtin_templates_loaded():
    """TemplateManager should load at least one built-in template on init."""
    with tempfile.TemporaryDirectory() as tmp:
        manager = TemplateManager(tmp)
        templates = manager.list_templates()
        assert len(templates) > 0


def test_builtin_snippets_loaded():
    """TemplateManager should load at least one built-in snippet on init."""
    with tempfile.TemporaryDirectory() as tmp:
        manager = TemplateManager(tmp)
        snippets = manager.list_snippets()
        assert len(snippets) > 0


def test_get_template_returns_named_template():
    """get_template should return the template for a known built-in name."""
    with tempfile.TemporaryDirectory() as tmp:
        manager = TemplateManager(tmp)
        template = manager.get_template("combat")
        assert template is not None
        assert template.name == "Combat Encounter"


def test_get_template_returns_none_for_unknown():
    """get_template should return None for an unrecognised template name."""
    with tempfile.TemporaryDirectory() as tmp:
        manager = TemplateManager(tmp)
        result = manager.get_template("nonexistent_template")
        assert result is None


def test_apply_template_fills_placeholders():
    """apply_template should replace {placeholder} markers with provided values."""
    with tempfile.TemporaryDirectory() as tmp:
        manager = TemplateManager(tmp)
        result = manager.apply_template(
            "travel",
            {"origin": "Rivendell", "destination": "Mordor"},
        )
        assert "Rivendell" in result
        assert "Mordor" in result


def test_apply_template_leaves_unfilled_placeholders():
    """Unfilled placeholders should remain in the output."""
    with tempfile.TemporaryDirectory() as tmp:
        manager = TemplateManager(tmp)
        result = manager.apply_template("combat", {})
        assert "{enemy_description}" in result


def test_apply_template_raises_for_unknown_name():
    """apply_template should raise KeyError for an unknown template name."""
    with tempfile.TemporaryDirectory() as tmp:
        manager = TemplateManager(tmp)
        try:
            manager.apply_template("does_not_exist", {})
            assert False, "Expected KeyError"
        except KeyError:
            pass


def test_get_snippet_returns_known_snippet():
    """get_snippet should return a snippet for a known built-in key."""
    with tempfile.TemporaryDirectory() as tmp:
        manager = TemplateManager(tmp)
        snippet = manager.get_snippet("combat/ambush")
        assert snippet is not None
        assert snippet.name == "ambush"


def test_insert_snippet_injects_at_position():
    """insert_snippet should insert snippet content at the given character position."""
    with tempfile.TemporaryDirectory() as tmp:
        manager = TemplateManager(tmp)
        base = "Start. End."
        result = manager.insert_snippet(base, "combat/ambush", 7)
        assert result.startswith("Start. ")
        assert "End." in result
        assert len(result) > len(base)


def test_insert_snippet_raises_for_unknown_name():
    """insert_snippet should raise KeyError for an unknown snippet name."""
    with tempfile.TemporaryDirectory() as tmp:
        manager = TemplateManager(tmp)
        try:
            manager.insert_snippet("Content.", "unknown/snippet", 0)
            assert False, "Expected KeyError"
        except KeyError:
            pass


def test_create_custom_template_added_to_library():
    """create_custom_template should add the new template to the library."""
    with tempfile.TemporaryDirectory() as tmp:
        manager = TemplateManager(tmp)
        manager.create_custom_template(
            "my_template",
            TemplateCategory.PUZZLE,
            "A puzzle appeared: {puzzle_description}.",
        )
        result = manager.get_template("my_template")
        assert result is not None
        assert result.category == TemplateCategory.PUZZLE


def test_save_custom_template_writes_file():
    """save_custom_template should write a .md file to the templates directory."""
    with tempfile.TemporaryDirectory() as tmp:
        manager = TemplateManager(tmp)
        template = manager.create_custom_template(
            "saved_template",
            TemplateCategory.ROLEPLAY,
            "{character} speaks: {dialogue}.",
            description="A roleplay template",
        )
        path = manager.save_custom_template(template)
        assert os.path.isfile(path)
        with open(path, encoding="utf-8") as fh:
            content = fh.read()
        assert "{character}" in content


def test_custom_template_loaded_from_disk():
    """Templates saved to disk should be loaded on next TemplateManager init."""
    with tempfile.TemporaryDirectory() as tmp:
        manager1 = TemplateManager(tmp)
        template = manager1.create_custom_template(
            "persisted_template",
            TemplateCategory.URBAN,
            "The city of {city} never sleeps.",
        )
        manager1.save_custom_template(template)

        manager2 = TemplateManager(tmp)
        loaded = manager2.get_template("persisted_template")
        assert loaded is not None
        assert "{city}" in loaded.content


def test_list_templates_filter_by_category():
    """list_templates with a category filter should return only matching templates."""
    with tempfile.TemporaryDirectory() as tmp:
        manager = TemplateManager(tmp)
        combat_templates = manager.list_templates(TemplateCategory.COMBAT)
        assert all(t.category == TemplateCategory.COMBAT for t in combat_templates)


def test_list_snippets_filter_by_category():
    """list_snippets with a category filter should return only matching snippets."""
    with tempfile.TemporaryDirectory() as tmp:
        manager = TemplateManager(tmp)
        social_snippets = manager.list_snippets(TemplateCategory.SOCIAL)
        assert all(s.category == TemplateCategory.SOCIAL for s in social_snippets)
