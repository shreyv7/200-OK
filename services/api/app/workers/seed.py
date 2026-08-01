"""Seed script entrypoint. Owner: Backend.

Real seeding (21-day Aarav simulated history, ledger entries, catalogs) is
M1+ scope. This stub only establishes the entrypoint contract.
"""

from __future__ import annotations

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed")


def main() -> None:
    logger.info("Seed script not yet implemented (M0 scaffold only).")


if __name__ == "__main__":
    main()
