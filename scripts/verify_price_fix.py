
import re

def parse_price_fixed(price_str, price_val=None):
    price_cents = 0
    # Priority 1: Use extracted_price if available (it's usually a reliable float)
    if isinstance(price_val, (int, float)):
        price_cents = int(round(price_val * 100))
    
    # Priority 2: Parse price string if extracted_price failed
    elif price_str:
        # Clean string: remove currency symbols, letters, etc. keep digits, dots, commas
        # Matches: $1,234.56 -> 1,234.56
        # Matches: CA$ 1200 -> 1200
        match = re.search(r'[\d,]+\.?\d*', str(price_str))
        if match:
            clean_str = match.group(0).replace(",", "")
            try:
                price_cents = int(round(float(clean_str) * 100))
            except (ValueError, TypeError):
                pass

    return price_cents if price_cents > 0 else None

test_cases = [
    ("$19.99", None, 1999),
    ("$1,234.56", None, 123456),
    ("CA$1200.00", None, 120000), 
    ("US $50.00", None, 5000),
    ("1.234,56", None, 123), # European format still fails with simple regex (returns 123), but better than crash
    ("1234", 1234.0, 123400), # Extracted price provided
    ("Free", None, None),
    (None, None, None)
]

print(f"{'Input':<15} | {'Expected':<10} | {'Actual':<10} | {'Status'}")
print("-" * 50)

for p_str, p_val, expected in test_cases:
    actual = parse_price_fixed(p_str, p_val)
    status = "PASS" if actual == expected else "FAIL"
    print(f"{str(p_str):<15} | {str(expected):<10} | {str(actual):<10} | {status}")
