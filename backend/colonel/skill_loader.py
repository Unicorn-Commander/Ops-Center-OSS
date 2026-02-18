"""
SKILL.md Parser - Converts SKILL.md files to OpenAI function-calling tool definitions.

SKILL.md Format:
```
---
name: skill-name
description: What this skill does
actions:
  - name: action_name
    description: What this action does
    confirmation_required: false
    parameters:
      param_name:
        type: string
        description: Param description
        required: true
        enum: [val1, val2]
---
Additional context or documentation below the frontmatter.
```
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

import yaml

logger = logging.getLogger("colonel.skill_loader")

SKILLS_DIR = Path(__file__).parent / "skills"


def load_skill_file(filepath: Path) -> Optional[Dict[str, Any]]:
    """Parse a single SKILL.md file."""
    try:
        content = filepath.read_text(encoding="utf-8")

        # Extract YAML frontmatter between --- markers
        if not content.startswith("---"):
            logger.warning(f"Skill file missing frontmatter: {filepath}")
            return None

        parts = content.split("---", 2)
        if len(parts) < 3:
            logger.warning(f"Skill file has incomplete frontmatter: {filepath}")
            return None

        yaml_str = parts[1].strip()
        docs = parts[2].strip()

        skill_def = yaml.safe_load(yaml_str)
        if not skill_def or not isinstance(skill_def, dict):
            logger.warning(f"Invalid YAML in skill file: {filepath}")
            return None

        skill_def["_docs"] = docs
        skill_def["_filepath"] = str(filepath)
        return skill_def

    except Exception as e:
        logger.error(f"Failed to load skill {filepath}: {e}")
        return None


def load_all_skills() -> Dict[str, Dict[str, Any]]:
    """Load all SKILL.md files from the skills directory."""
    skills = {}
    if not SKILLS_DIR.exists():
        logger.warning(f"Skills directory not found: {SKILLS_DIR}")
        return skills

    for filepath in sorted(SKILLS_DIR.glob("*.skill.md")):
        skill = load_skill_file(filepath)
        if skill and "name" in skill:
            skills[skill["name"]] = skill
            logger.info(f"Loaded skill: {skill['name']} ({len(skill.get('actions', []))} actions)")

    logger.info(f"Loaded {len(skills)} skills total")
    return skills


def skill_to_tool_definitions(skill: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Convert a skill definition to OpenAI function-calling tool definitions."""
    tools = []
    skill_name = skill.get("name", "unknown")

    for action in skill.get("actions", []):
        action_name = action.get("name", "unknown")
        func_name = f"{skill_name}__{action_name}"

        # Build JSON Schema for parameters
        properties = {}
        required = []

        for param_name, param_def in action.get("parameters", {}).items():
            prop = {
                "type": param_def.get("type", "string"),
                "description": param_def.get("description", ""),
            }
            if "enum" in param_def:
                prop["enum"] = param_def["enum"]
            if "default" in param_def:
                prop["default"] = param_def["default"]

            properties[param_name] = prop

            if param_def.get("required", False):
                required.append(param_name)

        tool = {
            "type": "function",
            "function": {
                "name": func_name,
                "description": action.get("description", ""),
                "parameters": {
                    "type": "object",
                    "properties": properties,
                },
            },
        }
        if required:
            tool["function"]["parameters"]["required"] = required

        tools.append(tool)

    return tools


def get_tool_definitions_for_skills(skills: Dict[str, Dict], enabled_skill_ids: List[str]) -> List[Dict[str, Any]]:
    """Get all tool definitions for enabled skills."""
    tools = []
    for skill_id in enabled_skill_ids:
        skill = skills.get(skill_id)
        if skill:
            tools.extend(skill_to_tool_definitions(skill))
    return tools


def get_skill_descriptions(skills: Dict[str, Dict], enabled_skill_ids: List[str]) -> str:
    """Get human-readable descriptions of enabled skills for the system prompt."""
    lines = []
    for skill_id in enabled_skill_ids:
        skill = skills.get(skill_id)
        if skill:
            lines.append(f"- **{skill.get('name')}**: {skill.get('description', '')}")
            for action in skill.get("actions", []):
                confirm = " ⚠️ (requires confirmation)" if action.get("confirmation_required") else ""
                lines.append(f"  - `{action['name']}`: {action.get('description', '')}{confirm}")
    return "\n".join(lines) if lines else "No skills loaded."


def get_confirmation_required(skills: Dict[str, Dict], func_name: str) -> bool:
    """Check if a function call requires user confirmation."""
    parts = func_name.split("__", 1)
    if len(parts) != 2:
        return False

    skill_name, action_name = parts
    skill = skills.get(skill_name)
    if not skill:
        return False

    for action in skill.get("actions", []):
        if action["name"] == action_name:
            return action.get("confirmation_required", False)

    return False
