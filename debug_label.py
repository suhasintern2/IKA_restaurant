import sys
sys.path.insert(0, '/mnt/d/Vlookupprojects/IKA')

from app.extraction.ocr import extract_text_from_image
from app.models.ticket import _clean_value, _label_values

def debug_ticket():
    image_path = "data/uploads/ticket_screenshots/ticket.png"
    extracted_text = extract_text_from_image(image_path)
    lines = [_clean_value(line) for line in extracted_text.splitlines() if _clean_value(line)]
    print("Lines:")
    for i, line in enumerate(lines):
        print(f"{i}: {line}")
    print("\nLabel values:")
    fields = _label_values(lines)
    for k, v in fields.items():
        print(f"  {k}: {v}")

if __name__ == "__main__":
    debug_ticket()