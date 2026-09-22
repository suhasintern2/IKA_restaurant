import logging
import os

import pytesseract
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

# Tesseract config. --psm 6 (uniform block) keeps each bill line on its own
# OCR line, which is essential for line-oriented block segmentation.
OCR_CONFIG = "--oem 3 --psm 6"


def _preprocess(image: Image.Image) -> Image.Image:
    """Clean up a phone photo before OCR: grayscale, contrast, upscale, orient."""
    image = image.convert("L")

    # Upscale small/dim phone photos so Tesseract sees sharper glyph shapes.
    width, height = image.size
    if max(width, height) < 1400:
        scale = 2
        image = image.resize((width * scale, height * scale), Image.LANCZOS)

    # Stretch contrast so faint thermal/screen prints become readable.
    image = ImageOps.autocontrast(image, cutoff=1)

    return _deskew(image)


def _deskew(image: Image.Image) -> Image.Image:
    """Correct 90/180/270 phone rotation via Tesseract OSD.

    Micro-skew is handled internally by Tesseract; only gross rotation is
    corrected here. Rotation is applied only when OSD is reasonably confident
    (>= 5.0): dense numeric tables (income reports, receipts full of amounts)
    spuriously report 180° with low confidence and rotating them garbles OCR.
    """
    try:
        osd = pytesseract.image_to_osd(image, config="--oem 3 --psm 0")
        angle = 0
        confidence = 0.0
        for line in osd.splitlines():
            if line.startswith("Rotate:"):
                angle = int(line.split(":", 1)[1].strip())
            elif line.startswith("Orientation confidence:"):
                confidence = float(line.split(":", 1)[1].strip())
        if angle and confidence >= 5.0:
            logger.info("%s rotation detected (confidence %.2f) - rotating", angle, confidence)
            return image.rotate(angle, expand=True, fillcolor=255)
    except pytesseract.TesseractError:
        pass
    except Exception as e:  # noqa: BLE001 - OSD is best-effort
        logger.warning("OSD orientation detection failed: %s", e)
    return image


def extract_text_from_image(image_path: str) -> str:
    """
    Extract text from an image using Tesseract OCR.
    Phone-photo cleanup (grayscale, contrast, upscale, orientation) runs first.

    Args:
        image_path: Path to the image file

    Returns:
        str: Extracted raw text from the image

    Raises:
        Exception: If image cannot be processed or OCR fails
    """
    try:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")

        with Image.open(image_path) as img:
            if img.mode != "RGB":
                img = img.convert("RGB")
            img = _preprocess(img)
            extracted_text = pytesseract.image_to_string(img, config=OCR_CONFIG)

            logger.info("Extracted %d characters from %s", len(extracted_text), image_path)
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
        logger.error("OCR extraction failed for %s: %s", image_path, str(e))
        raise Exception(f"Text extraction failed: {str(e)}")