"""Parse and display SerpAPI Lens results."""
import json

with open("/app/serpapi_hybrid_test.json") as f:
    data = json.load(f)

print("=== SerpAPI Lens Results ===")
print(f"Keys: {list(data.keys())}")

if "knowledge_graph" in data:
    kg = data["knowledge_graph"]
    print(f"\nKnowledge Graph: {kg.get('title')}")

if "visual_matches" in data:
    vm = data["visual_matches"]
    print(f"\nVisual Matches ({len(vm)}):")
    for i, m in enumerate(vm[:8]):
        print(f"  {i+1}. {m.get('title')}")

if "shopping_results" in data:
    sr = data["shopping_results"]
    print(f"\nShopping Results ({len(sr)}):")
    for i, s in enumerate(sr[:5]):
        print(f"  {i+1}. {s.get('title')}")
        print(f"     Price: {s.get('price')}")

if "error" in data:
    print(f"\nError: {data['error']}")
