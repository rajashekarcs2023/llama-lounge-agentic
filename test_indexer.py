"""Test the llms.txt-based indexer against Composio and CrewAI docs."""

from src.indexer import index_site, fetch_pages

print("=" * 60)
print("Test 1: Index Composio docs via llms.txt")
print("=" * 60)
pages = index_site("https://docs.composio.dev")
print(f"\nFirst 10 pages:")
for p in pages[:10]:
    print(f"  [{p.get('section', '?')}] {p['title']}")
    print(f"    → {p['url']}")

print(f"\n{'=' * 60}")
print("Test 2: Index CrewAI docs via llms.txt")
print("=" * 60)
pages2 = index_site("https://docs.crewai.com")
print(f"\nFirst 10 pages:")
for p in pages2[:10]:
    print(f"  [{p.get('section', '?')}] {p['title']}")
    print(f"    → {p['url']}")

print(f"\n{'=' * 60}")
print("Test 3: Fetch a single Composio doc page (.md)")
print("=" * 60)
# Pick a page that ends in .md from the index
md_pages = [p for p in pages if p['url'].endswith('.md')]
if md_pages:
    test_url = md_pages[0]['url']
    print(f"Fetching: {test_url}")
    content = fetch_pages([test_url])
    for url, text in content.items():
        print(f"  Content length: {len(text)} chars")
        print(f"  First 500 chars:\n{text[:500]}")
else:
    print("  No .md pages found in index")

print(f"\n{'=' * 60}")
print("All indexer tests complete!")
print("=" * 60)
