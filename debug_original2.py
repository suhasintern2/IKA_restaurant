import sys
sys.path.insert(0, '/mnt/d/Vlookupprojects/IKA')

from app.extraction.ocr import extract_text_from_image
from app.models.ticket import _original_parse_ticket_screenshot

def debug_ticket():
    image_path = "data/uploads/ticket_screenshots/ticket.png"
    extracted_text = extract_text_from_image(image_path)
    print(f"Extracted text (first 200 chars): {extracted_text[:200]}")
    original = _original_parse_ticket_screenshot(extracted_text)
    print("Original parse result:")
    for key, value in original.items():
        if key == "items":
            print(f"  {key}: [{len(value)} items]")
            for i, item in enumerate(value[:3]):
                print(f"    Item {i}: {item}")
        else:
            print(f"  {key}: {value}")

if __name__ == "__main__":
    debug_ticket()