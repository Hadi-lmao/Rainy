from pathlib import Path
import sqlite3

def initialize_database(database_file):
    database_file = Path(database_file)
    database_file.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(database_file) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                activity_name TEXT NOT NULL,
                description TEXT DEFAULT '',
                focus_seconds INTEGER NOT NULL DEFAULT 0,
                focus_periods INTEGER NOT NULL DEFAULT 0,
                breaks_completed INTEGER NOT NULL DEFAULT 0,
                started_at TEXT NOT NULL,
                ended_at TEXT NOT NULL
            )
        """)

def save_activity(database_file,activity_name,description,focus_seconds,focus_periods,breaks_completed,started_at,ended_at):
    with sqlite3.connect(database_file) as connection:
        connection.execute("""
            INSERT INTO activities (
                activity_name,
                description,
                focus_seconds,
                focus_periods,
                breaks_completed,
                started_at,
                ended_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            activity_name,
            description,
            focus_seconds,
            focus_periods,
            breaks_completed,
            started_at,
            ended_at,
        ))

def get_activities(database_file):
    with sqlite3.connect(database_file) as connection:
        connection.row_factory = sqlite3.Row

        rows = connection.execute("""
            SELECT *
            FROM activities
            ORDER BY ended_at DESC
        """).fetchall()

        return [dict(row) for row in rows]

def get_daily_focus(database_file):
    with sqlite3.connect(database_file) as connection:
        rows = connection.execute("""
            SELECT
                DATE(ended_at) AS day,
                SUM(focus_seconds) AS total_seconds
            FROM activities
            GROUP BY DATE(ended_at)
            ORDER BY day ASC
        """).fetchall()

        return [
            (day, total_seconds // 60)
            for day, total_seconds in rows
        ]

def get_session_totals(database_file):
    with sqlite3.connect(database_file) as connection:
        row = connection.execute("""
            SELECT
                COALESCE(SUM(focus_periods), 0),
                COALESCE(SUM(breaks_completed), 0)
            FROM activities
        """).fetchone()

        return {
            "focus_periods": row[0],
            "breaks": row[1],
        }