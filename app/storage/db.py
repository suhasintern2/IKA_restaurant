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

        conn.execute("""
            CREATE TABLE IF NOT EXISTS ticket_records (
                ticket_id TEXT PRIMARY KEY,
                ticket_id_display TEXT NOT NULL,
                restaurant TEXT,
                phone TEXT,
                ticket_date TEXT,
                terminal TEXT,
                table_name TEXT,
                department TEXT,
                user_name TEXT,
                payment_status TEXT,
                credit_card_amount TEXT,
                ticket_total TEXT,
                grand_total TEXT,
                charged TEXT,
                extra_fields TEXT,
                items TEXT NOT NULL,
                screenshot_filenames TEXT NOT NULL,
                raw_texts TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS docket_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                docket_order_no TEXT,
                docket_date TEXT,
                docket_time TEXT,
                item TEXT,
                discrepancy_type TEXT,
                handwritten_reason TEXT,
                printed_text TEXT NOT NULL,
                raw_text TEXT NOT NULL,
                extra_fields TEXT,
                image_filename TEXT NOT NULL,
                review_required INTEGER NOT NULL DEFAULT 0,
                review_reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS ticket_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id TEXT NOT NULL REFERENCES ticket_records(ticket_id) ON DELETE CASCADE,
                item TEXT,
                category TEXT,
                price TEXT,
                qty TEXT,
                total TEXT,
                is_void INTEGER NOT NULL DEFAULT 0
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

        # Add blocks column (JSON) if it doesn't exist
        try:
            conn.execute("ALTER TABLE entries ADD COLUMN blocks TEXT")
            conn.commit()
        except sqlite3.OperationalError:
            # Column already exists, which is fine
            pass

        conn.commit()

def create_entry(entry: EntryInDBBase) -> int:
    """Create a new entry and return its ID."""
    with get_db_connection() as conn:
        extra_fields_json = json.dumps(entry.extra_fields) if entry.extra_fields else None
        blocks_json = json.dumps(entry.blocks) if entry.blocks else None

        cursor = conn.execute("""
            INSERT INTO entries (restaurant, ticket_number, discrepancy_type, extracted_text, description, status, extra_fields, blocks, image_filename)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entry.restaurant,
            entry.ticket_number,
            entry.discrepancy_type,
            entry.extracted_text,
            entry.description,
            entry.status,
            extra_fields_json,
            blocks_json,
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
        if key in ['restaurant', 'ticket_number', 'discrepancy_type', 'extracted_text', 'description', 'status', 'extra_fields', 'blocks', 'image_filename']:
            # Convert dict fields to JSON strings for storage
            if key in ('extra_fields', 'blocks') and value is not None:
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


def get_ticket_record(ticket_id: str) -> t.Optional[sqlite3.Row]:
    """Return one merged ticket record by normalized Ticket ID."""
    with get_db_connection() as conn:
        return conn.execute(
            "SELECT * FROM ticket_records WHERE ticket_id = ?",
            (ticket_id,),
        ).fetchone()


def upsert_ticket_record(ticket: t.Dict[str, t.Any]) -> sqlite3.Row:
    """Insert or merge a ticket record atomically, preserving populated fields."""
    with get_db_connection() as conn:
        existing = conn.execute(
            "SELECT * FROM ticket_records WHERE ticket_id = ?",
            (ticket["ticket_id"],),
        ).fetchone()

        if existing:
            def existing_json(name: str) -> t.Any:
                raw = existing[name]
                try:
                    return json.loads(raw) if raw else None
                except (json.JSONDecodeError, TypeError):
                    return None

            merged = dict(ticket)
            for field in (
                "restaurant", "phone", "ticket_date", "terminal", "table_name",
                "department", "user_name", "payment_status", "credit_card_amount",
                "ticket_total", "grand_total", "charged",
            ):
                merged[field] = ticket.get(field) or existing[field]

            old_extra = existing_json("extra_fields") or {}
            old_extra.update(ticket.get("extra_fields") or {})
            merged["extra_fields"] = old_extra

            old_items = existing_json("items") or []
            seen_items = {
                (
                    str(item.get("name", "")).strip().casefold(),
                    str(item.get("quantity", "")).strip(),
                    str(item.get("unit_price", "")).strip(),
                )
                for item in old_items
            }
            for item in ticket.get("items") or []:
                key = (
                    str(item.get("name", "")).strip().casefold(),
                    str(item.get("quantity", "")).strip(),
                    str(item.get("unit_price", "")).strip(),
                )
                if key not in seen_items:
                    old_items.append(item)
                    seen_items.add(key)
            merged["items"] = old_items

            old_screenshots = existing_json("screenshot_filenames") or []
            merged["screenshot_filenames"] = list(dict.fromkeys(
                old_screenshots + (ticket.get("screenshot_filenames") or [])
            ))
            old_raw_texts = existing_json("raw_texts") or []
            merged["raw_texts"] = list(dict.fromkeys(
                old_raw_texts + (ticket.get("raw_texts") or [])
            ))

            conn.execute("""
                UPDATE ticket_records SET
                    ticket_id_display = ?, restaurant = ?, phone = ?, ticket_date = ?,
                    terminal = ?, table_name = ?, department = ?, user_name = ?,
                    payment_status = ?, credit_card_amount = ?, ticket_total = ?,
                    grand_total = ?, charged = ?, extra_fields = ?, items = ?,
                    screenshot_filenames = ?, raw_texts = ?, updated_at = CURRENT_TIMESTAMP
                WHERE ticket_id = ?
            """, (
                merged.get("ticket_id_display") or existing["ticket_id_display"],
                merged.get("restaurant"), merged.get("phone"), merged.get("ticket_date"),
                merged.get("terminal"), merged.get("table_name"), merged.get("department"),
                merged.get("user_name"), merged.get("payment_status"),
                merged.get("credit_card_amount"), merged.get("ticket_total"),
                merged.get("grand_total"), merged.get("charged"),
                json.dumps(merged["extra_fields"]), json.dumps(merged["items"]),
                json.dumps(merged["screenshot_filenames"]), json.dumps(merged["raw_texts"]),
                ticket["ticket_id"],
            ))
        else:
            conn.execute("""
                INSERT INTO ticket_records (
                    ticket_id, ticket_id_display, restaurant, phone, ticket_date,
                    terminal, table_name, department, user_name, payment_status,
                    credit_card_amount, ticket_total, grand_total, charged,
                    extra_fields, items, screenshot_filenames, raw_texts
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ticket["ticket_id"], ticket["ticket_id_display"], ticket.get("restaurant"),
                ticket.get("phone"), ticket.get("ticket_date"), ticket.get("terminal"),
                ticket.get("table_name"), ticket.get("department"), ticket.get("user_name"),
                ticket.get("payment_status"), ticket.get("credit_card_amount"),
                ticket.get("ticket_total"), ticket.get("grand_total"), ticket.get("charged"),
                json.dumps(ticket.get("extra_fields") or {}),
                json.dumps(ticket.get("items") or []),
                json.dumps(ticket.get("screenshot_filenames") or []),
                json.dumps(ticket.get("raw_texts") or []),
            ))

        items_for_child_table = merged["items"] if existing else (ticket.get("items") or [])
        conn.execute("DELETE FROM ticket_items WHERE ticket_id = ?", (ticket["ticket_id"],))
        conn.executemany(
            """
            INSERT INTO ticket_items (ticket_id, item, category, price, qty, total, is_void)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    ticket["ticket_id"], item.get("name"), item.get("category"),
                    item.get("price") or item.get("unit_price"),
                    item.get("qty") or item.get("quantity"), item.get("total"),
                    int(bool(item.get("is_void"))),
                )
                for item in items_for_child_table
            ],
        )
        conn.commit()
        return conn.execute(
            "SELECT * FROM ticket_records WHERE ticket_id = ?",
            (ticket["ticket_id"],),
        ).fetchone()


def create_docket_record(docket: t.Dict[str, t.Any]) -> int:
    """Persist one parsed docket; docket order numbers are intentionally not unique."""
    with get_db_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO docket_records (
                docket_order_no, docket_date, docket_time, item, discrepancy_type,
                handwritten_reason, printed_text, raw_text, extra_fields,
                image_filename, review_required, review_reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            docket.get("docket_order_no"), docket.get("docket_date"),
            docket.get("docket_time"), docket.get("item"),
            docket.get("discrepancy_type"), docket.get("handwritten_reason"),
            docket.get("printed_text") or "", docket.get("raw_text") or "",
            json.dumps(docket.get("extra_fields") or {}), docket["image_filename"],
            int(bool(docket.get("review_required"))), docket.get("review_reason"),
        ))
        conn.commit()
        return cursor.lastrowid


def get_docket_record(docket_id: int) -> t.Optional[sqlite3.Row]:
    """Return a docket row after it has been persisted."""
    with get_db_connection() as conn:
        return conn.execute(
            "SELECT * FROM docket_records WHERE id = ?",
            (docket_id,),
        ).fetchone()


def get_ticket_records() -> t.List[sqlite3.Row]:
    """Return all merged ticket records in stable update order."""
    with get_db_connection() as conn:
        return conn.execute(
            "SELECT * FROM ticket_records ORDER BY updated_at DESC, ticket_id"
        ).fetchall()


def get_ticket_items(ticket_id: str) -> t.List[sqlite3.Row]:
    """Return normalized child item rows for one ticket."""
    with get_db_connection() as conn:
        return conn.execute(
            "SELECT item, category, price, qty, total, is_void FROM ticket_items WHERE ticket_id = ? ORDER BY id",
            (ticket_id,),
        ).fetchall()


def get_docket_records() -> t.List[sqlite3.Row]:
    """Return all docket records in stable creation order."""
    with get_db_connection() as conn:
        return conn.execute(
            "SELECT * FROM docket_records ORDER BY created_at ASC, id ASC"
        ).fetchall()