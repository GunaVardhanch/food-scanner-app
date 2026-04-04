#!/usr/bin/env python3
"""
Test script to diagnose chatbot issue.
Tests: 1) Groq SDK availability, 2) API key, 3) Chatbot initialization
"""

import os
import sys
sys.path.insert(0, '.')

print("=" * 60)
print("CHATBOT DIAGNOSIS TEST")
print("=" * 60)

# Test 1: Groq SDK
print("\n[TEST 1] Groq SDK Check")
try:
    from groq import Groq
    print("  ✓ Groq SDK installed and importable")
    GROQ_AVAILABLE = True
except ImportError as e:
    print(f"  ✗ Groq SDK not available: {e}")
    GROQ_AVAILABLE = False

# Test 2: Environment variable
print("\n[TEST 2] GROQ_API_KEY Environment Variable")
api_key = os.getenv('GROQ_API_KEY')
print(f"  Key present: {bool(api_key)}")
if api_key:
    print(f"  Key length: {len(api_key)}")
    print(f"  Key preview: {api_key[:10]}...{api_key[-5:]}")
else:
    print(f"  ✗ GROQ_API_KEY not set!")

# Test 3: Chatbot initialization
print("\n[TEST 3] Chatbot Initialization")
from app.services.chatbot_service import FoodChatbot

cb = FoodChatbot()
print(f"  Client initialized: {cb.client is not None}")
print(f"  API Key available: {bool(cb.api_key)}")

# Test 4: Chat functionality
print("\n[TEST 4] Send Chat Message")
print("  Sending: 'What is biryani?'")
response = cb.chat("What is biryani?")
print(f"  Response: {response}")

# Summary
print("\n" + "=" * 60)
if cb.client is not None and api_key:
    print("✅ CHATBOT WORKING - No issues found")
elif not GROQ_AVAILABLE:
    print("❌ ISSUE: Groq SDK not installed")
    print("   FIX: pip install groq")
elif not api_key:
    print("❌ ISSUE: GROQ_API_KEY not set")
    print("   FIX: Set environment variable GROQ_API_KEY=your_key")
else:
    print("❌ ISSUE: Chatbot client not initialized")
    print("   FIX: Check logs above")
print("=" * 60)
