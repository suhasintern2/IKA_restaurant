import sys
sys.path.insert(0, '/mnt/d/Vlookupprojects/IKA')
from app.models.ticket import _label_values, _clean_value
import re

lines = [_clean_value(line) for line in """Ticket #260920-143 ou xXx
Haweli Restaurant Southall
Date Terminal
21/9/2026 Till-1
4
Table Department
12 RESTAURANT
& re]
User Payment Status
FARAZ Paid
&
Credit Card
£216.09
Items
Ticket Total: £216""".splitlines() if _clean_value(line)]

print("Lines:")
for i, line in enumerate(lines):
    print(f"{i}: {line}")

print("\n--- Testing _label_values ---")
fields = _label_values(lines)
for k, v in fields.items():
    print(f"  {k}: {v}")

# Let's also test the label_names loop manually
label_names = {
    "restaurant", "branch", "phone", "date", "terminal", "table",
    "department", "user", "staff", "payment status", "payment",
    "credit card", "ticket total", "grand total", "charged",
}
aliases = {
    "restaurant": "restaurant", "branch": "restaurant", "phone": "phone",
    "date": "ticket_date", "terminal": "terminal", "table": "table_name",
    "department": "department", "user": "user_name", "staff": "user_name",
    "payment status": "payment_status", "payment": "payment_status",
    "credit card": "credit_card_amount", "ticket total": "ticket_total",
    "grand total": "grand_total", "charged": "charged",
}
print("\n--- Label names loop (label on one line, value on next) ---")
for index, line in enumerate(lines[:-1]):
    key = re.sub(r"\s+", " ", line).strip().casefold()
    if key not in label_names or key in {"date", "terminal", "table", "department", "user", "staff"}:
        continue
    next_value = lines[index + 1]
    if next_value.casefold() in label_names:
        continue
    alias = aliases.get(key)
    if alias and next_value:
        print(f"  Matched: line '{line}' -> key '{key}' -> alias '{alias}', next_value '{next_value}'")

print("\n--- Colon/dash separated labels ---")
for line in lines:
    match = re.match(r"^\s*([A-Za-z][A-Za-z /_-]{1,30}?)\s*[:\-]\s*(.+?)\s*$", line)
    if not match:
        continue
    key = re.sub(r"\s+", " ", match.group(1)).strip().casefold()
    value = _clean_value(match.group(2))
    if key in aliases and value:
        print(f"  Matched: line '{line}' -> key '{key}', value '{value}' -> alias '{aliases[key]}'")

print("\n--- Specific regex for date, terminal, phone ---")
joined = " ".join(lines)
date_match = re.search(r"\b([0-3]?\d[/-][01]?\d[/-]\d{2,4})\b", joined)
if date_match:
    print(f"  Date: {date_match.group(1)}")
terminal_match = re.search(r"\b(Till[- ]?\d+|POS[- ]?\d+)\b", joined, re.IGNORECASE)
if terminal_match:
    print(f"  Terminal: {terminal_match.group(1)}")
phone_match = re.search(r"\b(0?\d{9,12})\b", joined)
if phone_match:
    print(f"  Phone: {phone_match.group(1)}")

print("\n--- Department and user from TAKE AWAY/RESTAURANT ---")
for line in lines:
    upper = line.upper()
    if upper.startswith("TAKE AWAY") or upper.startswith("RESTAURANT"):
        print(f"  Line: {line}")
        dept = line.split()[0] if upper.startswith("RESTAURANT") else "TAKE AWAY"
        print(f"    Department: {dept}")
        remainder = re.sub(r"^(TAKE AWAY|RESTAURANT)\b", "", line, flags=re.IGNORECASE).strip()
        print(f"    Remainder: '{remainder}'")

print("\n--- Payment status from exact match ---")
for line in lines:
    if re.fullmatch(r"PAID|UNPAID|PENDING|CASH|CARD", line, re.IGNORECASE):
        print(f"  Payment status line: {line}")

print("\n--- Last loop: label, field in (('credit card', ...)) ---")
for label, field in (("credit card", "credit_card_amount"), ("ticket total", "ticket_total"), ("grand total", "grand_total"), ("charged", "charged")):
    pattern = rf"{label}\s*:?[^\n]*?(£?\s*\d+[.,]\d{{2}})"
    match = re.search(pattern, joined, flags=re.IGNORECASE)
    if match:
        print(f"  Label '{label}' matched: {match.group(0)} -> group 1: {match.group(1)}")