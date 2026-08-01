"""Prompt template loading + rendering. Owner: Backend. docs/work.md B6.

Single facade every LLM call site in the codebase should use — no call
site should read a template file or substitute placeholders itself.

Two real bugs found live while consolidating scattered prompts here:
- bottleneck_v1.py called load_prompt("identity/bottleneck_diagnosis_v1.md")
  with the extension already included, on top of this loader's own
  f"{name}.md" — always FileNotFoundError, looking for a literal
  "....md.md" file that never existed.
- Even with that fixed, bottleneck_diagnosis_v1.md's own "Output Format"
  section embeds a literal JSON example. str.format() (the previous
  rendering approach) treats every single `{`/`}` as a substitution
  field, so it crashed with KeyError on the template's own example the
  moment the first bug was out of the way.

Both were invisible in practice because the only caller wraps the whole
thing in a blanket `except Exception: return <deterministic fallback>` —
the real LLM path had never actually executed successfully even once.

Templates use {{ placeholder }} (double braces) exclusively, specifically
because every template embeds a literal JSON example — single braces in
template bodies are never touched by rendering, so a JSON example can
never collide with a real placeholder again.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

PROMPTS_DIR = Path(__file__).resolve().parent

_PLACEHOLDER = re.compile(r"\{\{\s*(\w+)\s*\}\}")

#: Shared system-role preamble for every generate_structured() call in the
#: codebase (docs/work.md B6). Each template's own opening line still
#: carries its specific persona/task framing; this is just the one
#: generic instruction that used to be retyped slightly differently
#: (and inconsistently) at every call site.
SYSTEM_PREAMBLE = (
    "You are a Trellis agent. Follow the instructions below exactly and "
    "return only valid JSON matching the provided schema — no prose "
    "outside the JSON."
)


def load_prompt(name: str) -> str:
    """Load a versioned prompt template by stem (e.g. curator_bottleneck,
    identity/bottleneck_diagnosis_v1 — no .md suffix). Raises
    FileNotFoundError if the file doesn't exist; never silently returns
    an empty or partial template."""
    path = PROMPTS_DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt template not found: {path}")
    return path.read_text(encoding="utf-8")


def render_prompt(name: str, **values: Any) -> str:
    """Loads a template and substitutes every {{ placeholder }} with a
    value from `values`. Raises KeyError naming the exact missing
    placeholder — never silently leaves one unrendered in a prompt sent
    to a model."""
    template = load_prompt(name)

    def _substitute(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in values:
            raise KeyError(
                f"render_prompt({name!r}): missing value for placeholder '{{{{ {key} }}}}'"
            )
        return str(values[key])

    return _PLACEHOLDER.sub(_substitute, template)


def build_messages(name: str, **values: Any) -> list[dict[str, str]]:
    """The single facade every LLM call site should use (docs/work.md
    B6): renders the named template and wraps it with the shared system
    preamble, producing exactly the messages list
    LLMProvider.generate_structured() expects."""
    return [
        {"role": "system", "content": SYSTEM_PREAMBLE},
        {"role": "user", "content": render_prompt(name, **values)},
    ]
