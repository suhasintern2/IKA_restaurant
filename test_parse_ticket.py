import sys
sys.path.insert(0, '/mnt/d/Vlookupprojects/IKA')

from app.extraction.ocr import extract_text_from_image
from app.models.ticket import parse_ticket_screenshot

def test():
    image_path = "data/uploads/ticket_screenshots/ticket.png"
    extracted_text = extract_text_from_image(image_path)
    result = parse_ticket_screenshot(extracted_text)
    print("Parse ticket screenshot result:")
    for key, value in result.items():
        if key == "items":
            print(f"  {key}: [{len(value)} items]")
            for i, item in enumerate(value):
                print(f"    Item {i}: {item}")
        else:
            print(f"  {key}: {value}")

if __name__ == "__main__":
    test()