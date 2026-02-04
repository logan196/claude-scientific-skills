"""
Loads scientific skill definitions from SKILL.md files.

Scans the scientific-skills/ directory, parses YAML frontmatter
from each SKILL.md to extract name and description, and provides
the full markdown content on demand.
"""

import os
import logging
from typing import Dict, List, Any, Optional

import yaml

logger = logging.getLogger(__name__)

SKILLS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scientific-skills")


def _parse_frontmatter(content: str) -> tuple:
    """Parse YAML frontmatter from a SKILL.md file.

    Returns (metadata_dict, body_text).
    """
    if not content.startswith("---"):
        return {}, content

    end = content.find("---", 3)
    if end == -1:
        return {}, content

    frontmatter_str = content[3:end].strip()
    body = content[end + 3:].strip()

    try:
        metadata = yaml.safe_load(frontmatter_str) or {}
    except yaml.YAMLError as exc:
        logger.warning(f"Failed to parse YAML frontmatter: {exc}")
        metadata = {}

    return metadata, body


class SkillRegistry:
    """Registry of all available scientific skills."""

    def __init__(self, skills_dir: str = SKILLS_DIR):
        self.skills_dir = skills_dir
        self._skills: Dict[str, Dict[str, Any]] = {}
        self._loaded = False

    def load(self):
        """Scan skills directory and load all SKILL.md metadata."""
        if not os.path.isdir(self.skills_dir):
            logger.error(f"Skills directory not found: {self.skills_dir}")
            self._loaded = True
            return

        for entry in sorted(os.listdir(self.skills_dir)):
            skill_path = os.path.join(self.skills_dir, entry)
            skill_md = os.path.join(skill_path, "SKILL.md")

            if not os.path.isdir(skill_path) or not os.path.isfile(skill_md):
                continue

            try:
                with open(skill_md, "r", encoding="utf-8") as f:
                    content = f.read()

                metadata, body = _parse_frontmatter(content)
                name = metadata.get("name", entry)
                description = metadata.get("description", "")

                self._skills[name] = {
                    "name": name,
                    "description": description,
                    "dir_name": entry,
                    "content": content,
                }
            except Exception as exc:
                logger.warning(f"Failed to load skill from {skill_md}: {exc}")

        self._loaded = True
        logger.info(f"Loaded {len(self._skills)} scientific skills")

    def list_tools(self) -> List[Dict[str, Any]]:
        """Return MCP-formatted tool list."""
        if not self._loaded:
            self.load()

        tools = []
        for skill in self._skills.values():
            tools.append({
                "name": skill["name"],
                "description": skill["description"],
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The scientific question or task to get guidance on",
                        }
                    },
                },
            })
        return tools

    def get_skill_content(self, name: str) -> Optional[str]:
        """Return the full SKILL.md content for a given skill name."""
        if not self._loaded:
            self.load()

        skill = self._skills.get(name)
        if skill:
            return skill["content"]
        return None

    @property
    def count(self) -> int:
        if not self._loaded:
            self.load()
        return len(self._skills)
