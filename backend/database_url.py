"""Database URL normalization independent of SQLAlchemy runtime imports."""


def normalize_database_url(url: str) -> str:
    """Use SQLAlchemy's Psycopg 3 dialect for PostgreSQL connection URLs."""
    for scheme in ("postgresql://", "postgres://"):
        if url.startswith(scheme):
            return "postgresql+psycopg://" + url.removeprefix(scheme)
    return url
