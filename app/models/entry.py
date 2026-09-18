import re
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

def parse_extracted_text(extracted_text: str) -> dict:
    """
    Parse raw extracted text from OCR to identify structured fields.

    Args:
        extracted_text: Raw text from OCR

    Returns:
        dict: Contains parsed fields (restaurant, ticket_number, discrepancy_type, description)
              Missing fields will be None or empty strings
    """
    # Initialize result with default/empty values
    result = {
        "restaurant": "",  # Will need to be filled by user or inferred from context
        "ticket_number": "",
        "discrepancy_type": "",
        "description": ""  # Will be empty -> status = needs_description
    }

    if not extracted_text:
        return result

    # Convert to lowercase for case-insensitive matching
    text_lower = extracted_text.lower()

    # Try to extract ticket number (look for sequences of 6+ digits)
    # Common ticket number patterns
    ticket_match = re.search(r'\b\d{6,}\b', extracted_text)
    if ticket_match:
        result["ticket_number"] = ticket_match.group()

    # Try to extract discrepancy type
    discrepancy_keywords = {
        "void": ["void", "voided"],
        "discount": ["discount", "disc", "discounted"],
        "promotion": ["promotion", "promo", "promotional", "offer", "deal"]
    }

    for disc_type, keywords in discrepancy_keywords.items():
        for keyword in keywords:
            if keyword in text_lower:
                result["discrepancy_type"] = disc_type
                break
        if result["discrepancy_type"]:
            break

    # Try to extract restaurant (if we know the possible names)
    # For MVP, we'll leave this blank as it's harder to infer reliably
    # In a real system, we might have a list of known restaurant names/patterns
    # result["restaurant"] = infer_restaurant_from_text(extracted_text)

    # For description, we could try to extract meaningful text,
    # but for simplicity we'll leave it empty -> status = needs_description
    # A more advanced approach might look for paragraphs, dates, amounts, etc.

    return result

class EntryBase(BaseModel):
    restaurant: str  # One of 3 restaurants
    ticket_number: str  # Extracted or entered
    discrepancy_type: str  # void, discount, or promotion
    extracted_text: str  # Raw OCR text
    description: Optional[str] = None  # User-provided description
    status: str  # matched, unmatched, needs_description

class EntryCreate(EntryBase):
    pass

class EntryUpdate(BaseModel):
    description: Optional[str] = None
    status: Optional[str] = None

class EntryInDBBase(EntryBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class EntryInDB(EntryInDBBase):
    pass

class Entry(EntryBase):
    id: int

    class Config:
        orm_mode = True