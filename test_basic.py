"""Quick smoke test: verify Composio + CrewAI integration works."""

import os
from dotenv import load_dotenv

load_dotenv()

# 1. Test env vars are loaded
print("=" * 50)
print("1. Checking environment variables...")
composio_key = os.getenv("COMPOSIO_API_KEY")
openai_key = os.getenv("OPENAI_API_KEY")
print(f"   COMPOSIO_API_KEY: {'✓ set' if composio_key else '✗ missing'}")
print(f"   OPENAI_API_KEY:   {'✓ set' if openai_key else '✗ missing'}")

# 2. Test imports
print("\n2. Testing imports...")
try:
    from composio import Composio
    from composio_crewai import CrewAIProvider
    from crewai import Agent, Crew, Task
    print("   ✓ All imports successful")
except ImportError as e:
    print(f"   ✗ Import failed: {e}")
    exit(1)

# 3. Test Composio client initialization
print("\n3. Testing Composio client...")
try:
    composio = Composio(provider=CrewAIProvider())
    print("   ✓ Composio client created with CrewAI provider")
except Exception as e:
    print(f"   ✗ Composio init failed: {e}")
    exit(1)

# 4. Test session creation
print("\n4. Testing session creation...")
try:
    session = composio.create(user_id="test_user")
    print("   ✓ Session created")
except Exception as e:
    print(f"   ✗ Session creation failed: {e}")
    exit(1)

# 5. Test getting tools
print("\n5. Testing tools retrieval...")
try:
    tools = session.tools()
    print(f"   ✓ Got {len(tools)} tools")
except Exception as e:
    print(f"   ✗ Tools retrieval failed: {e}")
    exit(1)

# 6. Test creating a simple CrewAI agent (no execution, just verify wiring)
print("\n6. Testing CrewAI agent creation...")
try:
    agent = Agent(
        role="Test Agent",
        goal="Test that CrewAI + Composio wiring works",
        backstory="You are a test agent.",
        tools=tools,
        llm="gpt-4o",
        verbose=True,
    )
    print("   ✓ Agent created with Composio tools")
except Exception as e:
    print(f"   ✗ Agent creation failed: {e}")
    exit(1)

print("\n" + "=" * 50)
print("All checks passed! Composio + CrewAI integration is working.")
print("=" * 50)
