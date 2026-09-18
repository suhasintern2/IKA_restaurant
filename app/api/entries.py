from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.models.entry import EntryCreate, EntryUpdate, Entry
from app.storage.db import init_db, get_entries, get_entry_by_id, update_entry, create_entry
import os

router = APIRouter()

# Initialize database on module import
if not os.path.exists("./data/til_system.db"):
    init_db()

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

    # Convert sqlite3.Row objects to Entry models
    entries = []
    for row in rows:
        entry = Entry(
            id=row['id'],
            restaurant=row['restaurant'],
            ticket_number=row['ticket_number'],
            discrepancy_type=row['discrepancy_type'],
            extracted_text=row['extracted_text'],
            description=row['description'],
            status=row['status']
        )
        entries.append(entry)

    return entries

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
        return Entry(
            id=existing_entry['id'],
            restaurant=existing_entry['restaurant'],
            ticket_number=existing_entry['ticket_number'],
            discrepancy_type=existing_entry['discrepancy_type'],
            extracted_text=existing_entry['extracted_text'],
            description=existing_entry['description'],
            status=existing_entry['status']
        )

    # Update the entry
    success = update_entry(entry_id, update_data)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update entry")

    # Get and return updated entry
    updated_entry = get_entry_by_id(entry_id)
    if not updated_entry:
        raise HTTPException(status_code=404, detail="Entry not found after update")

    return Entry(
        id=updated_entry['id'],
        restaurant=updated_entry['restaurant'],
        ticket_number=updated_entry['ticket_number'],
        discrepancy_type=updated_entry['discrepancy_type'],
        extracted_text=updated_entry['extracted_text'],
        description=updated_entry['description'],
        status=updated_entry['status']
    )

# Note: POST /entries would be called internally by the upload endpoint
# after text extraction and parsing, but that's outside the scope of Division 2
# as per the task description which says to assume /upload already returns
# raw extracted text per image.