import re
import json
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

from app.models.segmentation import segment_text

def parse_extracted_text(extracted_text: str) -> dict:
    """
    Parse raw extracted text from OCR to identify structured fields.
    Enhanced to be more reliable and schema-flexible.

    Args:
        extracted_text: Raw text from OCR

    Returns:
        dict: Contains parsed fields (restaurant, ticket_number, discrepancy_type, description)
              plus extra_fields for unexpected bill fields
              Blocks (structured line items / discrepancies / totals / payment) are
              added under ``blocks``, ``line_items`` and ``discrepancies``.
              Missing fields will be None or empty strings
    """
    # Initialize result with default/empty values
    result = {
        "restaurant": "",  # Will be extracted from text when possible
        "ticket_number": "",
        "discrepancy_type": "",
        "description": "",  # Will be empty -> status = needs_description if no description found
        "extra_fields": {}  # For capturing unexpected bill fields like Table, Staff, etc.
    }

    if not extracted_text:
        return result

    # Split text into lines for processing
    lines = [line.strip() for line in extracted_text.split('\n') if line.strip()]
    if not lines:
        return result

    # Convert to lowercase for case-insensitive matching
    text_lower = extracted_text.lower()

    # 1. Extract restaurant name (look at first 1-3 lines for likely restaurant names)
    # Restaurant names are often at the top and contain letters, possibly with punctuation
    for i in range(min(3, len(lines))):
        line = lines[i]
        # Skip lines that are mostly numbers or look like addresses/dates
        if line and not re.match(r'^[\d\s\-.,/:]+$', line) and len(line) > 2:
            # Likely a restaurant name if it has mostly letters and common restaurant words
            if re.search(r'[a-zA-Z]', line) and len(line) < 50:  # Reasonable length for restaurant name
                result["restaurant"] = line
                break

    # 2. Extract ticket number with multiple patterns and context awareness
    # Try multiple patterns for ticket numbers
    ticket_patterns = [
        r'\b\d{6,}\b',  # Original: 6+ digits
        r'(?:ticket|#|no\.?|number)[\s#:]*(\d{4,})',  # Contextual: Ticket #: 1234
        r'(?:[\s#:])(\d{4,})(?=[\s#:])',  # Surrounded by spaces/#/:
        r'(\d{4,})\s*[-–]\s*\d{4,}',  # Range format: 1234-5678 (take first)
    ]

    for pattern in ticket_patterns:
        ticket_match = re.search(pattern, extracted_text, re.IGNORECASE)
        if ticket_match:
            # Extract the ticket number from the appropriate group
            if pattern == r'\b\d{6,}\b':
                result["ticket_number"] = ticket_match.group()
            elif pattern in [r'(?:ticket|#|no\.?|number)[\s#:]*(\d{4,})',
                           r'(?:[\s#:])(\d{4,})(?=[\s#:])',
                           r'(\d{4,})\s*[-–]\s*\d{4,}']:
                result["ticket_number"] = ticket_match.group(1)
            else:
                result["ticket_number"] = ticket_match.group()

            # Validate it looks like a ticket number (reasonable length)
            if len(result["ticket_number"]) >= 4:
                break

    # If still no ticket number, fall back to original method
    if not result["ticket_number"]:
        ticket_match = re.search(r'\b\d{6,}\b', extracted_text)
        if ticket_match:
            result["ticket_number"] = ticket_match.group()

    # 3. Extract discrepancy type (improved)
    discrepancy_keywords = {
        "void": ["void", "voided"],
        "discount": ["discount", "disc", "discounted"],
        "promotion": ["promotion", "promo", "promotional", "offer", "deal", "special"]
    }

    for disc_type, keywords in discrepancy_keywords.items():
        for keyword in keywords:
            # Use word boundaries to avoid partial matches
            if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
                result["discrepancy_type"] = disc_type
                break
        if result["discrepancy_type"]:
            break

    # 4. Extract description (attempt to find descriptive content)
    # Look for paragraphs or sections that seem descriptive
    # Skip header-like lines and look for meaningful content
    description_lines = []
    skip_patterns = [
        r'(?i)^(ticket|#|no\.?|number)',  # Ticket headers
        r'(?i)^(date|time)',  # Date/time
        r'(?i)^(table|server|staff|cashier)',  # Service info
        r'(?i)^(subtotal|total|tax|amount|\$)',  # Money amounts
        r'(?i)^(thank you|please come again)',  # Footers
        r'^\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}',  # Dates
        r'^\d{1,2}:\d{2}',  # Times
        r'^[\d\s\-.:]+$',  # Just numbers and separators
    ]

    for line in lines:
        # Skip lines that match skip patterns
        should_skip = False
        for pattern in skip_patterns:
            if re.search(pattern, line):
                should_skip = True
                break

        if not should_skip and len(line) > 10:  # Meaningful length for description
            description_lines.append(line)

    # Join description lines, but limit to reasonable length
    if description_lines:
        result["description"] = ' '.join(description_lines)[:500]  # Limit length

    # 5. Extract extra fields (key-value pairs that might be on the bill)
    # Look for patterns like "Field: Value" or "Field Value"
    extra_field_patterns = [
        r'(?:^|\n)([A-Za-z\s]+?):\s*([^\n]+)',  # Field: Value
        r'(?:^|\n)([A-Za-z\s]+?)\s{2,}([^\n]+)',  # Field    Value (multiple spaces)
    ]

    for pattern in extra_field_patterns:
        matches = re.findall(pattern, extracted_text, re.MULTILINE)
        for match in matches:
            key, value = match[0].strip(), match[1].strip()
            # Filter out keys we already capture or that are too generic
            if key.lower() not in ['ticket', 'number', 'date', 'time', 'total', 'amount',
                                 'subtotal', 'tax', 'description', 'restaurant'] and len(key) > 1:
                # Avoid capturing very long values that are likely not fields
                if len(value) < 100 and len(key) < 30:
                    result["extra_fields"][key] = value

    # 6. Block segmentation: structured line items, discrepancies, totals,
    #    payment and metadata. The discrepancy type comes from the line-item
    #    markers ONLY (never from summary lines like "Voids Total").
    blocks = segment_text(extracted_text)
    result["blocks"] = blocks
    result["line_items"] = blocks["line_items"]
    result["discrepancies"] = blocks["discrepancies"]

    if blocks["discrepancies"]:
        types = sorted({d["type"] for d in blocks["discrepancies"] if d["type"] != "unknown"})
        if types:
            result["discrepancy_type"] = ", ".join(types)

    return result

class EntryBase(BaseModel):
    restaurant: str  # One of 3 restaurants
    ticket_number: str  # Extracted or entered
    discrepancy_type: str  # void, discount, or promotion
    extracted_text: str  # Raw OCR text
    description: Optional[str] = None  # User-provided description
    status: str  # matched, needs_description, needs_ticket_number, needs_restaurant, needs_discrepancy_type, needs_review
    extra_fields: Optional[Dict[str, Any]] = None  # Extra bill fields captured from OCR
    blocks: Optional[Dict[str, Any]] = None  # Structured segmentation of the bill
    image_filename: Optional[str] = None  # Stored image filename for reference

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
        from_attributes = True

class EntryInDB(EntryInDBBase):
    pass

class Entry(EntryBase):
    id: int

    class Config:
        from_attributes = True