"""Check last Lens entries."""
with open("/app/debug_output.txt") as f:
    lines = f.readlines()[-100:]

for line in lines:
    if "[Lens]" in line or "Lens" in line or "timeout" in line.lower() or "error" in line.lower():
        print(line.rstrip())
