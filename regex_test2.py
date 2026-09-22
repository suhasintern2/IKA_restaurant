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
print(repr(joined))
print()

label = "ticket total"
pattern = rf"{label}\s*:?[^\n]*?(£?\s*\d+[.,]\d{{2}})"
print(f"Pattern: {pattern}")
match = re.search(pattern, joined, flags=re.IGNORECASE)
if match:
    print(f"Match: {match.group(0)}")
    print(f"Group 1: {match.group(1)}")
else:
    print("No match")

# Let's also try to see if the pattern matches somewhere else by using findall
print("\nUsing findall:")
matches = list(re.finditer(pattern, joined, flags=re.IGNORECASE))
for m in matches:
    print(f"  {m.group(0)} -> group1: {m.group(1)}")

# Let's also test the pattern for credit card
label2 = "credit card"
pattern2 = rf"{label2}\s*:?[^\n]*?(£?\s*\d+[.,]\d{{2}})"
print(f"\nPattern for credit card: {pattern2}")
match2 = re.search(pattern2, joined, flags=re.IGNORECASE)
if match2:
    print(f"Match: {match2.group(0)}")
    print(f"Group 1: {match2.group(1)}")
else:
    print("No match")