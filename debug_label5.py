import sys
sys.path.insert(0, '/mnt/d/Vlookupprojects/IKA')

from app.extraction.ocr import extract_text_from_image
import re

def _clean_value(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip(" :-")

def debug_label_values(lines):
    print("=== Debugging _label_values ===")
    all_labels: Dict[str, str] = {}
    # First, get colon/dash separated labels
    print("\nFirst loop (colon/dash separated labels):")
    for line in lines:
        match = re.match(r"^\s*([A-Za-z][A-Za-z /_-]{1,30}?)\s*[:\-]\s*(.+?)\s*$", line)
        if not match:
            continue
        key = _clean_value(match.group(1)).strip().casefold()
        value = _clean_value(match.group(2)).strip()
        print(f"  Line: '{line}' -> key='{key}', value='{value}'")
        if key and value:
            all_labels[key] = value
            print(f"    -> added to all_labels: {key} = {value}")

    # Second, get label on one line, value on the next (for labels that are exactly in label_names)
    label_names = {
        "restaurant", "branch", "phone", "date", "terminal", "table",
        "department", "user", "staff", "payment status", "payment",
        "credit card", "ticket total", "grand total", "charged",
    }
    print("\nSecond loop (label on one line, value on next):")
    for index, line in enumerate(lines[:-1]):
        key = _clean_value(line).strip().casefold()
        print(f"  Line {index}: '{line}' -> key='{key}'")
        if key in label_names:
            print(f"    -> key is in label_names")
            next_value = _clean_value(lines[index + 1]).strip()
            print(f"    -> next line {index+1}: '{lines[index+1]}' -> cleaned next_value='{next_value}'")
            if next_value and next_value.casefold() not in label_names:
                all_labels[key] = next_value
                print(f"    -> added to all_labels: {key} = {next_value}")
            else:
                print(f"    -> next value is empty or is a label, skipping")
        else:
            print(f"    -> key NOT in label_names, skipping")
    return all_labels

def debug_ticket():
    image_path = "data/uploads/ticket_screenshots/ticket.png"
    extracted_text = extract_text_from_image(image_path)
    lines = [_clean_value(line) for line in extracted_text.splitlines() if _clean_value(line)]
    print("Lines:")
    for i, line in enumerate(lines):
        print(f"{i}: {line}")
    fields = debug_label_values(lines)
    print("\nFinal all_labels:")
    for k, v in fields.items():
        print(f"  {k}: {v}")

if __name__ == "__main__":
    debug_ticket()