import sys
sys.path.insert(0, '/mnt/d/Vlookupprojects/IKA')

from app.extraction.ocr import extract_text_from_image
from app.models.ticket import _label_values, _original_parse_ticket_screenshot

def compare():
    image_path = "data/uploads/ticket_screenshots/ticket.png"
    extracted_text = extract_text_from_image(image_path)
    lines = [_clean_value(line) for line in extracted_text.splitlines() if _clean_value(line)]

    print("Calling _label_values directly:")
    fields = _label_values(lines)
    for k in sorted(fields.keys()):
        print(f"  {k}: {fields[k]}")

    print("\nCalling _original_parse_ticket_screenshot:")
    original = _original_parse_ticket_screenshot(extracted_text)
    for k in sorted(original.keys()):
        if k not in ["items", "extra_fields"]:
            print(f"  {k}: {original[k]}")

def _clean_value(value: str) -> str:
    import re
    return re.sub(r"\s+", " ", value).strip(" :-")

if __name__ == "__main__":
    compare()