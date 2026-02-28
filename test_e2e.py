"""End-to-end test: index docs, navigate, fetch, generate code."""

import os
from dotenv import load_dotenv
load_dotenv()

from src.engine import add_source, run_task

print("=" * 60)
print("DocAgent — End-to-End Test")
print("=" * 60)

# Step 1: Index doc sites
print("\n📚 Indexing documentation sources...")
add_source("https://docs.composio.dev")
add_source("https://docs.crewai.com")

# Step 2: Run a task that requires BOTH doc sites
print("\n🔍 Running task...")
task = "Build a CrewAI agent that uses Composio to send Gmail emails. Show the full setup including authentication."

code = run_task(task)

if code:
    print("\n✅ End-to-end test PASSED — code generated successfully")
else:
    print("\n❌ End-to-end test FAILED — no code generated")
