"""Story template and snippet management.

Provides a template library for common D&D story scenarios and
utilities for applying templates to new story files.
"""

import os
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

_PLACEHOLDER_RE = re.compile(r"\{(\w+)\}")

# Built-in template content
_BUILTIN_TEMPLATES: dict[str, tuple[str, str, str]] = {
    "combat": (
        "Combat Encounter",
        "## Combat Scene\n\n"
        "The party faces {enemy_description}.\n\n"
        "{combat_narrative}\n\n"
        "## Aftermath\n\n"
        "{aftermath_narrative}\n",
        "combat",
    ),
    "social": (
        "Social Encounter",
        "## Social Scene\n\n"
        "The party meets {npc_name} at {location}.\n\n"
        "{dialogue_and_events}\n\n"
        "## Outcome\n\n"
        "{outcome_description}\n",
        "social",
    ),
    "exploration": (
        "Exploration Scene",
        "## Exploration\n\n"
        "The party ventures into {location_description}.\n\n"
        "{exploration_narrative}\n\n"
        "## Discovery\n\n"
        "{discovery_description}\n",
        "exploration",
    ),
    "dungeon": (
        "Dungeon Delve",
        "## Dungeon Entrance\n\n"
        "The party stands before {dungeon_name}.\n\n"
        "{entry_narrative}\n\n"
        "## Deeper In\n\n"
        "{interior_narrative}\n\n"
        "## The Heart\n\n"
        "{climax_narrative}\n",
        "dungeon",
    ),
    "urban": (
        "Urban Scene",
        "## {city_name}\n\n"
        "The city of {city_name} bustles around the party.\n\n"
        "{urban_narrative}\n\n"
        "## Encounters\n\n"
        "{encounter_description}\n",
        "urban",
    ),
    "travel": (
        "Travel Scene",
        "## On the Road\n\n"
        "The party travels from {origin} to {destination}.\n\n"
        "{travel_narrative}\n\n"
        "## Along the Way\n\n"
        "{encounter_description}\n",
        "travel",
    ),
}

# Built-in snippet content keyed by (category, name)
_BUILTIN_SNIPPETS: dict[tuple[str, str], str] = {
    ("combat", "ambush"): (
        "Without warning, {ambusher} strikes from the shadows!\n"
        "Initiative is rolled as the chaos of battle erupts.\n"
    ),
    ("combat", "boss_intro"): (
        "A shadow falls across the chamber. {boss_name} rises, a terrible\n"
        "presence filling the room with dread and anticipation.\n"
    ),
    ("social", "tavern_scene"): (
        "The Prancing Pony buzzes with chatter. Candles flicker on rough-hewn tables\n"
        "as travelers swap tales of the road.\n"
    ),
    ("social", "negotiation"): (
        "{npc_name} leans forward, fingers laced. 'I have a proposition for you.'\n"
        "Their eyes hold a calculating gleam.\n"
    ),
    ("exploration", "discovery"): (
        "Beneath a thick layer of dust lies {artifact_description}.\n"
        "The air itself seems to hold its breath.\n"
    ),
    ("exploration", "travel"): (
        "The road stretches ahead, {weather_description}. "
        "Miles pass in comfortable silence.\n"
    ),
}


class TemplateCategory(Enum):
    """Categories of story templates."""

    COMBAT = "combat"
    SOCIAL = "social"
    EXPLORATION = "exploration"
    DUNGEON = "dungeon"
    URBAN = "urban"
    WILDERNESS = "wilderness"
    BOSS_FIGHT = "boss_fight"
    PUZZLE = "puzzle"
    ROLEPLAY = "roleplay"
    TRAVEL = "travel"


@dataclass
class StorySnippet:
    """A reusable story snippet."""

    name: str
    category: TemplateCategory
    content: str
    placeholders: list[str] = field(default_factory=list)
    description: str = ""
    tags: list[str] = field(default_factory=list)


@dataclass
class StoryTemplate:
    """A complete story template."""

    name: str
    category: TemplateCategory
    content: str
    placeholders: dict[str, str] = field(default_factory=dict)
    description: str = ""
    snippets: list[StorySnippet] = field(default_factory=list)


@dataclass
class TemplateLibrary:
    """Collection of available templates and snippets."""

    templates: dict[str, StoryTemplate] = field(default_factory=dict)
    snippets: dict[str, StorySnippet] = field(default_factory=dict)

    def get_templates_by_category(
        self,
        category: TemplateCategory,
    ) -> list[StoryTemplate]:
        """Get all templates in a category.

        Args:
            category: TemplateCategory to filter by.

        Returns:
            List of matching StoryTemplate objects.
        """
        return [t for t in self.templates.values() if t.category == category]

    def get_snippets_by_category(
        self,
        category: TemplateCategory,
    ) -> list[StorySnippet]:
        """Get all snippets in a category.

        Args:
            category: TemplateCategory to filter by.

        Returns:
            List of matching StorySnippet objects.
        """
        return [s for s in self.snippets.values() if s.category == category]


class TemplateManager:
    """Manage story templates and snippets."""

    _CUSTOM_TEMPLATES_DIR = "templates/story"
    _CUSTOM_SNIPPETS_DIR = "templates/story/snippets"

    def __init__(self, workspace_path: str) -> None:
        """Initialize template manager.

        Args:
            workspace_path: Root workspace path.
        """
        self.workspace_path = workspace_path
        self.library = TemplateLibrary()
        self._load_builtin_templates()
        self._load_builtin_snippets()
        self._load_custom_templates()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_template(self, template_name: str) -> Optional[StoryTemplate]:
        """Get a template by name.

        Args:
            template_name: Name of template.

        Returns:
            StoryTemplate if found, None otherwise.
        """
        return self.library.templates.get(template_name)

    def apply_template(
        self,
        template_name: str,
        values: dict[str, str],
    ) -> str:
        """Apply placeholder values to a template.

        Args:
            template_name: Name of template.
            values: Dictionary of placeholder name to replacement value.

        Returns:
            Template content with placeholders filled.

        Raises:
            KeyError: If the template name is not found.
        """
        template = self.library.templates.get(template_name)
        if template is None:
            raise KeyError(f"Template '{template_name}' not found.")
        return self._fill_placeholders(template.content, values)

    def get_snippet(self, snippet_name: str) -> Optional[StorySnippet]:
        """Get a snippet by name.

        Args:
            snippet_name: Name of snippet.

        Returns:
            StorySnippet if found, None otherwise.
        """
        return self.library.snippets.get(snippet_name)

    def insert_snippet(
        self,
        content: str,
        snippet_name: str,
        position: int,
        values: Optional[dict[str, str]] = None,
    ) -> str:
        """Insert a snippet into existing content at a character position.

        Args:
            content: Existing content.
            snippet_name: Name of snippet to insert.
            position: Character position to insert at.
            values: Optional placeholder values.

        Returns:
            Content with snippet inserted.

        Raises:
            KeyError: If the snippet name is not found.
        """
        snippet = self.library.snippets.get(snippet_name)
        if snippet is None:
            raise KeyError(f"Snippet '{snippet_name}' not found.")
        snippet_content = self._fill_placeholders(snippet.content, values or {})
        return content[:position] + snippet_content + content[position:]

    def create_custom_template(
        self,
        name: str,
        category: TemplateCategory,
        content: str,
        description: str = "",
    ) -> StoryTemplate:
        """Create a custom template and add it to the library.

        Args:
            name: Template name (used as the library key).
            category: Template category.
            content: Template content with optional {placeholder} markers.
            description: Human-readable description.

        Returns:
            Created StoryTemplate.
        """
        placeholders = {p: "" for p in _PLACEHOLDER_RE.findall(content)}
        template = StoryTemplate(
            name=name,
            category=category,
            content=content,
            placeholders=placeholders,
            description=description,
        )
        self.library.templates[name] = template
        return template

    def save_custom_template(self, template: StoryTemplate) -> str:
        """Save a custom template to the workspace templates directory.

        Args:
            template: Template to save.

        Returns:
            Path to saved template file.
        """
        templates_dir = os.path.join(
            self.workspace_path, self._CUSTOM_TEMPLATES_DIR
        )
        os.makedirs(templates_dir, exist_ok=True)
        filename = re.sub(r"[^a-zA-Z0-9_-]", "_", template.name.lower()) + ".md"
        filepath = os.path.join(templates_dir, filename)
        with open(filepath, "w", encoding="utf-8") as fh:
            if template.description:
                fh.write(f"<!-- {template.description} -->\n")
            fh.write(template.content)
        return filepath

    def list_templates(
        self,
        category: Optional[TemplateCategory] = None,
    ) -> list[StoryTemplate]:
        """List available templates, optionally filtered by category.

        Args:
            category: Optional category filter.

        Returns:
            List of matching StoryTemplate objects.
        """
        if category is None:
            return list(self.library.templates.values())
        return self.library.get_templates_by_category(category)

    def list_snippets(
        self,
        category: Optional[TemplateCategory] = None,
    ) -> list[StorySnippet]:
        """List available snippets, optionally filtered by category.

        Args:
            category: Optional category filter.

        Returns:
            List of matching StorySnippet objects.
        """
        if category is None:
            return list(self.library.snippets.values())
        return self.library.get_snippets_by_category(category)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_builtin_templates(self) -> None:
        """Populate the library with built-in templates."""
        for key, (display_name, content, cat_str) in _BUILTIN_TEMPLATES.items():
            category = self._category_from_str(cat_str)
            placeholders = {p: "" for p in _PLACEHOLDER_RE.findall(content)}
            self.library.templates[key] = StoryTemplate(
                name=display_name,
                category=category,
                content=content,
                placeholders=placeholders,
            )

    def _load_builtin_snippets(self) -> None:
        """Populate the library with built-in snippets."""
        for (cat_str, snippet_name), content in _BUILTIN_SNIPPETS.items():
            category = self._category_from_str(cat_str)
            placeholders = _PLACEHOLDER_RE.findall(content)
            key = f"{cat_str}/{snippet_name}"
            self.library.snippets[key] = StorySnippet(
                name=snippet_name,
                category=category,
                content=content,
                placeholders=placeholders,
            )

    def _load_custom_templates(self) -> None:
        """Load custom templates from the workspace templates directory."""
        templates_dir = os.path.join(
            self.workspace_path, self._CUSTOM_TEMPLATES_DIR
        )
        if not os.path.isdir(templates_dir):
            return

        for filename in sorted(os.listdir(templates_dir)):
            if not filename.endswith(".md"):
                continue
            filepath = os.path.join(templates_dir, filename)
            try:
                with open(filepath, encoding="utf-8") as fh:
                    content = fh.read()
            except OSError:
                continue

            name = os.path.splitext(filename)[0]
            description = ""
            comment_match = re.match(r"<!--\s*(.+?)\s*-->", content)
            if comment_match:
                description = comment_match.group(1)
                content = content[comment_match.end():].lstrip()

            category = TemplateCategory.EXPLORATION
            for cat in TemplateCategory:
                if cat.value in name.lower():
                    category = cat
                    break

            placeholders = {p: "" for p in _PLACEHOLDER_RE.findall(content)}
            self.library.templates[name] = StoryTemplate(
                name=name,
                category=category,
                content=content,
                placeholders=placeholders,
                description=description,
            )

    def _fill_placeholders(
        self,
        content: str,
        values: dict[str, str],
    ) -> str:
        """Replace {placeholder} markers in content with provided values.

        Args:
            content: Template content.
            values: Mapping of placeholder names to replacement strings.

        Returns:
            Content with all matched placeholders replaced.
        """
        def replace(match: re.Match[str]) -> str:
            key = match.group(1)
            return values.get(key, match.group(0))

        return _PLACEHOLDER_RE.sub(replace, content)

    def _category_from_str(self, cat_str: str) -> TemplateCategory:
        """Convert a category string to a TemplateCategory enum value.

        Args:
            cat_str: Category string (e.g. 'combat', 'social').

        Returns:
            Matching TemplateCategory, defaulting to EXPLORATION.
        """
        for cat in TemplateCategory:
            if cat.value == cat_str:
                return cat
        return TemplateCategory.EXPLORATION
