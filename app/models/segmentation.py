"""Block segmentation for bill text.

Turns one flat OCR blob into structured blocks:

    header        restaurant/address/contact lines
    metadata      date, time, table, staff, terminal, ...
    line_items    [{name, quantity, unit_price, line_total, raw, ...}]
    discrepancies [void/discount/promotion marker bound to an item index]
    totals        subtotal, tax, total plus summary totals (voids, discounts...)
    payment       method, card_type, card_last4

Every value-normalization / OCR-misread fix is recorded under
``corrections`` so nothing is silently "corrected".
"""

import re

# --- Classification patterns -------------------------------------------------

CURRENCY = r"[$£€]"
# First group must be 3+ digits so decimal prices like "14.00" are NOT phones,
# while "020 7123 4567" / "117.945 6789" still are.
PHONE_RE = re.compile(r"\d{3,}[\s.\-]\d{3,}(?:[\s.\-]\d{2,4})?")
MONEY_TOKEN_RE = re.compile(rf"{CURRENCY}?\s*-?\s*(\d[\d.,]*)")
DATE_RE = re.compile(r"\d{1,2}[/.\-]\d{1,2}[/.\-]\d{2,4}")
TIME_RE = re.compile(r"\d{1,2}:\d{2}")
ADDRESS_START_RE = re.compile(r"^\d{1,3}[,\s]\s*[A-Z]")
QTY_X_RE = re.compile(r"(?<![\d.])(\d{1,4})\s*[xX×*]\s*")

METADATA_KEYS = ["date", "time", "table", "staff", "server", "cashier", "terminal", "waiter"]

DISCREPANCY_KEYWORDS = {
    "void": ["void", "voided"],
    "discount": ["discount", "disc", "discounted"],
    "promotion": ["promotion", "promo", "promotional", "offer", "promo deal"],
}

TOTAL_KEYWORDS = [
    "subtotal", "sub total", "grand total", "balance",
]
SUMMARY_TOTALS = [
    "voids total", "voids today", "discounts total", "promotions total",
    "cancelled total", "gifts total",
]
PAYMENT_KEYWORDS = ["payment method", "card type", "card no", "visa", "mastercard", "amex"]
FOOTER_KEYWORDS = ["thank you", "please come", "please visit", "come back", "have a great"]

SEPARATOR_RE = re.compile(r"^[\s\-—_=•·*+.|'\"`~/#\\]+$")
ITEM_HEADER_RE = re.compile(r"(?i)(item|qty\s|quantity|description)\s*[:\-]?|price\s*\(\s*[€$£]")
METADATA_SCAN_RE = re.compile(
    r"(?i)(?<![a-z])(date|time|table|staff|server|cashier|terminal|waiter)\s*[:\-=|;]{1,3}\s*(.*)$"
)
MARKER_RE = re.compile(
    r"(?i)(void\b|voided\b|discount\b|disc\b|discounted\b|promotion\b|promo\b|promotional\b)"
)
SUMMARY_TOTAL_RE = re.compile(r"(?i)(" + "|".join(SUMMARY_TOTALS) + ")")
# "total" must also match after OCR junk digits ("6Total") but not inside
# "Subtotal" — hence the lookbehind instead of \b.
TOTAL_LINE_RE = re.compile(
    r"(?i)(sub\s*total|grand\s*total|(?<![a-z])total\b|\btax\b|\bvat\b|\bbalance\b)"
)
PAYMENT_LINE_RE = re.compile(r"(?i)(" + "|".join(PAYMENT_KEYWORDS) + ")")
FOOTER_LINE_RE = re.compile(r"(?i)(" + "|".join(FOOTER_KEYWORDS) + ")")
CARD_LAST4_RE = re.compile(r"\d{4}")

# --- OCR value correction (auditable) ----------------------------------------

# Reliable single-char OCR misreads, applied only inside numbers.
DIGIT_SUBSTITUTIONS = {
    "O": "0", "o": "0", "Q": "0", "q": "0",
    "l": "1", "I": "1", "i": "1", "L": "1",
    "Z": "2", "z": "2",
    "S": "5", "s": "5",
    "B": "8", "b": "8",
}


def _is_money_like(token: str) -> bool:
    """True for price-looking tokens: 12.50, 4,50, 14.0 or a small integer."""
    if re.fullmatch(r"\d{1,6}[.,]\d{1,2}", token):
        return True
    if re.fullmatch(r"\d{1,3}", token):
        return int(token) <= 500
    return False


def _normalize_separators(token: str) -> str:
    """Resolve comma/dot ambiguity: dot stays decimal; '12,50' -> '12.50';
    '1,234' -> '1234'; mixed '6,273.94' -> '6273.94'."""
    if not re.fullmatch(r"\d[\d.,]*", token):
        return token
    if "," in token and "." in token:
        return token.replace(",", "")
    if "," in token:
        if re.fullmatch(r"\d{1,3},\d{2}", token):
            return token.replace(",", ".")
        if re.fullmatch(r"\d{1,3}(?:,\d{3})+", token):
            return token.replace(",", "")
    return token


def _parse_digits(token: str):
    try:
        return float(_normalize_separators(token).replace(",", "."))
    except ValueError:
        return None


def parse_amount(text: str, corrections: list, context: str):
    """Best-effort parse of the first money value in ``text``.

    Returns (value, raw_token, [corrections]). Every OCR-misread fix applied
    here is appended to ``corrections`` so the audit trail stays honest.
    """
    match = MONEY_TOKEN_RE.search(text)
    if not match:
        return None, None, []
    raw = match.group(1)

    # 'n' between digits is a misread decimal point (4n50 -> 4.50).
    n_fixed = re.sub(r"(?<=\d)n(?=\d)", ".", raw) if "n" in raw.lower() else raw
    parsed = _parse_digits(n_fixed)
    if parsed is not None:
        if n_fixed != raw:
            correction = {
                "context": context, "raw": raw, "value": parsed,
                "reason": "OCR 'n' misread as decimal point",
            }
            corrections.append(correction)
            return parsed, raw, [correction]
        return parsed, raw, []

    # Digit-letter confusion: O->0, l->1, ... applied only to retry a token
    # that otherwise could not parse.
    substituted = "".join(DIGIT_SUBSTITUTIONS.get(ch, ch) for ch in n_fixed)
    if substituted != n_fixed:
        parsed = _parse_digits(substituted)
        if parsed is not None:
            correction = {
                "context": context, "raw": raw, "value": parsed,
                "reason": "OCR digit-misread substitutions",
            }
            corrections.append(correction)
            return parsed, raw, [correction]
    return None, raw, []


def amounts_in_line(line: str):
    """All candidate number tokens in a line (validated as price-like)."""
    return [
        m.group(1)
        for m in MONEY_TOKEN_RE.finditer(line)
        if _is_money_like(m.group(1))
    ]


def _has_qty_x(line: str) -> bool:
    return bool(QTY_X_RE.search(line))


def looks_like_item(line: str) -> bool:
    """A receipt item line: has price-like numbers and isn't a phone/address."""
    if not amounts_in_line(line):
        return False
    if PHONE_RE.search(line):
        return False
    if DATE_RE.search(line):
        return False
    if ADDRESS_START_RE.match(line):
        return False
    return True


# --- Metadata helpers --------------------------------------------------------

def _extract_date(text: str):
    m = DATE_RE.search(text)
    return m.group(0) if m else None


def _extract_time(text: str):
    m = TIME_RE.search(text)
    return m.group(0) if m else None


def _extract_table(text: str):
    m = re.search(r"\d{1,4}", text)
    return m.group(0) if m else None


def _extract_staff(text: str):
    cleaned = re.sub(r"[^A-Za-z\s.']", "", text).strip()
    return cleaned or None


def _extract_terminal(text: str):
    # OCR noise: '@' and lowercase 'o' inside values are '0' ("POS-@2"); the
    # uppercase 'O' in terminal labels like "POS-01" must NOT be converted.
    text = re.sub(r"[@o]", "0", text)
    cleaned = re.sub(r"[\W_]+", " ", text).strip()
    m = re.search(r"(?i)([a-z]{1,5})\s*-?\s*(\d+)", cleaned)
    if m:
        return f"{m.group(1).upper()}-{m.group(2)}"
    return cleaned or None


def _clean_name(text: str) -> str:
    cleaned = re.sub(r"^[\s\W_]+", "", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    # If a price got glued onto the name column ("Mango Lassi 4.50"), cut the
    # name off before the first number and trim trailing junk.
    cut = re.search(r"\s(?=\d)", cleaned)
    if cut:
        cleaned = cleaned[: cut.start()]
    cleaned = re.sub(r"[\W_]+$", "", cleaned).strip()
    return cleaned


# --- Item record building ----------------------------------------------------

def _parse_item_structure(line: str, corrections: list):
    """Parse qty / unit price / line total from an item's amount line.

    Money tokens are read from the text AFTER the qty marker only, so junk
    OCR digits before the quantity (e.g. "4 1 x 3.95 -3.95") never leak into
    the prices.
    """
    result = {"quantity": None, "unit_price": None, "line_total": None, "has_x": False}

    match = QTY_X_RE.search(line)
    if match:
        result["has_x"] = True
        result["quantity"] = int(match.group(1))
        tail = line[match.end():]
    else:
        tail = line

    money = [
        m.group(1)
        for m in MONEY_TOKEN_RE.finditer(tail)
        if _is_money_like(m.group(1))
    ]
    if not money:
        return None

    result["unit_price"] = parse_amount(money[0], corrections, "line_item.unit_price")[0]
    if result["has_x"] and len(money) >= 2:
        result["line_total"] = parse_amount(money[1], corrections, "line_item.line_total")[0]
    return result


def _make_item(index, name, raw, struct, corrections):
    item = {
        "index": index,
        "name": name or "",
        "raw": raw,
        "quantity": struct["quantity"],
        "unit_price": struct["unit_price"],
        "line_total": struct["line_total"],
        "corrections": [],
    }
    if item["quantity"] == 1 and item["unit_price"] is None and item["line_total"] is not None:
        item["unit_price"] = item["line_total"]
        corrections.append({
            "context": f"line_items[{index}].unit_price", "raw": None,
            "value": item["line_total"], "reason": "inferred from line_total (qty=1)",
        })
    elif (
        item["quantity"] is not None
        and item["unit_price"] is not None
        and item["line_total"] is None
    ):
        item["line_total"] = item["quantity"] * item["unit_price"]
        corrections.append({
            "context": f"line_items[{index}].line_total", "raw": None,
            "value": item["line_total"], "reason": "inferred from qty * unit_price",
        })
    return item


# --- Segmentation ------------------------------------------------------------

class BillSegmenter:
    def __init__(self, text: str):
        self.text = text
        self.lines = [line.strip() for line in text.splitlines() if line.strip()]
        self.corrections = []
        self.line_kind = {}
        self.items = []
        self.item_end = []
        self.markers = []
        self.totals_lines = []
        self.payment_lines = []
        self.footer_lines = []
        self.header_lines = []
        self.extra_lines = []
        self.metadata = {}
        self.section = "header"
        self.pending_name = None

    # -- classification ------------------------------------------------------

    def run(self):
        for idx, line in enumerate(self.lines):
            self._classify(idx, line)
        self._flush_pending()
        return self._blocks()

    def _classify(self, idx, line):
        if self._is_separator(line):
            self.line_kind[idx] = "separator"
            return

        meta = self._metadata_from_line(line)
        if meta:
            self._record_metadata(meta)
            self.line_kind[idx] = "metadata"
            self.section = "metadata"
            return

        if SUMMARY_TOTAL_RE.search(line) or TOTAL_LINE_RE.search(line):
            self.totals_lines.append(line)
            self.line_kind[idx] = "totals"
            if self.section != "footer":
                self.section = "totals"
            return

        if FOOTER_LINE_RE.search(line) and self.section in ("totals", "payment", "footer", "items"):
            self.footer_lines.append(line)
            self.line_kind[idx] = "footer"
            self.section = "footer"
            return

        if PAYMENT_LINE_RE.search(line):
            self.payment_lines.append(line)
            self.line_kind[idx] = "payment"
            if self.section != "footer":
                self.section = "payment"
            return

        if ITEM_HEADER_RE.search(line) and len(line) < 50:
            self.line_kind[idx] = "item_header"
            self.section = "items"
            return

        if MARKER_RE.search(line) and self.section != "footer":
            self.markers.append({"line_idx": idx, "raw": line})
            self.line_kind[idx] = "marker"
            if self.section == "header":
                self.section = "items"
            return

        if self.section in ("items", "metadata"):
            self._item_line(idx, line)
            return

        # Header reaches an unambiguous receipt line (qty x price) with no
        # column header present — start items.
        if _has_qty_x(line):
            self.section = "items"
            self._item_line(idx, line)
            return

        # Unclassified.
        if self.section == "header":
            self.header_lines.append(line)
            self.line_kind[idx] = "header"
        else:
            self.extra_lines.append(line)
            self.line_kind[idx] = "other"

    def _is_separator(self, line):
        stripped = line.strip()
        return len(stripped) >= 3 and bool(SEPARATOR_RE.match(stripped))

    def _metadata_from_line(self, line):
        match = METADATA_SCAN_RE.search(line)
        if not match:
            return None
        return match.group(1).lower(), match.group(2)

    def _record_metadata(self, meta):
        key, value = meta
        if key == "date":
            date = _extract_date(value)
            if date:
                self.metadata["date"] = date
            time = _extract_time(value)
            if time:
                self.metadata["time"] = time
        elif key == "time":
            time = _extract_time(value)
            if time:
                self.metadata["time"] = time
        elif key == "table":
            table = _extract_table(value)
            if table:
                self.metadata["table"] = table
        elif key in ("staff", "server", "waiter"):
            staff = _extract_staff(value)
            if staff:
                self.metadata.setdefault("staff", staff)
        elif key == "terminal":
            terminal = _extract_terminal(value)
            if terminal:
                self.metadata["terminal"] = terminal
        else:
            self.extra_lines.append(f"{key}: {value}")

    # -- items ---------------------------------------------------------------

    def _item_line(self, idx, line):
        if not looks_like_item(line):
            name = _clean_name(line)
            if name and len(name) <= 60 and not _has_qty_x(line):
                self.pending_name = name
                self.line_kind[idx] = "name"
                return
            self.extra_lines.append(line)
            self.line_kind[idx] = "other"
            return

        struct = _parse_item_structure(line, self.corrections)
        if struct is None:
            name = _clean_name(line)
            if name and len(name) <= 60:
                self.pending_name = name
                self.line_kind[idx] = "name"
                return
            self.extra_lines.append(line)
            self.line_kind[idx] = "other"
            return

        name = self.pending_name or _clean_name(line)
        if self.pending_name:
            raw_line = f"{self.pending_name} / {line}"
        else:
            raw_line = line
        self.items.append(_make_item(len(self.items), name, raw_line, struct, self.corrections))
        self.item_end.append(idx)
        self.pending_name = None
        self.line_kind[idx] = "item"
        if self.section == "metadata":
            self.section = "items"

    def _flush_pending(self):
        if self.pending_name:
            self.extra_lines.append(self.pending_name)
            self.pending_name = None

    # -- discrepancy association ----------------------------------------------

    def _associate(self, marker):
        before = [i for i, end in enumerate(self.item_end) if end < marker["line_idx"]]
        mark_type = self._marker_type(marker["raw"])
        mark_amount, _, _ = parse_amount(marker["raw"], self.corrections, "discrepancy.amount")

        if not before:
            return {
                "type": mark_type, "item_index": None, "item_name": None,
                "confidence": "low", "amount": mark_amount,
                "reason": "no line item precedes the marker", "raw": marker["raw"],
            }

        idx = max(before)
        target = self.items[idx]
        gap = marker["line_idx"] - self.item_end[idx]
        matches_total = mark_amount is None or (
            target.get("line_total") is not None
            and abs(mark_amount - target["line_total"]) < 0.01
        )
        high = gap <= 2 and matches_total
        return {
            "type": mark_type, "item_index": idx, "item_name": target.get("name"),
            "confidence": "high" if high else "low",
            "amount": mark_amount,
            "reason": None if high else "marker amount or distance does not match the preceding item",
            "raw": marker["raw"],
        }

    def _marker_type(self, raw):
        for kind, patterns in DISCREPANCY_KEYWORDS.items():
            for pat in patterns:
                if re.search(rf"\b{re.escape(pat)}\b", raw, re.IGNORECASE):
                    return kind
        return "unknown"

    # -- totals / payment -----------------------------------------------------

    def _collect_totals(self):
        totals = {
            "lines": list(self.totals_lines),
            "subtotal": None, "tax": None, "total": None, "summaries": {},
        }
        total_re = re.compile(r"(?i)(?<![a-z])total\b|grand\s*total")
        for line in self.totals_lines:
            lower = line.lower()

            handled = False
            for label, pattern, strip_pct in (
                ("subtotal", "sub\\s*total", False),
                ("tax", "vat|tax", True),
            ):
                m = re.search(pattern, lower)
                if m and totals[label] is None:
                    vals = self._amount_values(line[m.end():], strip_pct=strip_pct)
                    if not vals:
                        vals = self._amount_values(line, strip_pct=strip_pct)
                    if vals:
                        totals[label] = vals[0]
                    handled = True
                    break
            if handled:
                continue

            summary = SUMMARY_TOTAL_RE.search(line)
            if summary:
                key = re.sub(r"[^a-z]", "", summary.group(1).lower()) or "other"
                totals["summaries"][key] = self._amount_values(line)
                continue

            m_total = total_re.search(lower)
            if m_total:
                vals = self._amount_values(line[m_total.end():])
                if not vals:
                    vals = self._amount_values(line)
                # grand-total rows on income reports carry a count + amount.
                if len(vals) >= 2 and re.search(r"income", lower):
                    continue
                if vals:
                    totals["total"] = vals[0]
                continue
        return totals

    def _amount_values(self, line, strip_pct=False):
        if strip_pct:
            line = re.sub(r"\(\s*\d+\s*%\)", "", line)
        return [
            value
            for value in (
                parse_amount(tok, self.corrections, "totals.amount")[0]
                for tok in amounts_in_line(line)
            )
            if value is not None
        ]

    def _collect_payment(self):
        payment = {}
        for line in self.payment_lines:
            lower = line.lower()
            m = re.search(r"(?i)payment\s*method\s*[:=\-]?\s*([A-Za-z\s]+)$", line)
            if m and "method" not in payment:
                payment["method"] = m.group(1).strip()
                continue
            m = re.search(r"(?i)card\s*type\s*[:=\-]?\s*([A-Za-z]+)", line)
            if m and "card_type" not in payment:
                payment["card_type"] = m.group(1).strip()
                continue
            if re.search(r"(?i)card\s*no", lower):
                last4 = CARD_LAST4_RE.findall(line)
                if last4:
                    payment["card_last4"] = last4[-1]
                continue
            if "method" not in payment:
                for keyword in ("visa", "mastercard", "amex"):
                    if keyword in lower:
                        payment["method"] = keyword.capitalize()
                        break
        return payment

    def _blocks(self):
        return {
            "header": list(dict.fromkeys(self.header_lines)),
            "metadata": self.metadata,
            "line_items": self.items,
            "discrepancies": [self._associate(m) for m in self.markers],
            "totals": self._collect_totals(),
            "payment": self._collect_payment(),
            "footer": list(dict.fromkeys(self.footer_lines)),
            "extra_lines": list(dict.fromkeys(self.extra_lines)),
            "corrections": self.corrections,
        }


def segment_text(text: str) -> dict:
    """Segment one bill's OCR text into structured blocks."""
    return BillSegmenter(text).run()