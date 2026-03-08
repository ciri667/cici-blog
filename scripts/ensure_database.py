from __future__ import annotations

from pathlib import Path
from urllib.parse import parse_qsl, quote, unquote, urlencode, urlsplit, urlunsplit

import psycopg2
from psycopg2 import sql

ROOT_DIR = Path(__file__).resolve().parent.parent


def _load_database_url() -> str:
    # Import project settings so .env and default config are both honored.
    import sys

    sys.path.insert(0, str(ROOT_DIR))
    from app.core.config import settings  # pylint: disable=import-outside-toplevel

    return settings.DATABASE_URL


def _to_sync_psycopg2_url(database_url: str) -> str:
    parts = urlsplit(database_url)

    if not parts.scheme.startswith("postgresql"):
        raise ValueError("Only PostgreSQL DATABASE_URL is supported.")

    # Convert SQLAlchemy async URL such as postgresql+asyncpg:// to psycopg2 URL.
    scheme = "postgresql"
    netloc = parts.netloc
    path = parts.path

    query_items = parse_qsl(parts.query, keep_blank_values=True)
    filtered = [(k, v) for k, v in query_items if k != "async_fallback"]
    query = urlencode(filtered)

    return urlunsplit((scheme, netloc, path, query, parts.fragment))


def _extract_db_name(pg_url: str) -> str:
    parts = urlsplit(pg_url)
    db_name = unquote(parts.path.lstrip("/"))
    if not db_name:
        raise ValueError("DATABASE_URL must include a database name.")
    return db_name


def _build_admin_db_url(pg_url: str, admin_db: str = "postgres") -> str:
    parts = urlsplit(pg_url)
    admin_path = "/" + quote(admin_db, safe="")
    return urlunsplit((parts.scheme, parts.netloc, admin_path, parts.query, parts.fragment))


def ensure_database_exists() -> None:
    database_url = _load_database_url()
    pg_url = _to_sync_psycopg2_url(database_url)
    target_db = _extract_db_name(pg_url)
    admin_url = _build_admin_db_url(pg_url)

    conn = psycopg2.connect(admin_url)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (target_db,))
            exists = cur.fetchone() is not None
            if exists:
                print(f"Database '{target_db}' already exists.")
                return

            cur.execute(
                sql.SQL("CREATE DATABASE {}").format(sql.Identifier(target_db))
            )
            print(f"Database '{target_db}' created.")
    finally:
        conn.close()


if __name__ == "__main__":
    ensure_database_exists()
