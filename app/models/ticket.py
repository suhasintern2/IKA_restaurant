import re
from typing import Any, Dict, List, Optional


TICKET_ID_RE = re.compile(r"#?\s*(\d{6})\s*[-–]\s*(\d+)", re.IGNORECASE)
MONEY_RE = re.compile(r"\b\d+[.,]\d{2}\b")
LABEL_RE = re.compile(r"^\s*([A-Za-z][A-Za-z /_-]{1,30}?)\s*[:\-]\s*(.+?)\s*$")


def _clean_value(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip(" :-")


def _amount(value: str) -> str:
    return value.replace(",", ".")


def _ticket_id(text: str) -> Optional[str]:
    match = TICKET_ID_RE.search(text)
    if not match:
        return None
    return f"{match.group(1)}-{match.group(2)}"


def _label_values(lines: List[str]) -> Dict[str, str]:
    values: Dict[str, str] = {}
    aliases = {
        "restaurant": "restaurant", "branch": "restaurant", "phone": "phone",
        "date": "ticket_date", "terminal": "terminal", "table": "table_name",
        "department": "department", "user": "user_name", "staff": "user_name",
        "payment status": "payment_status", "payment": "payment_status",
        "credit card": "credit_card_amount", "ticket total": "ticket_total",
        "grand total": "grand_total", "charged": "charged",
    }
    for line in lines:
        match = re.match(r"^\s*([A-Za-z][A-Za-z /_-]{1,30}?)\s*[:\-]\s*(.+?)\s*$", line)
        if not match:
            continue
        key = re.sub(r"\s+", " ", match.group(1)).strip().casefold()
        value = _clean_value(match.group(2))
        if key in aliases and value:
            values[aliases[key]] = value

    # Ticket screenshots often render a label row and its value row separately
    # (for example, "Payment Status" followed by "Paid"). Recover those
    # values without joining neighboring labels into one field.
    label_names = {
        "restaurant", "branch", "phone", "date", "terminal", "table",
        "department", "user", "staff", "payment status", "payment",
        "credit card", "ticket total", "grand total", "charged",
    }
    for index, line in enumerate(lines[:-1]):
        key = re.sub(r"\s+", " ", line).strip().casefold()
        if key not in label_names or key in {"date", "terminal", "table", "department", "user", "staff"}:
            continue
        next_value = lines[index + 1]
        if next_value.casefold() in label_names:
            continue
        alias = aliases.get(key)
        if alias and next_value:
            values.setdefault(alias, next_value)

    joined = " ".join(lines)
    date_match = re.search(r"\b([0-3]?\d[/-][01]?\d[/-]\d{2,4})\b", joined)
    if date_match:
        values.setdefault("ticket_date", date_match.group(1))
    terminal_match = re.search(r"\b(Till[- ]?\d+|POS[- ]?\d+)\b", joined, re.IGNORECASE)
    if terminal_match:
        values.setdefault("terminal", terminal_match.group(1))
    phone_match = re.search(r"\b(0?\d{9,12})\b", joined)
    if phone_match:
        values.setdefault("phone", phone_match.group(1))

    for line in lines:
        upper = line.upper()
        if upper.startswith("TAKE AWAY") or upper.startswith("RESTAURANT"):
            values.setdefault("department", line.split()[0] if upper.startswith("RESTAURANT") else "TAKE AWAY")
            remainder = re.sub(r"^(TAKE AWAY|RESTAURANT)\b", "", line, flags=re.IGNORECASE).strip()
            if remainder and "user_name" not in values:
                values["user_name"] = remainder
        if re.fullmatch(r"PAID|UNPAID|PENDING|CASH|CARD", line, re.IGNORECASE):
            values.setdefault("payment_status", line)

    for label, field in (("credit card", "credit_card_amount"), ("ticket total", "ticket_total"), ("grand total", "grand_total"), ("charged", "charged")):
        match = re.search(rf"{label}\s*:?[^\n]*?(£?\s*\d+[.,]\d{{2}})", "\n".join(lines), flags=re.IGNORECASE)
        if match:
            values[field] = match.group(1).strip()

    # Additional enhancements for missing fields
    # Extract restaurant from the first few lines that is not a ticket line and not a label line
    if not values.get("restaurant") and lines:
        for i in range(min(5, len(lines))):
            line = lines[i]
            # Skip if it looks like a ticket number (with hyphen pattern)
            if re.search(r"#?\d{6}\s*[-–]\s*\d+", line, re.IGNORECASE):
                continue
            # Skip if it looks like a label with colon/dash
            if LABEL_RE.match(line):
                continue
            # If it contains letters, set as restaurant
            if re.search(r"[a-zA-Z]", line):
                values["restaurant"] = line
                break

    # Extract table number and department from lines that contain a number followed by a word (like "12 RESTAURANT")
    for line in lines:
        # Look for pattern: number(s) followed by space(s) followed by word(s)
        match = re.search(r"^(\d+)\s+([A-Za-z][A-Za-z\s]*)$", line)
        if match:
            table_num = match.group(1)
            dept = match.group(2).strip()
            # Only set if we haven't already got a better value
            if not values.get("table_name"):
                values["table_name"] = table_num
            # Only set department if it looks like a department name and we don't have one yet
            if not values.get("department") and dept.upper() in ["RESTAURANT", "TAKE AWAY", "BAR", "LOUNGE"]:
                values["department"] = dept

    # Extract user and payment status from lines that have two words (like "FARAZ Paid")
    # Known label words to avoid misclassification
    known_label_words = {"date", "terminal", "table", "department", "user", "staff", "payment", "ticket", "total", "grand", "charged", "credit", "card", "items"}
    for line in lines:
        # Look for pattern: word(s) space word(s)
        match = re.search(r"^([A-Za-z][A-Za-z\s]*)\s+([A-Za-z][A-Za-z\s]*)$", line)
        if match:
            part1 = match.group(1).strip()
            part2 = match.group(2).strip()
            # Skip if either part is a known label word (to avoid misclassifying label lines)
            if part1.lower() in known_label_words or part2.lower() in known_label_words:
                continue
            # Check if part2 is a payment status
            if part2.upper() in ["PAID", "UNPAID", "PENDING", "CASH", "CARD"]:
                if not values.get("payment_status"):
                    values["payment_status"] = part2
                # The other part might be the user
                if not values.get("user_name") and part1:
                    values["user_name"] = part1
            # Check if part1 is a user name (heuristic: if it's all letters and not too long)
            elif not values.get("user_name") and part1.isalpha() and len(part1) < 20:
                values["user_name"] = part1
                if not values.get("payment_status") and part2.upper() in ["PAID", "UNPAID", "PENDING", "CASH", "CARD"]:
                    values["payment_status"] = part2

    return values


def _parse_item(line: str, category: str = "") -> Optional[Dict[str, Any]]:
    if not MONEY_RE.search(line) or re.search(
        r"\b(ticket total|grand total|charged|subtotal|vat|tax|payment|credit card)\b",
        line,
        re.IGNORECASE,
    ):
        return None

    is_void = bool(re.search(r"\(\s*void\s*\)|\bvoid(?:ed)?\b", line, re.IGNORECASE))
    cleaned = re.sub(r"\(\s*void\s*\)|\bvoid(?:ed)?\b", "", line, flags=re.IGNORECASE)
    amounts = MONEY_RE.findall(cleaned)
    if not amounts:
        return None

    quantity_match = re.search(r"(?:^|\s)(\d+(?:\.\d+)?)\s*[xX]\s*", cleaned)
    if quantity_match:
        quantity = quantity_match.group(1)
        unit_price = _amount(amounts[0])
        total = _amount(amounts[-1])
        name = cleaned[:quantity_match.start()].strip(" -:|")
    else:
        numbers_start = re.search(r"\d+[.,]\d{2}", cleaned)
        if not numbers_start:
            return None
        prefix = cleaned[:numbers_start.start()].strip(" -:|")
        quantity_match = re.search(r"\b(\d+(?:\.\d+)?)\s*$", prefix)
        quantity = quantity_match.group(1) if quantity_match else "1"
        name = prefix[:quantity_match.start()].strip(" -:|") if quantity_match else prefix
        unit_price = _amount(amounts[-2] if len(amounts) >= 2 else amounts[0])
        total = _amount(amounts[-1])

    if not name or len(name) < 2 or re.fullmatch(r"[\d\s.,:/-]+", name):
        return None
    return {
        "name": _clean_value(name),
        "category": category or None,
        "quantity": quantity,
        "unit_price": unit_price,
        "total": total,
        "is_void": is_void,
    }


def _original_parse_ticket_screenshot(text: str) -> Dict[str, Any]:
    """Original parse_ticket_screenshot function from the backup."""
    lines = [_clean_value(line) for line in text.splitlines() if _clean_value(line)]
    ticket_id = _ticket_id(text)
    fields = _label_values(lines)
    if not fields.get("restaurant") and lines:
        first = lines[0]
        if not re.search(r"#?\d{6}\s*[-–]\s*\d+", first, re.IGNORECASE):
            fields["restaurant"] = first

    known_keys = {
        "restaurant", "phone", "ticket_date", "terminal", "table_name", "department",
        "user_name", "payment_status", "credit_card_amount", "ticket_total",
        "grand_total", "charged",
    }
    extra_fields: Dict[str, str] = {}
    for line in lines:
        match = re.match(r"^\s*([A-Za-z][A-Za-z /_-]{1,30}?)\s*[:\-]\s*(.+?)\s*$", line)
        if match:
            key = _clean_value(match.group(1))
            normalized = key.casefold()
            if normalized not in {"restaurant", "branch", "phone", "date", "terminal", "table", "department", "user", "staff", "payment", "payment status", "credit card", "ticket total", "grand total", "charged"}:
                extra_fields[key] = _clean_value(match.group(2))

    items = []
    category = ""
    in_items = False
    for line in lines:
        if re.fullmatch(r"items?", line, re.IGNORECASE):
            in_items = True
            continue
        if in_items and re.search(r"ticket total|grand total|charged|payment status", line, re.IGNORECASE):
            in_items = False
        if in_items and re.fullmatch(r"item category price qty total", line, re.IGNORECASE):
            continue
        if (
            re.search(r"[A-Za-z]", line)
            and not MONEY_RE.search(line)
            and not LABEL_RE.match(line)
            and not re.search(r"ticket|total|payment|charged|date|time|terminal|table|department|user|staff", line, re.IGNORECASE)
        ):
            category = _clean_value(line)
        item = _parse_item(line, category)
        if item:
            items.append(item)
        elif in_items and re.search(r"[A-Za-z]", line) and len(line) > 2:
            item_name = re.sub(r"[^A-Za-z0-9 '&/().-]", "", line).strip()
            if item_name and not re.search(r"item|category|price|qty|total|void", item_name, re.IGNORECASE):
                items.append({
                    "name": item_name,
                    "category": category or None,
                    "quantity": None,
                    "unit_price": None,
                    "total": None,
                    "is_void": bool(re.search(r"void|veid|weid", line, re.IGNORECASE)),
                })

    return {
        "ticket_id": ticket_id,
        "ticket_id_display": f"#{ticket_id}" if ticket_id else None,
        **{key: fields.get(key) for key in known_keys},
        "extra_fields": extra_fields,
        "items": items,
    }


def parse_ticket_screenshot(text: str) -> Dict[str, Any]:
    """Parse a ticket screenshot according to the master parsing prompt.
    Returns a dictionary with the following keys:
        type: "ticket"
        ticket_number: full string with hyphen (e.g. "260920-143") or None
        restaurant: string or None
        date: string or None
        terminal: string or None
        table: string or None
        department: string or None
        user: string or None
        payment_status: string or None
        credit_card_amount: string or None
        items: list of dicts with keys: name, category, price, qty, total, is_void (all strings or None, is_void boolean)
        ticket_total: string or None
        grand_total: string or None
        charged: string or None
        extra_fields: dict of unrecognized labeled text
    """
    # First, get the original parsing result
    original = _original_parse_ticket_screenshot(text)

    # Initialize result with None for all fields
    result = {
        "type": "ticket",
        "ticket_number": None,
        "restaurant": None,
        "date": None,
        "terminal": None,
        "table": None,
        "department": None,
        "user": None,
        "payment_status": None,
        "credit_card_amount": None,
        "items": [],
        "ticket_total": None,
        "grand_total": None,
        "charged": None,
        "extra_fields": {}
    }

    if not text:
        return result

    # Map ticket_number from original's ticket_id (which is already in YYMMDD-N format)
    ticket_id = original.get("ticket_id")
    if ticket_id:
        result["ticket_number"] = ticket_id

    # Map other known fields
    result["restaurant"] = original.get("restaurant")
    result["date"] = original.get("ticket_date")
    result["terminal"] = original.get("terminal")
    result["table"] = original.get("table_name")
    result["department"] = original.get("department")
    result["user"] = original.get("user_name")
    result["payment_status"] = original.get("payment_status")
    result["credit_card_amount"] = original.get("credit_card_amount")
    result["ticket_total"] = original.get("ticket_total")
    result["grand_total"] = original.get("grand_total")
    result["charged"] = original.get("charged")

    # Convert items to master prompt format
    original_items = original.get("items", [])
    master_items = []
    for item in original_items:
        master_item = {
            "name": item.get("name"),
            "category": item.get("category"),
            "price": item.get("unit_price"),
            "qty": item.get("quantity"),
            "total": item.get("total"),
            "is_void": item.get("is_void", False)
        }
        master_items.append(master_item)
    result["items"] = master_items

    # Build extra_fields: start with original's extra_fields, then add any other keys from original that are not in the known set
    extra_fields = original.get("extra_fields", {}).copy()
    # Define the set of keys that are already used in the result (excluding extra_fields and items)
    used_keys = {
        "ticket_id", "ticket_id_display", "restaurant", "phone", "ticket_date", "terminal", "table_name",
        "department", "user_name", "payment_status", "credit_card_amount", "ticket_total", "grand_total", "charged"
    }
    for key, value in original.items():
        if key not in used_keys and key not in extra_fields:
            # Avoid adding nested structures like items or extra_fields again
            if key not in ["items", "extra_fields"]:
                extra_fields[key] = value
    result["extra_fields"] = extra_fields

    return result