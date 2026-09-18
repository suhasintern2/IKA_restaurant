import pytesseract
from PIL import Image
import logging
import os
import platform

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_text_from_image(image_path: str) -> str:
    """
    Extract text from an image using Tesseract OCR.

    Args:
        image_path: Path to the image file

    Returns:
        str: Extracted raw text from the image

    Raises:
        Exception: If image cannot be processed or OCR fails
    """
    try:
        # Check if file exists
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")

        # Open and validate image
        with Image.open(image_path) as img:
            # Convert to RGB if necessary (for PNG with transparency, etc.)
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Extract text using Tesseract OCR
            # Using config options for better results with document-like images
            custom_config = r'--oem 3 --psm 6'
            extracted_text = pytesseract.image_to_string(img, config=custom_config)

            # Log the extraction for debugging
            logger.info(f"Extracted {len(extracted_text)} characters from {image_path}")

            return extracted_text.strip()

    except pytesseract.TesseractNotFoundError:
        logger.error("Tesseract OCR engine is not installed or not in your PATH")
        raise Exception(
            "Text extraction failed: Tesseract OCR engine is not installed or not in your PATH. "
            "Please install Tesseract OCR and ensure it's in your system PATH. "
            "On Ubuntu/Debian: sudo apt install tesseract-ocr "
            "On macOS: brew install tesseract "
            "On Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki"
        )
    except Exception as e:
        logger.error(f"OCR extraction failed for {image_path}: {str(e)}")
        raise Exception(f"Text extraction failed: {str(e)}")