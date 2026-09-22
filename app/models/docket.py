import re
from typing import Any, Dict, List


ORDER_NO_RE = re.compile(
    r"\b(?:ORDER\s*NO|ORDER|NO)\s*[:#]?\s*(?:NO\s*[:#]?\s*)?(\d{1,6})\b",
    re.IGNORECASE,
)
DATE_RE = re.compile(
    r"\b(?:date|dated)\s*[:\-]?\s*([0-3]?\d[/-][01]?\d[/-](?:\d{2}|\d{4})|\d{4}[/-][01]?\d[/-][0-3]?\d)\b",
    re.IGNORECASE,
)
TIME_RE = re.compile(r"\b(?:time)\s*[:\-]?\s*(\d{1,2}:\d{2}(?:\s*[AP]M)?)\b", re.IGNORECASE)
MARKER_RE = re.compile(
    r"\*{0,2}\s*(VOID(?:ED)?|VO1D|OID|OTDRE|DISCOUNT|PROMO(?:TION)?)\s*\*{0,2}",
    re.IGNORECASE,
)
LABEL_RE = re.compile(r"^\s*([A-Za-z][A-Za-z0-9 /_-]{1,30}?)\s*[:\-]\s*(.+?)\s*$")


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip(" :-")


def _printed_lines(lines: List[str]) -> List[str]:
    """Identify lines that look like printed docket metadata or item content."""
    result = []
    for line in lines:
        if (
            ORDER_NO_RE.search(line)
            or DATE_RE.search(line)
            or TIME_RE.search(line)
            or MARKER_RE.search(line)
            or LABEL_RE.match(line)
            or re.search(r"\b(?:TAKE AWAY|RESTAURANT|TABLE|CATEGORY|BIRYANI|RICE)\b", line, re.IGNORECASE)
        ):
            result.append(line)
    return result


def _handwritten_reason(lines: List[str], printed: List[str]) -> str:
    """Return only a note written in the docket's table-number area.

    Printed OCR and handwriting cannot be separated reliably from text alone.
    The table-number label is the one stable anchor in the current docket
    layout, so unrelated OCR is left out instead of being mislabelled as a
    handwritten reason.
    """
    for line in lines:
        match = re.match(r"^\s*table(?:\s+no)?\s*[^:]*:\s*(.+?)\s*$", line, re.IGNORECASE)
        if not match:
            continue
        value = _clean(match.group(1))
        if value and not re.fullmatch(r"[\d\s.,:/-]+", value):
            return value
    return ""


def parse_docket_text(text: str) -> Dict[str, Any]:
    """Parse a docket image according to the master parsing prompt.
    Returns a dictionary with the following keys:
        type: "docket"
        docket_order_no: trailing order number only (e.g. "49") or None
        date: string or None
        time: string or None
        item: string or None
        discrepancy_type: "void" | "discount" | "promotion" or None
        handwritten_reason: string or None (handwriting only, never mixed with printed text)
        extra_fields: dict of unrecognized labeled text
    """
    lines = [_clean(line) for line in text.splitlines() if _clean(line)]

    # Initialize result with None for all fields
    result = {
        "type": "docket",
        "docket_order_no": None,
        "date": None,
        "time": None,
        "item": None,
        "discrepancy_type": None,
        "handwritten_reason": None,
        "extra_fields": {}
    }

    if not lines:
        return result

    # Extract order numbers
    order_numbers = [match.group(1) for match in ORDER_NO_RE.finditer(text)]
    unique_order_numbers = list(dict.fromkeys(order_numbers))
    if len(unique_order_numbers) == 1:
        result["docket_order_no"] = unique_order_numbers[0]

    # Extract date
    date_match = DATE_RE.search(text)
    if date_match:
        result["date"] = date_match.group(1)

    # Extract time
    time_match = TIME_RE.search(text)
    if time_match:
        result["time"] = time_match.group(1)

    # Extract discrepancy type from marker
    marker_matches = list(MARKER_RE.finditer(text))
    marker_line = None
    if marker_matches:
        marker = marker_matches[-1].group(1).casefold()
    else:
        for line in lines:
            if "otdre" in line.casefold() or re.search(r"\bo[i1]d\b", line, re.IGNORECASE):
                marker_line = line
                marker = "void"
                break
    if marker_matches or marker_line:
        if marker.startswith("void") or marker in {"vo1d", "oid", "otdre"}:
            result["discrepancy_type"] = "void"
        elif marker.startswith("discount"):
            result["discrepancy_type"] = "discount"
        elif marker.startswith("promo") or marker.startswith("promotion"):
            result["discrepancy_type"] = "promotion"

    # Extract item
    item = ""
    if marker_matches:
        # Try to get the line after the marker
        item_line = text[marker_matches[-1].end():].splitlines()[0] if marker_matches[-1].end() < len(text) else ""
        item = _clean(re.sub(r"^\s*\d+(?:\s+|$)", "", item_line))
    elif marker_line:
        item = _clean(re.sub(r".*?(?:otdre|o[i1]d)\W*", "", marker_line, flags=re.IGNORECASE)).strip("()[]{}*")
    if not item:
        # Fallback: look for a line in printed_lines that is not a label, date, or time
        printed = _printed_lines(lines)
        candidates = []
        for line in lines:
            if line in printed and not LABEL_RE.match(line) and not ORDER_NO_RE.search(line):
                if not DATE_RE.search(line) and not TIME_RE.search(line):
                    candidates.append(line)
        if candidates:
            # Score candidates: longer lines are better, also prefer lines with more words
            def score(line):
                # Length score
                length_score = len(line)
                # Word count score
                word_count = len(line.split())
                # Penalize lines that are too short (less than 3 chars) or have less than 2 words
                if len(line) < 3 or word_count < 2:
                    return -1000
                # Prefer lines that contain at least one alphabetic character
                if not any(c.isalpha() for c in line):
                    return -1000
                return length_score * 2 + word_count * 10  # arbitrary weights
            # Choose the candidate with the highest score
            item = max(candidates, key=score)

    result["item"] = item if item else None

    # Extract handwritten reason: lines not explained by printed docket grammar
    printed = _printed_lines(lines)
    result["handwritten_reason"] = _handwritten_reason(lines, printed)
    if result["handwritten_reason"] == "":
        result["handwritten_reason"] = None

    printed_lines = printed
    if result["handwritten_reason"]:
        printed_lines = [
            re.sub(re.escape(result["handwritten_reason"]), "", line, flags=re.IGNORECASE).strip()
            for line in printed
        ]
        printed_lines = [line for line in printed_lines if line]
    result["printed_text"] = "\n".join(printed_lines) if printed_lines else None

    # Extract extra fields: any labeled text not in the known labels
    known_labels = {"order", "order no", "order no.", "date", "dated", "time", "category"}
    for line in lines:
        match = LABEL_RE.match(line)
        if match:
            key = _clean(match.group(1))
            normalized = key.casefold()
            if normalized not in known_labels:
                value = _clean(match.group(2))
                if value:  # Only add non-empty values
                    result["extra_fields"][key] = value

    return result