from __future__ import annotations

from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent


def load_prompt(name: str) -> str:
  """Load a versioned prompt template by stem (e.g. curator_bottleneck)."""
  path = PROMPTS_DIR / f"{name}.md"
  if not path.exists():
      raise FileNotFoundError(f"Prompt template not found: {path}")
  return path.read_text(encoding="utf-8")
