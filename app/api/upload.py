import os
import uuid
from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from app.extraction.ocr import extract_text_from_image
from app.models.entry import parse_extracted_text, EntryCreate
from app.storage.db import create_entry


def determine_status(parsed_data: dict) -> str:
    """
    Determine the status of an entry based on parsed fields.

    Args:
        parsed_data: Dictionary containing parsed fields from OCR

    Returns:
        str: Status - "matched", "needs_description", "needs_ticket_number",
               "needs_restaurant", "needs_discrepancy_type", or "needs_review"
    """
    # Check for critical missing fields
    missing_fields = []

    if not parsed_data.get("restaurant") or parsed_data.get("restaurant") == "unknown":
        missing_fields.append("restaurant")

    if not parsed_data.get("ticket_number"):
        missing_fields.append("ticket_number")

    if not parsed_data.get("discrepancy_type") or parsed_data.get("discrepancy_type") == "unknown":
        missing_fields.append("discrepancy_type")

    description = parsed_data.get("description")
    if not description or not description.strip():
        missing_fields.append("description")

    # Determine status based on missing fields
    if not missing_fields:
        return "matched"
    elif missing_fields == ["description"]:
        return "needs_description"
    elif "ticket_number" in missing_fields:
        return "needs_ticket_number"
    elif "restaurant" in missing_fields:
        return "needs_restaurant"
    elif "discrepancy_type" in missing_fields:
        return "needs_discrepancy_type"
    else:
        # Multiple missing fields or other combinations
        return "needs_review"

router = APIRouter()

# Configure upload directory
UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_bill_image(
    file: UploadFile = File(...),
    restaurant: str = Form(None, description="Restaurant name (optional - overrides OCR extraction)")
):
    """
    Upload a bill image, extract text, parse into structured fields, and store in database.

    Args:
        file: The uploaded image file
        restaurant: Optional restaurant name from frontend selection (overrides OCR extraction)

    Returns:
        dict: Contains filename, original filename, extracted text, and created entry ID

    Raises:
        HTTPException: If file is not an image or OCR fails
    """
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    # Generate unique filename to avoid conflicts
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    try:
        # Save uploaded file
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)

        # Extract text from image using OCR
        extracted_text = extract_text_from_image(file_path)

        # Parse extracted text into structured fields
        parsed_data = parse_extracted_text(extracted_text)

        # Use provided restaurant if given, otherwise use parsed/extracted restaurant
        final_restaurant = restaurant if restaurant else (parsed_data["restaurant"] or "unknown")

        # Create entry in database
        entry_to_create = EntryCreate(
            restaurant=final_restaurant,
            ticket_number=parsed_data["ticket_number"] or "",
            discrepancy_type=parsed_data["discrepancy_type"] or "unknown",
            extracted_text=extracted_text,
            description=parsed_data["description"] or None,
            status=determine_status({
                **parsed_data,
                "restaurant": final_restaurant
            }),
            extra_fields=parsed_data.get("extra_fields"),
            image_filename=unique_filename
        )

        entry_id = create_entry(entry_to_create)

        return {
            "filename": unique_filename,
            "original_filename": file.filename,
            "extracted_text": extracted_text,
            "entry_id": entry_id,
            "parsed_data": {
                **parsed_data,
                "restaurant": final_restaurant
            }
        }

    except Exception as e:
        # Clean up file if processing failed
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process image: {str(e)}"
        )