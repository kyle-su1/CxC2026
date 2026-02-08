
import re

def parse_price(price_str):
    """
    Current implementation logic from serpapi_client.py
    """
    if isinstance(price_str, (int, float)):
        return int(price_str * 100)
    else:
        # Original logic
        cleaned = str(price_str).replace("$", "").replace(",", "").strip()
        try:
            return int(float(cleaned) * 100)
        except (ValueError, TypeError):
            return None

test_cases = [
    ("$19.99", 1999),
    ("$1,234.56", 123456),
    ("CA$1200.00", 120000), # Fails currently?
    ("US $50.00", 5000),    # Fails currently?
    ("1.234,56", 123456),   # European format (will fail with current logic)
    ("1234", 123400),
    ("Free", None),
    (None, None)
]

print(f"{'Input':<15} | {'Expected':<10} | {'Actual':<10} | {'Status'}")
print("-" * 50)

for inp, expected in test_cases:
    actual = parse_price(inp)
    status = "PASS" if actual == expected else "FAIL"
    print(f"{str(inp):<15} | {str(expected):<10} | {str(actual):<10} | {status}")
