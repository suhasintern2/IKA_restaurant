import sqlite3
import os
import typing as t
import json
from contextlib import contextmanager
from datetime import datetime
from app.models.entry import EntryInDBBase

DATABASE_PATH = "./data/til_system.db"

@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Initialize the database with the entries table."""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

    with get_db_connection() as conn:
        # Create table if it doesn't exist
        conn.execute("""
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                restaurant TEXT NOT NULL,
                ticket_number TEXT NOT NULL,
                discrepancy_type TEXT NOT NULL,
                extracted_text TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL,
                extra_fields TEXT,
                image_filename TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Add extra_fields column if it doesn't exist (for existing databases) -- JSON string for extra fields
        try:
            conn.execute("ALTER TABLE entries ADD COLUMN extra_fields TEXT")
            conn.commit()
        except sqlite3.OperationalError:
            # Column already exists, which is fine
            pass

        # Add image_filename column if it doesn't exist
        try:
            conn.execute("ALTER TABLE entries ADD COLUMN image_filename TEXT")
            conn.commit()
        except sqlite3.OperationalError:
            # Column already exists, which is fine
            pass

        conn.commit()

def create_entry(entry: EntryInDBBase) -> int:
    """Create a new entry and return its ID."""
    with get_db_connection() as conn:
        # Convert extra_fields dict to JSON string for storage
        extra_fields_json = json.dumps(entry.extra_fields) if entry.extra_fields else None

        cursor = conn.execute("""
            INSERT INTO entries (restaurant, ticket_number, discrepancy_type, extracted_text, description, status, extra_fields, image_filename)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entry.restaurant,
            entry.ticket_number,
            entry.discrepancy_type,
            entry.extracted_text,
            entry.description,
            entry.status,
            extra_fields_json,
            entry.image_filename
        ))
        conn.commit()
        return cursor.lastrowid

def get_entries(restaurant: t.Optional[str] = None, ticket_number: t.Optional[str] = None) -> t.List[sqlite3.Row]:
    """Get entries with optional filtering by restaurant and/or ticket number."""
    query = "SELECT * FROM entries WHERE 1=1"
    params = []

    if restaurant:
        query += " AND restaurant = ?"
        params.append(restaurant)

    if ticket_number:
        query += " AND ticket_number = ?"
        params.append(ticket_number)

    query += " ORDER BY created_at DESC"

    with get_db_connection() as conn:
        cursor = conn.execute(query, params)
        return cursor.fetchall()

def get_entry_by_id(entry_id: int) -> t.Optional[sqlite3.Row]:
    """Get a single entry by ID."""
    with get_db_connection() as conn:
        cursor = conn.execute("SELECT * FROM entries WHERE id = ?", (entry_id,))
        return cursor.fetchone()

def update_entry(entry_id: int, updates: t.Dict[str, t.Any]) -> bool:
    """Update an entry with the given fields."""
    if not updates:
        return False

    # Build the SET clause dynamically
    set_clauses = []
    params = []
    for key, value in updates.items():
        if key in ['restaurant', 'ticket_number', 'discrepancy_type', 'extracted_text', 'description', 'status', 'extra_fields', 'image_filename']:
            # Handle extra_fields specially - convert to JSON string for storage
            if key == 'extra_fields' and value is not None:
                params.append(json.dumps(value))
            else:
                params.append(value)
            set_clauses.append(f"{key} = ?")

    if not set_clauses:
        return False

    # Always update the updated_at timestamp
    set_clauses.append("updated_at = CURRENT_TIMESTAMP")
    params.append(entry_id)

    query = f"UPDATE entries SET {', '.join(set_clauses)} WHERE id = ?"

    with get_db_connection() as conn:
        cursor = conn.execute(query, params)
        conn.commit()
        return cursor.rowcount > 0

def delete_entry(entry_id: int) -> bool:
    """Delete an entry by ID."""
    with get_db_connection() as conn:
        cursor = conn.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
        conn.commit()
        return cursor.rowcount > 0