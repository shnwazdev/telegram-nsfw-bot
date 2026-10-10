"""
Persistent SQLite Database for Users, Groups, and Feature Settings
"""

import sqlite3
import os
import logging
from pathlib import Path
from typing import List, Dict, Optional
from . import config

logger = logging.getLogger("database")

DB_FILE = os.path.join(config.ROOT_DIR, "bot_data.db")


def get_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                chat_id INTEGER PRIMARY KEY,
                title TEXT,
                members_count INTEGER DEFAULT 0,
                nsfw_enabled INTEGER DEFAULT 1,
                edit_guard_enabled INTEGER DEFAULT 1,
                sensitivity TEXT DEFAULT 'balanced',
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    conn.close()
    logger.info("Database initialized successfully.")


def add_or_update_user(user_id: int, username: Optional[str], first_name: Optional[str]):
    conn = get_connection()
    with conn:
        conn.execute("""
            INSERT INTO users (user_id, username, first_name)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name
        """, (user_id, username, first_name))
    conn.close()


def get_all_users() -> List[int]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users")
    rows = cur.fetchall()
    conn.close()
    return [r["user_id"] for r in rows]


def add_or_update_group(chat_id: int, title: str, members_count: int = 0):
    conn = get_connection()
    with conn:
        conn.execute("""
            INSERT INTO groups (chat_id, title, members_count)
            VALUES (?, ?, ?)
            ON CONFLICT(chat_id) DO UPDATE SET
                title = excluded.title,
                members_count = CASE WHEN excluded.members_count > 0 THEN excluded.members_count ELSE members_count END
        """, (chat_id, title, members_count))
    conn.close()


def remove_group(chat_id: int):
    conn = get_connection()
    with conn:
        conn.execute("DELETE FROM groups WHERE chat_id = ?", (chat_id,))
    conn.close()


def get_all_groups() -> List[Dict]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT chat_id, title, members_count, nsfw_enabled, edit_guard_enabled, sensitivity FROM groups")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_group_settings(chat_id: int) -> Dict:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT nsfw_enabled, edit_guard_enabled, sensitivity FROM groups WHERE chat_id = ?", (chat_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return {
            "nsfw_enabled": bool(row["nsfw_enabled"]),
            "edit_guard_enabled": bool(row["edit_guard_enabled"]),
            "sensitivity": row["sensitivity"] or "balanced"
        }
    return {
        "nsfw_enabled": True,
        "edit_guard_enabled": True,
        "sensitivity": "balanced"
    }


def set_nsfw_status(chat_id: int, enabled: bool):
    conn = get_connection()
    with conn:
        conn.execute("""
            INSERT INTO groups (chat_id, nsfw_enabled)
            VALUES (?, ?)
            ON CONFLICT(chat_id) DO UPDATE SET nsfw_enabled = excluded.nsfw_enabled
        """, (chat_id, 1 if enabled else 0))
    conn.close()


def set_edit_guard_status(chat_id: int, enabled: bool):
    conn = get_connection()
    with conn:
        conn.execute("""
            INSERT INTO groups (chat_id, edit_guard_enabled)
            VALUES (?, ?)
            ON CONFLICT(chat_id) DO UPDATE SET edit_guard_enabled = excluded.edit_guard_enabled
        """, (chat_id, 1 if enabled else 0))
    conn.close()


def set_group_sensitivity(chat_id: int, sensitivity: str):
    conn = get_connection()
    with conn:
        conn.execute("""
            INSERT INTO groups (chat_id, sensitivity)
            VALUES (?, ?)
            ON CONFLICT(chat_id) DO UPDATE SET sensitivity = excluded.sensitivity
        """, (chat_id, sensitivity))
    conn.close()


init_db()
