"""Deterministic seed. From repo root: python scripts/seed.py --reset"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.core.config import get_settings  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import make_engine, make_session_factory  # noqa: E402
from app.models import Department, Employee, FxRate, SalaryRecord  # noqa: E402, F401
from app.services.seed import DEFAULT_COUNT, seed, verify_counts  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed ACME salary data")
    parser.add_argument("--reset", action="store_true", help="Wipe existing rows first")
    parser.add_argument("--count", type=int, default=DEFAULT_COUNT)
    parser.add_argument("--database-url", default=None)
    args = parser.parse_args()

    settings = get_settings()
    url = args.database_url or settings.database_url
    if url.startswith("sqlite+pysqlite:///:memory:"):
        print("Refusing to seed an in-memory database. Set DATABASE_URL.", file=sys.stderr)
        sys.exit(2)

    engine = make_engine(url)
    Base.metadata.create_all(engine)
    factory = make_session_factory(engine)
    started = time.perf_counter()
    with factory() as session:
        result = seed(session, count=args.count, reset=args.reset)
        session.commit()
        counts = verify_counts(session)
    elapsed = time.perf_counter() - started
    print(f"seeded {result['employees']} employees in {elapsed:.2f}s")
    print(f"checksum {result['checksum']}")
    print(counts)
    if elapsed >= 60:
        print("warning: seed exceeded 60s budget", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
