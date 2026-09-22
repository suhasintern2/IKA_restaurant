import os
import uuid
import json
import logging
import re
from typing import Any, Dict, List
from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from app.extraction.ocr import extract_text_from_image
from app.models.ticket import parse_ticket_screenshot
from app.models.docket import ORDER_NO_RE, parse_docket_text
from app.storage.db import create_docket_record, get_docket_record, get_ticket_record, upsert_ticket_record, init_db


logger = logging.getLogger(__name__)

router = APIRouter()
init_db()

# Configure upload directory
UPLOAD_DIR = "data/uploads"
TICKET_SCREENSHOT_DIR = os.path.join(UPLOAD_DIR, "ticket_screenshots")
DOCKET_IMAGE_DIR = os.path.join(UPLOAD_DIR, "dockets")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(TICKET_SCREENSHOT_DIR, exist_ok=True)
os.makedirs(DOCKET_IMAGE_DIR, exist_ok=True)
MAX_BULK_UPLOADS = 30


def _looks_like_ticket_screenshot(extracted_text: str) -> bool:
    """Detect ticket screenshot using the master prompt's pattern: Ticket #YYMMDD-N"""
    return bool(re.search(r"(?:ticket\s*)?#?\s*\d{6}\s*[-–]\s*\d+", extracted_text, re.IGNORECASE))


def _map_ticket_to_storage(parsed: Dict[str, Any]) -> Dict[str, Any]:
    """Map the master prompt's ticket structure to the storage format expected by upsert_ticket_record."""
    # Extract ticket number (without #) for ticket_id
    ticket_number = parsed.get("ticket_number")
    ticket_id = ticket_number  # This is already in the format YYMMDD-N
    ticket_id_display = f"#{ticket_number}" if ticket_number else None

    # Map fields
    mapped = {
        "ticket_id": ticket_id,
        "ticket_id_display": ticket_id_display,
        "restaurant": parsed.get("restaurant"),
        "phone": None,  # Not in master prompt; we leave as None
        "ticket_date": parsed.get("date"),
        "terminal": parsed.get("terminal"),
        "table_name": parsed.get("table"),
        "department": parsed.get("department"),
        "user_name": parsed.get("user"),
        "payment_status": parsed.get("payment_status"),
        "credit_card_amount": parsed.get("credit_card_amount"),
        "ticket_total": parsed.get("ticket_total"),
        "grand_total": parsed.get("grand_total"),
        "charged": parsed.get("charged"),
        "extra_fields": parsed.get("extra_fields", {}),
        "items": parsed.get("items", []),
        # screenshot_filenames and raw_texts will be added by the caller
    }
    # Remove None values? We'll keep them as None; the storage function handles None.
    return mapped


def _map_docket_to_storage(parsed: Dict[str, Any], extracted_text: str, image_filename: str) -> Dict[str, Any]:
    """Map the master prompt's docket structure to the storage format expected by create_docket_record."""
    # Extract date and time
    date = parsed.get("date")
    time = parsed.get("time")

    # Determine review_required and review_reason
    docket_order_no = parsed.get("docket_order_no")
    discrepancy_type = parsed.get("discrepancy_type")
    unique_order_numbers = list(dict.fromkeys(ORDER_NO_RE.findall(extracted_text)))
    ambiguous = len(unique_order_numbers) > 1
    review_required = ambiguous or not unique_order_numbers or not discrepancy_type
    review_reason = ""
    if ambiguous:
        review_reason = "Multiple docket order numbers detected in one image"
    elif not unique_order_numbers:
        review_reason = "Could not isolate one docket order number"
    elif not discrepancy_type:
        review_reason = "Could not isolate discrepancy marker"

    # Map fields
    mapped = {
        "docket_order_no": docket_order_no,
        "docket_date": date,
        "docket_time": time,
        "item": parsed.get("item"),
        "discrepancy_type": discrepancy_type,
        "handwritten_reason": parsed.get("handwritten_reason"),
        "printed_text": parsed.get("printed_text") or "",
        "raw_text": extracted_text,
        "extra_fields": parsed.get("extra_fields", {}),
        "image_filename": image_filename,
        "review_required": review_required,
        "review_reason": review_reason,
    }
    return mapped


async def _process_uploaded_file(
    file: UploadFile = File(...),
    restaurant: str = Form(None, description="Restaurant name (optional - overrides OCR extraction)")
):
    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise ValueError("File must be an image")

    # Generate unique filename to avoid conflicts
    original_filename = file.filename or "unnamed"
    file_extension = os.path.splitext(original_filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    try:
        # Save uploaded file
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)

        # Extract text from image using OCR
        extracted_text = extract_text_from_image(file_path)

        if _looks_like_ticket_screenshot(extracted_text):
            # Treat as ticket
            parsed_ticket = parse_ticket_screenshot(extracted_text)
            if not parsed_ticket.get("ticket_number"):
                raise ValueError("Ticket screenshot detected, but the full Ticket ID could not be parsed")

            # Map to storage format
            ticket_for_storage = _map_ticket_to_storage(parsed_ticket)

            # Save the ticket screenshot
            ticket_filename = f"ticket-{uuid.uuid4()}{file_extension or '.png'}"
            ticket_path = os.path.join(TICKET_SCREENSHOT_DIR, ticket_filename)
            with open(ticket_path, "wb") as ticket_handle:
                ticket_handle.write(contents)
            os.remove(file_path)
            file_path = ticket_path

            # Add screenshot_filenames and raw_texts
            ticket_for_storage["screenshot_filenames"] = [ticket_filename]
            ticket_for_storage["raw_texts"] = [extracted_text]

            record = upsert_ticket_record(ticket_for_storage)
            if get_ticket_record(ticket_for_storage["ticket_id"]) is None:
                raise RuntimeError("Ticket was saved but could not be retrieved")
            return {
                "record_type": "ticket",
                "filename": ticket_filename,
                "original_filename": original_filename,
                "extracted_text": extracted_text,
                "ticket_number": record["ticket_id"],
                "ticket_id": record["ticket_id"],
                "item_count": len(json.loads(record["items"])),
                "screenshot_count": len(json.loads(record["screenshot_filenames"])),
            }

        else:
            raise ValueError(
                "Unrecognized image type; use /api/upload/tickets for ticket screenshots "
                "or /api/upload/dockets for docket images"
            )

    except Exception as e:
        # Clean up file if processing failed
        if os.path.exists(file_path):
            os.remove(file_path)
        raise RuntimeError(f"Failed to process image: {str(e)}") from e


@router.post("/upload")
async def upload_bill_image(
    file: UploadFile = File(...),
    restaurant: str = Form(None, description="Restaurant name (optional - overrides OCR extraction)")
):
    """Upload and process one bill image."""
    try:
        return await _process_uploaded_file(file, restaurant)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        ) from e


@router.post("/upload/bulk")
async def upload_bill_images_bulk(
    files: List[UploadFile] = File(...),
    restaurant: str = Form(None, description="Restaurant name (optional - overrides OCR extraction)")
):
    """Process up to 30 bill images and report each result independently."""
    if len(files) > MAX_BULK_UPLOADS:
        raise HTTPException(
            status_code=400,
            detail=f"Bulk upload accepts at most {MAX_BULK_UPLOADS} images"
        )

    succeeded = []
    failed = []
    for file in files:
        original_filename = file.filename or "unnamed"
        try:
            succeeded.append(await _process_uploaded_file(file, restaurant))
        except Exception as e:
            failed.append({
                "filename": original_filename,
                "reason": str(e),
            })

    return {
        "total": len(files),
        "succeeded": succeeded,
        "failed": failed,
    }


@router.post("/upload/tickets")
async def upload_ticket_screenshots(files: List[UploadFile] = File(...)):
    """OCR and merge a batch of ticket screenshots by their Ticket ID."""
    if len(files) > MAX_BULK_UPLOADS:
        raise HTTPException(
            status_code=400,
            detail=f"Bulk ticket screenshot upload accepts at most {MAX_BULK_UPLOADS} files"
        )

    succeeded = []
    failed = []
    for file in files:
        original_filename = file.filename or "unnamed"
        file_path = None
        try:
            if not file.content_type or not file.content_type.startswith("image/"):
                raise ValueError("Ticket upload must be an image")

            extension = os.path.splitext(original_filename)[1] or ".png"
            stored_filename = f"ticket-{uuid.uuid4()}{extension}"
            file_path = os.path.join(TICKET_SCREENSHOT_DIR, stored_filename)
            contents = await file.read()
            with open(file_path, "wb") as handle:
                handle.write(contents)

            extracted_text = extract_text_from_image(file_path)
            parsed = parse_ticket_screenshot(extracted_text)
            if not parsed.get("ticket_number"):
                raise ValueError("Could not extract Ticket ID in #YYMMDD-N format")

            # Map to storage format
            ticket_for_storage = _map_ticket_to_storage(parsed)
            ticket_for_storage["screenshot_filenames"] = [stored_filename]
            ticket_for_storage["raw_texts"] = [extracted_text]

            record = upsert_ticket_record(ticket_for_storage)
            succeeded.append({
                "filename": stored_filename,
                "original_filename": original_filename,
                "ticket_number": record["ticket_id"],
                "ticket_id": record["ticket_id"],
                "item_count": len(json.loads(record["items"])),
                "screenshot_count": len(json.loads(record["screenshot_filenames"])),
            })
        except Exception as error:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
            logger.exception("Ticket screenshot parsing failed for %s", original_filename)
            failed.append({
                "filename": original_filename,
                "reason": str(error),
            })

    return {
        "total": len(files),
        "succeeded": succeeded,
        "failed": failed,
    }


@router.post("/upload/dockets")
async def upload_docket_images(files: List[UploadFile] = File(...)):
    """OCR and store a batch of discrepancy dockets with partial failures."""
    if len(files) > MAX_BULK_UPLOADS:
        raise HTTPException(
            status_code=400,
            detail=f"Bulk docket upload accepts at most {MAX_BULK_UPLOADS} files"
        )

    succeeded = []
    failed = []
    for file in files:
        original_filename = file.filename or "unnamed"
        file_path = None
        try:
            if not file.content_type or not file.content_type.startswith("image/"):
                raise ValueError("Docket upload must be an image")

            extension = os.path.splitext(original_filename)[1] or ".png"
            stored_filename = f"docket-{uuid.uuid4()}{extension}"
            file_path = os.path.join(DOCKET_IMAGE_DIR, stored_filename)
            contents = await file.read()
            with open(file_path, "wb") as handle:
                handle.write(contents)

            extracted_text = extract_text_from_image(file_path)
            parsed = parse_docket_text(extracted_text)
            # Map to storage format
            docket_for_storage = _map_docket_to_storage(parsed, extracted_text, stored_filename)

            docket_id = create_docket_record(docket_for_storage)
            stored_docket = get_docket_record(docket_id)
            if stored_docket is None:
                raise RuntimeError("Docket was saved but could not be retrieved")
            succeeded.append({
                "id": stored_docket["id"],
                "filename": stored_filename,
                "original_filename": original_filename,
                "order_number": stored_docket["docket_order_no"],
                "date": stored_docket["docket_date"],
                "time": stored_docket["docket_time"],
                "item": stored_docket["item"],
                "discrepancy_type": stored_docket["discrepancy_type"],
                "description": stored_docket["handwritten_reason"],
                "review_required": bool(stored_docket["review_required"]),
                "review_reason": stored_docket["review_reason"],
            })
        except Exception as error:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
            failed.append({
                "filename": original_filename,
                "reason": str(error),
            })

    return {
        "total": len(files),
        "succeeded": succeeded,
        "failed": failed,
    }