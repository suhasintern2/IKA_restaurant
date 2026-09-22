import re

lines = [
    "Ticket #260920-143 ou xXx",
    "Haweli Restaurant Southall",
    "Date Terminal",
    "21/9/2026 Till-1",
    "4",
    "Table Department",
    "12 RESTAURANT",
    "& re]",
    "User Payment Status",
    "FARAZ Paid",
    "&",
    "Credit Card",
    "£216.09",
    "Items",
    "Ticket Total: £216"
]

joined = "\n".join(lines)
print("Joined string:")
print(joined)
print()

for label, field in [("credit card", "credit_card_amount"), ("ticket total", "ticket_total"), ("grand total", "grand_total"), ("charged", "charged")]:
    pattern = rf"{label}\s*:?[^\n]*?(£?\s*\d+[.,]\d{{2}})"
    print(f"Label: {label}")
    print(f"Pattern: {pattern}")
    match = re.search(pattern, joined, flags=re.IGNORECASE)
    if match:
        print(f"  Match: {match.group(0)}")
        print(f"  Group 1: {match.group(1)}")
    else:
        print("  No match")
    print()