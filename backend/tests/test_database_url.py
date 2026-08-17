import unittest

from database_url import normalize_database_url


class DatabaseUrlTests(unittest.TestCase):
    def test_normalizes_supported_postgres_schemes_for_psycopg_three(self):
        expected = "postgresql+psycopg://user:password@db.example/app"
        self.assertEqual(normalize_database_url("postgres://user:password@db.example/app"), expected)
        self.assertEqual(normalize_database_url("postgresql://user:password@db.example/app"), expected)

    def test_preserves_explicit_dialects_and_non_postgres_urls(self):
        self.assertEqual(
            normalize_database_url("postgresql+psycopg://user:password@db.example/app"),
            "postgresql+psycopg://user:password@db.example/app",
        )
        self.assertEqual(normalize_database_url("sqlite:///claims.db"), "sqlite:///claims.db")


if __name__ == "__main__":
    unittest.main()
