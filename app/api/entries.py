from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import json
from app.models.entry import EntryCreate, EntryUpdate, Entry
from app.storage.db import init_db, get_entries, get_entry_by_id, update_entry, create_entry
import os

router = APIRouter()

# Initialize database on module import
if not os.path.exists("./data/til_system.db"):
    init_db()


def _row_to_entry(row) -> Entry:
    """Convert a sqlite3.Row into an Entry, deserializing JSON columns."""
    def _load_json(key):
        raw = row[key]
        if not raw:
            return None
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return None

    return Entry(
        id=row['id'],
        restaurant=row['restaurant'],
        ticket_number=row['ticket_number'],
        discrepancy_type=row['discrepancy_type'],
        extracted_text=row['extracted_text'],
        description=row['description'],
        status=row['status'],
        extra_fields=_load_json('extra_fields'),
        blocks=_load_json('blocks'),
        image_filename=row['image_filename'],
    )


@router.get("/entries", response_model=List[Entry])
async def get_entries_endpoint(
    restaurant: Optional[str] = Query(None, description="Filter by restaurant"),
    ticket_number: Optional[str] = Query(None, description="Filter by ticket number")
):
    """
    Get table rows with optional filtering by restaurant and/or ticket number.

    Args:
        restaurant: Optional filter by restaurant name
        ticket_number: Optional filter by ticket number

    Returns:
        List of entry objects
    """
    rows = get_entries(restaurant=restaurant, ticket_number=ticket_number)
    return [_row_to_entry(row) for row in rows]

@router.patch("/entries/{entry_id}", response_model=Entry)
async def update_entry_endpoint(entry_id: int, entry_update: EntryUpdate):
    """
    Update an entry's description and/or status.

    Args:
        entry_id: ID of the entry to update
        entry_update: Fields to update (description and/or status)

    Returns:
        Updated entry object

    Raises:
        HTTPException: If entry not found
    """
    # Check if entry exists
    existing_entry = get_entry_by_id(entry_id)
    if not existing_entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    # Prepare update data (only include fields that were provided)
    update_data = entry_update.dict(exclude_unset=True)

    if not update_data:
        # If no fields to update, return existing entry
        return _row_to_entry(existing_entry)

    # Update the entry
    success = update_entry(entry_id, update_data)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update entry")

    # Get and return updated entry
    updated_entry = get_entry_by_id(entry_id)
    if not updated_entry:
        raise HTTPException(status_code=404, detail="Entry not found after update")

    return _row_to_entry(updated_entry)

# Note: POST /entries would be called internally by the upload endpoint
# after text extraction and parsing, but that's outside the scope of Division 2
# as per the task description which says to assume /upload already returns
# raw extracted text per image.