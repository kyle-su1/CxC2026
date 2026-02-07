"""Parse and display SerpAPI Lens results."""
import json

with open("/app/serpapi_lens_test_results.json") as f:
    data = json.load(f)

print("Keys:", list(data.keys()))

if "knowledge_graph" in data:
    kg = data["knowledge_graph"]
    print("\n=== Knowledge Graph ===")
    print(f"Title: {kg.get('title')}")
    print(f"Description: {kg.get('description')}")

if "visual_matches" in data:
    matches = data["visual_matches"]
    print(f"\n=== Visual Matches ({len(matches)}) ===")
    for i, m in enumerate(matches[:8]):
        print(f"{i+1}. {m.get('title')}")
        if m.get('source'):
            print(f"   Source: {m.get('source')}")
        if m.get('link'):
            print(f"   Link: {m.get('link')[:60]}...")

if "shopping_results" in data:
    items = data["shopping_results"]
    print(f"\n=== Shopping Results ({len(items)}) ===")
    for i, item in enumerate(items[:5]):
        print(f"{i+1}. {item.get('title')}")
        print(f"   Price: {item.get('price')}")

if "error" in data:
    print(f"\nAPI Error: {data['error']}")
