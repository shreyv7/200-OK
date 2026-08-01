from __future__ import annotations

from pathlib import Path

FORBIDDEN_IMPORT_MARKERS = (
  "google.generativeai",
  "google.genai",
  "tavily",
  "boto3",
  "anthropic",
)

AIS_SCAN_ROOTS = (
  Path("app/agents"),
  Path("app/services/recommendation"),
)


def _python_files(root: Path) -> list[Path]:
  return [path for path in root.rglob("*.py") if path.is_file()]


def test_no_vendor_sdk_imports_outside_providers() -> None:
  violations: list[str] = []

  for rel_root in AIS_SCAN_ROOTS:
      for path in _python_files(rel_root):
          text = path.read_text(encoding="utf-8")
          for marker in FORBIDDEN_IMPORT_MARKERS:
              if marker in text:
                  violations.append(f"{path}: contains '{marker}'")

  assert violations == [], "Vendor SDK references found:\n" + "\n".join(violations)
