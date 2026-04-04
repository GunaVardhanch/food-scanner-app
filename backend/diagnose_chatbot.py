#!/usr/bin/env python3
"""
Standalone chatbot test - doesn't require full backend setup
"""

import os
import sys

print("=" * 60)
print("CHATBOT ISSUE DIAGNOSIS")
print("=" * 60)

# Test 1: API Key check
print("\n[TEST 1] GROQ_API_KEY Environment Variable")
api_key = os.getenv('GROQ_API_KEY')
if api_key:
    print(f"  ✓ API Key found: {api_key[:15]}...{api_key[-5:]}")
else:
    print(f"  ✗ GROQ_API_KEY is NOT SET")
    print(f"  ✗ This is the cause of your chatbot error!")

# Test 2: Groq SDK check
print("\n[TEST 2] Groq SDK Installation")
try:
    from groq import Groq
    print(f"  ✓ Groq SDK is installed")
except ImportError:
    print(f"  ✗ Groq SDK not installed")
    print(f"  → Fix: pip install groq")
    sys.exit(1)

# Test 3: Simulate chatbot initialization
print("\n[TEST 3] Chatbot Initialization (Simulated)")
if not api_key:
    print(f"  Initializing without API key...")
    try:
        client = Groq(api_key=None)
        print(f"  Client created: {client}")
    except Exception as e:
        print(f"  ✗ Cannot initialize Groq client without API key")
        print(f"     Error: {type(e).__name__}: {e}")
    
    print(f"\n  → RESULT: Client initialization FAILS")
    print(f"  → Chatbot returns: 'I'm currently unavailable. Please try again later.'")
else:
    try:
        client = Groq(api_key=api_key)
        print(f"  ✓ Groq client initialized successfully")
    except Exception as e:
        print(f"  ✗ Failed to initialize: {e}")

# Summary
print("\n" + "=" * 60)
print("DIAGNOSIS SUMMARY:")
print("=" * 60)

if not api_key:
    print("""
❌ PROBLEM IDENTIFIED:
   Your chatbot is showing "I'm currently unavailable" because:
   
   1. GROQ_API_KEY environment variable is NOT SET
   2. Groq API client cannot be initialized without a key
   3. Backend returns error message

✅ SOLUTION:

   FOR LOCAL TESTING:
   ──────────────────
   1. Get API key from: https://console.groq.com/keys
   2. Set environment variable:
      - Windows PowerShell:
        $env:GROQ_API_KEY = "paste-your-key-here"
      - Windows CMD:
        set GROQ_API_KEY=paste-your-key-here
      - Mac/Linux:
        export GROQ_API_KEY="paste-your-key-here"
   
   3. Test: python test_chatbot.py (again)

   FOR RAILWAY DEPLOYMENT (IMPORTANT):
   ──────────────────────────────────
   1. Go to Railway Dashboard
   2. Select your NutriScanner project
   3. Click Settings → Environment → New Variable
   4. Name: GROQ_API_KEY
   5. Value: (paste your API key from https://console.groq.com/keys)
   6. Click Deploy

📝 MORE INFO: See CHATBOT_FIX_GUIDE.md for complete instructions
""")
else:
    print("✅ API key is set. Check Railway logs for other issues.")

print("=" * 60)
