"""Test script to verify everything is set up correctly"""

import os
import sys

print("=" * 50)
print("Testing Email Assistant Setup")
print("=" * 50)

# Test 1: Python version
print("\n[1/5] Checking Python version...")
print(f"Python: {sys.version}")
if sys.version_info >= (3, 8):
    print("✅ Python version OK")
else:
    print("❌ Python 3.8+ required")

# Test 2: Required files
print("\n[2/5] Checking required files...")
required_files = ["email_assistant_openrouter.py", "requirements.txt"]
for file in required_files:
    if os.path.exists(file):
        print(f"✅ {file} found")
    else:
        print(f"❌ {file} missing")

# Test 3: .env file
print("\n[3/5] Checking API keys...")
if os.path.exists(".env"):
    print("✅ .env file found")
    with open(".env", "r") as f:
        if "OPENROUTER_API_KEY=" in f.read():
            print("✅ OPENROUTER_API_KEY configured")
        else:
            print("⚠️ OPENROUTER_API_KEY not set in .env")
else:
    print("⚠️ .env file missing (needed for API key)")

# Test 4: Google credentials
print("\n[4/5] Checking Google credentials...")
if os.path.exists("credentials.json"):
    print("✅ credentials.json found")
else:
    print("⚠️ credentials.json missing (needed for Gmail access)")

# Test 5: Dependencies
print("\n[5/5] Checking dependencies...")
try:
    import google.auth
    print("✅ google-auth installed")
except ImportError:
    print("❌ google-auth not installed (run: pip install -r requirements.txt)")

try:
    import requests
    print("✅ requests installed")
except ImportError:
    print("❌ requests not installed")

print("\n" + "=" * 50)
print("Setup Check Complete!")
print("=" * 50)
print("\nIf everything is ✅, you can run: python email_assistant_openrouter.py")
print("If you see ⚠️ or ❌, follow the instructions above.\n")