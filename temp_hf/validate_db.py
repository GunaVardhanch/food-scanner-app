import json
import sys

db = json.load(open('additives_db.json', encoding='utf-8'))
print(f"Total entries: {len(db)}")

reds = [a for a in db if a['risk_level'] == 'RED']
oranges = [a for a in db if a['risk_level'] == 'ORANGE']
greens = [a for a in db if a['risk_level'] == 'GREEN']
yellows = [a for a in db if a['risk_level'] == 'YELLOW']
banned = [a for a in db if a.get('fssai_status') == 'banned']

print(f"RED: {len(reds)}, ORANGE: {len(oranges)}, YELLOW: {len(yellows)}, GREEN: {len(greens)}")
print(f"Banned substances: {len(banned)}")
print(f"All have fssai_status: {all('fssai_status' in a for a in db)}")
print(f"All have interaction_warnings: {all('interaction_warnings' in a for a in db)}")

assert len(db) >= 80, f"Database too small: {len(db)}"
assert all('fssai_status' in a for a in db), "Missing fssai_status field"
assert all('interaction_warnings' in a for a in db), "Missing interaction_warnings field"
print("\nAll validation checks PASSED!")
