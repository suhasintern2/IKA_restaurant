import os
import uuid
from fastapi import APIRouter, File, UploadFile, HTTPException
from app.extraction.ocr import extract_text_from_image
from app.models.entry import parse_extracted_text, EntryCreate
from app.storage.db import create_entry

router = APIRouter()

# Configure upload directory
UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_bill_image(file: UploadFile = File(...)):
    """
    Upload a bill image, extract text, parse into structured fields, and store in database.

    Args:
        file: The uploaded image file

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

        # Create entry in database
        entry_to_create = EntryCreate(
            restaurant=parsed_data["restaurant"] or "unknown",  # Default if not parsed
            ticket_number=parsed_data["ticket_number"] or "",
            discrepancy_type=parsed_data["discrepancy_type"] or "unknown",
            extracted_text=extracted_text,
            description=parsed_data["description"] or None,
            status="needs_description" if not (parsed_data["description"] or "").strip() else "unmatched"
        )

        entry_id = create_entry(entry_to_create)

        return {
            "filename": unique_filename,
            "original_filename": file.filename,
            "extracted_text": extracted_text,
            "entry_id": entry_id,
            "parsed_data": parsed_data
        }

    except Exception as e:
        # Clean up file if processing failed
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process image: {str(e)}"
        )