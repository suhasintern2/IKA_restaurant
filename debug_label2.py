import sys
sys.path.insert(0, '/mnt/d/Vlookupprojects/IKA')

from app.extraction.ocr import extract_text_from_image
from app.models.ticket import _clean_value

def debug_label_values(lines):
    values: Dict[str, str] = {}
    aliases = {
        "restaurant": "restaurant", "branch": "restaurant", "phone": "phone",
        "date": "ticket_date", "terminal": "terminal", "table": "table_name",
        "department": "department", "user": "user_name", "staff": "user_name",
        "payment status": "payment_status", "payment": "payment_status",
        "credit card": "credit_card_amount", "ticket total": "ticket_total",
        "grand total": "grand_total", "charged": "charged",
    }
    print("First loop (colon/dash separated labels):")
    for line in lines:
        match = re.match(r"^\s*([A-Za-z][A-Za-z /_-]{1,30}?)\s*[:\-]\s*(.+?)\s*$", line)
        if not match:
            continue
        key = re.sub(r"\s+", " ", match.group(1)).strip().casefold()
        value = _clean_value(match.group(2))
        if key in aliases and value:
            values[aliases[key]] = value
            print(f"  Matched: key='{key}', value='{value}' -> {aliases[key]} = {value}")

    # Ticket screenshots often render a label row and its value row separately
    # (for example, "Payment Status" followed by "Paid"). Recover those
    # values without joining neighboring labels into one field.
    label_names = {
        "restaurant", "branch", "phone", "date", "terminal", "table",
        "department", "user", "staff", "payment status", "payment",
        "credit card", "ticket total", "grand total", "charged",
    }
    print("\nSecond loop (label on one line, value on next):")
    for index, line in enumerate(lines[:-1]):
        key = re.sub(r"\s+", " ", line).strip().casefold()
        print(f"  Checking line {index}: '{line}' -> key='{key}'")
        if key not in label_names:
            print(f"    -> key not in label_names, skipping")
            continue
        next_value = lines[index + 1]
        print(f"    next line {index+1}: '{next_value}'")
        if next_value.casefold() in label_names:
            print(f"    -> next value is also a label, skipping")
            continue
        alias = aliases.get(key)
        if alias and next_value:
            values.setdefault(alias, next_value)
            print(f"    -> set {alias} = {next_value}")
        else:
            if not alias:
                print(f"    -> no alias for key '{key}'")
            if not next_value:
                print(f"    -> next value is empty")
    return values

import re

def debug_ticket():
    image_path = "data/uploads/ticket_screenshots/ticket.png"
    extracted_text = extract_text_from_image(image_path)
    lines = [_clean_value(line) for line in extracted_text.splitlines() if _clean_value(line)]
    print("Lines:")
    for i, line in enumerate(lines):
        print(f"{i}: {line}")
    print("\nLabel values:")
    fields = debug_label_values(lines)
    for k, v in fields.items():
        print(f"  {k}: {v}")

if __name__ == "__main__":
    debug_ticket()