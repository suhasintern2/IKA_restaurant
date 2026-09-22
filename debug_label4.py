import sys
sys.path.insert(0, '/mnt/d/Vlookupprojects/IKA')

from app.extraction.ocr import extract_text_from_image
from app.models.ticket import _clean_value

def debug_label_values(lines):
    label_names = {
        "restaurant", "branch", "phone", "date", "terminal", "table",
        "department", "user", "staff", "payment status", "payment",
        "credit card", "ticket total", "grand total", "charged",
    }
    print("First loop (colon/dash separated labels):")
    for line in lines:
        match = re.match(r"^\s*([A-Za-z][A-Za-z /_-]{1,30}?)\s*[:\-]\s*(.+?)\s*$", line)
        if not match:
            continue
        key = _clean_value(match.group(1)).strip().casefold()
        value = _clean_value(match.group(2)).strip()
        print(f"  Line: '{line}' -> key='{key}', value='{value}'")
        if key in label_names:
            print(f"    -> key is in label_names")
        else:
            print(f"    -> key NOT in label_names")

    print("\nSecond loop (label on one line, value on next):")
    for index, line in enumerate(lines[:-1]):
        key = _clean_value(line).strip().casefold()
        print(f"  Line {index}: '{line}' -> key='{key}'")
        if key in label_names:
            print(f"    -> key is in label_names")
            next_value = _clean_value(lines[index + 1]).strip()
            print(f"    -> next line {index+1}: '{lines[index+1]}' -> cleaned next_value='{next_value}'")
            if next_value and next_value.casefold() not in label_names:
                print(f"    -> next value is not a label, so we would set {key} = {next_value}")
            else:
                print(f"    -> next value is empty or is a label, skipping")
        else:
            print(f"    -> key NOT in label_names, skipping")

import re

def debug_ticket():
    image_path = "data/uploads/ticket_screenshots/ticket.png"
    extracted_text = extract_text_from_image(image_path)
    lines = [_clean_value(line) for line in extracted_text.splitlines() if _clean_value(line)]
    print("Lines:")
    for i, line in enumerate(lines):
        print(f"{i}: {line}")
    print("\n--- Debugging _label_values ---")
    debug_label_values(lines)

if __name__ == "__main__":
    debug_ticket()