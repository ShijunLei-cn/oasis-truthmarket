import sqlite3
import tempfile
import unittest
from pathlib import Path

from oasis.social_platform.database import REQUIRED_SCHEMA_TABLES, create_db


class SocialPlatformDatabaseTests(unittest.TestCase):
    def test_complete_existing_database_is_reopened_without_recreating_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            database_path = Path(tmp) / "market.db"
            connection, _ = create_db(str(database_path))
            connection.execute(
                "INSERT INTO user (agent_id, user_name, budget) "
                "VALUES (1, 'seller', 60.0)"
            )
            connection.commit()
            connection.close()

            reopened, cursor = create_db(str(database_path))
            existing_tables = {
                row[0]
                for row in cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                ).fetchall()
            }
            saved_user = cursor.execute(
                "SELECT agent_id, user_name, budget FROM user"
            ).fetchone()
            reopened.close()

            self.assertTrue(REQUIRED_SCHEMA_TABLES <= existing_tables)
            self.assertEqual(saved_user, (1, "seller", 60))

    def test_incomplete_existing_database_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            database_path = Path(tmp) / "partial.db"
            with sqlite3.connect(database_path) as connection:
                connection.execute("CREATE TABLE user (user_id INTEGER)")

            with self.assertRaisesRegex(
                sqlite3.DatabaseError,
                "incomplete schema",
            ):
                create_db(str(database_path))


if __name__ == "__main__":
    unittest.main()
