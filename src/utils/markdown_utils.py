"""
Markdown Utilities - Reusable functions for markdown file manipulation.

Provides utilities for updating and extracting sections from markdown files.
"""

import re

def update_markdown_section(content: str, section_name: str, new_content: str) -> str:
    """
    Update or add a section in markdown content.

    Args:
        content: The full markdown content
        section_name: The section header name (without ## prefix)
        new_content: The new content for the section

    Returns:
        Updated markdown content with the section modified or added
    """
    section_pattern = f"## {re.escape(section_name)}\\s*\\n([^#]*)"

    if re.search(section_pattern, content):
        # Replace existing section
        replacement = f"## {section_name}\\n{new_content}\\n\\n"
        content = re.sub(section_pattern, replacement, content)
    else:
        # Add section at the end
        content += f"\\n\\n## {section_name}\\n{new_content}\\n"

    return content


def extract_markdown_section(content: str, section_name: str) -> str:
    """
    Extract a section's content from markdown.

    Args:
        content: The full markdown content
        section_name: The section header name (without ## prefix)

    Returns:
        The section content or empty string if not found
    """
    section_pattern = f"## {re.escape(section_name)}\\s*\\n([^#]*)"
    match = re.search(section_pattern, content)

    if match:
        return match.group(1).strip()

    return ""
