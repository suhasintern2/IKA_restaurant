import sys
sys.path.insert(0, '/mnt/d/Vlookupprojects/IKA')

from app.extraction.ocr import extract_text_from_image
from app.models.ticket import parse_ticket_screenshot
from app.models.docket import parse_docket_text

def test_ticket():
    image_path = "data/uploads/ticket_screenshots/ticket.png"
    print(f"Testing ticket image: {image_path}")
    try:
        extracted_text = extract_text_from_image(image_path)
        print(f"Extracted text (first 200 chars): {extracted_text[:200]}")
        parsed = parse_ticket_screenshot(extracted_text)
        print("Parsed ticket:")
        for key, value in parsed.items():
            if key == "items":
                print(f"  {key}: [{len(value)} items]")
                for i, item in enumerate(value[:3]):  # show first 3 items
                    print(f"    Item {i}: {item}")
                if len(value) > 3:
                    print(f"    ... and {len(value)-3} more")
            else:
                print(f"  {key}: {value}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def test_docket():
    image_path = "data/uploads/dockets/docket.jpeg"
    print(f"\nTesting docket image: {image_path}")
    try:
        extracted_text = extract_text_from_image(image_path)
        print(f"Extracted text (first 200 chars): {extracted_text[:200]}")
        parsed = parse_docket_text(extracted_text)
        print("Parsed docket:")
        for key, value in parsed.items():
            print(f"  {key}: {value}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ticket()
    test_docket()