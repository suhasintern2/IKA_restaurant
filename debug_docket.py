import sys
sys.path.insert(0, '/mnt/d/Vlookupprojects/IKA')

from app.extraction.ocr import extract_text_from_image
from app.models.docket import parse_docket_text

def debug_docket():
    image_path = "data/uploads/dockets/docket.jpeg"
    extracted_text = extract_text_from_image(image_path)
    print(f"Extracted text (first 200 chars): {extracted_text[:200]}")
    parsed = parse_docket_text(extracted_text)
    print("Parsed docket:")
    for key, value in parsed.items():
        print(f"  {key}: {value}")

if __name__ == "__main__":
    debug_docket()