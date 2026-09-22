from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
import csv
import io
from typing import Optional
from app.storage.db import get_entries

router = APIRouter()

@router.get("/export")
async def export_entries_csv(
    restaurant: Optional[str] = Query(None, description="Filter by restaurant"),
    ticket_number: Optional[str] = Query(None, description="Filter by ticket number")
):
    """
    Export entries table as CSV file.

    Supports the same filters as /entries endpoint:
    - restaurant: Optional filter by restaurant name
    - ticket_number: Optional filter by ticket number

    Returns:
        CSV file with columns: restaurant, ticket_number, discrepancy_type, description, status, image_filename

    Note: The image thumbnail cannot be exported to CSV, so we export the stored image filename/path instead.
    """
    # Get entries with the same filtering logic as the /entries endpoint
    rows = get_entries(restaurant=restaurant, ticket_number=ticket_number)

    # Create a CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header - matching the table columns from frontend_spec.md section 1 (Screen 2)
    # Plus image_filename since we can't export the actual thumbnail
    writer.writerow([
        'restaurant',
        'ticket_number',
        'discrepancy_type',
        'description',
        'status',
        'image_filename'  # Stored filename/path instead of thumbnail
    ])

    # Write data rows
    for row in rows:
        writer.writerow([
            row['restaurant'] or '',
            row['ticket_number'] or '',
            row['discrepancy_type'] or '',
            row['description'] or '',
            row['status'] or '',
            row['image_filename'] or ''  # Use stored image filename
        ])

    # Prepare the response
    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; export=til_system_entries.csv"}
    )