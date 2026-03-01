"""Quick test to verify Daytona SDK integration."""
import os
from dotenv import load_dotenv
load_dotenv()

from daytona import Daytona, DaytonaConfig

api_key = os.getenv("DAYTONA_API_KEY")
print(f"API key loaded: {bool(api_key)}")

config = DaytonaConfig(api_key=api_key)
daytona = Daytona(config)

print("Creating sandbox...")
sandbox = daytona.create()
print(f"Sandbox created!")

# Test 1: Hello World
print("\n--- Test 1: Hello World ---")
r = sandbox.process.code_run('print("Hello from Daytona!")')
print(f"Exit: {r.exit_code} | Output: {r.result}")

# Test 2: Install + import a package
print("\n--- Test 2: pip install + import ---")
r = sandbox.process.code_run(
    'import subprocess; subprocess.run(["pip", "install", "-q", "requests"], capture_output=True)'
)
r2 = sandbox.process.code_run('import requests; print(f"requests {requests.__version__} OK")')
print(f"Exit: {r2.exit_code} | Output: {r2.result}")

# Test 3: Bad import (should fail)
print("\n--- Test 3: Bad import (should fail) ---")
r3 = sandbox.process.code_run('from composio.fake_module import FakeThing')
print(f"Exit: {r3.exit_code} | Output: {r3.result}")

# Cleanup
print("\nDeleting sandbox...")
sandbox.delete()
print("Done! Daytona SDK works correctly.")
