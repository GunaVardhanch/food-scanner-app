#!/usr/bin/env python3
from app import create_app

app = create_app()

print("\n📋 Registered Flask routes:")
print("=" * 60)

for rule in app.url_map.iter_rules():
    if rule.endpoint != 'static':
        methods = ','.join(rule.methods - {'HEAD', 'OPTIONS'})
        print(f"{rule.rule:40} {methods:15} {rule.endpoint}")

print("=" * 60)

# Check if /api/profile is registered
profile_route = None
for rule in app.url_map.iter_rules():
    if '/api/profile' in rule.rule:
        profile_route = rule
        print(f"\n✅ Found /api/profile route:")
        print(f"   Rule: {rule.rule}")
        print(f"   Methods: {rule.methods}")
        print(f"   Endpoint: {rule.endpoint}")
        break

if not profile_route:
    print(f"\n❌ /api/profile route NOT found!")
