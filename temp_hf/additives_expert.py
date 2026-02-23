import re
import json
import os

class AdditivesExpert:
    """
    Comprehensive FSSAI/INS additives detection, high-risk flagging,
    and interaction warning system.
    Loads data from additives_db.json and uses robust regex matching.
    """
    # Risk tier thresholds
    HIGH_RISK_RED_COUNT = 3      # ≥3 RED additives = HIGH_RISK
    MODERATE_RISK_RED_COUNT = 1  # ≥1 RED additive  = MODERATE_RISK

    def __init__(self, db_path=None):
        if db_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(current_dir, "additives_db.json")
        
        self.db_path = db_path
        self.additives = []
        self._interaction_map = {}  # id -> list of conflicting ids
        self.load_database()

    def load_database(self):
        try:
            if os.path.exists(self.db_path):
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    self.additives = json.load(f)
                self._build_interaction_map()
                print(f"AdditivesExpert: Loaded {len(self.additives)} items from {self.db_path}")
            else:
                print(f"AdditivesExpert: Warning! Database not found at {self.db_path}. Using minimal fallback.")
                self.additives = [
                    {"id": "INS 621", "name": "MSG", "risk_level": "RED", "impact": -3.5,
                     "description": "Flavor enhancer.", "fssai_status": "restricted",
                     "interaction_warnings": [], "tags": []},
                    {"id": "INS 319", "name": "TBHQ", "risk_level": "RED", "impact": -3.0,
                     "description": "Preservative.", "fssai_status": "restricted",
                     "interaction_warnings": [], "tags": []}
                ]
        except Exception as e:
            print(f"AdditivesExpert: Error loading database: {e}")
            self.additives = []

    def _build_interaction_map(self):
        """Pre-build a map of additive interactions for O(1) lookups."""
        self._interaction_map = {}
        for additive in self.additives:
            warnings = additive.get("interaction_warnings", [])
            if warnings:
                self._interaction_map[additive["id"]] = warnings

    def analyze_text(self, text):
        """
        Detect additives in OCR text using robust pattern matching.
        Returns: (detected_list, total_impact)
        """
        detected = []
        total_impact = 0
        text_upper = text.upper()
        detected_ids = set()

        for additive in self.additives:
            ins_id = additive["id"]
            name = additive["name"].upper()
            
            # Build search patterns
            patterns = [re.escape(name)]
            
            # Also match common aliases (e.g. "MSG" for "MSG (Monosodium Glutamate)")
            short_name = name.split("(")[0].strip()
            if short_name != name:
                patterns.append(re.escape(short_name))
            
            if "INS" in ins_id:
                simple_code = ins_id.replace("INS", "").strip()
                patterns.append(re.escape(ins_id))              # INS 102
                patterns.append(rf"INS[\s\-]*{simple_code}")    # INS-102, INS102
                patterns.append(rf"E[\s]*{simple_code}")        # E 102, E102
                patterns.append(rf"\b{simple_code}\b")          # Just "102" as whole word
            
            combined_pattern = "|".join(patterns)
            
            if re.search(combined_pattern, text_upper):
                if ins_id not in detected_ids:
                    entry = {
                        "name": f"{additive['name']} ({ins_id})",
                        "reason": additive.get("description", "Additive used in food processing."),
                        "risk_level": additive["risk_level"],
                        "category": additive.get("category", "Unknown"),
                        "fssai_status": additive.get("fssai_status", "unknown"),
                        "tags": additive.get("tags", [])
                    }
                    detected.append(entry)
                    total_impact += additive.get("impact", 0)
                    detected_ids.add(ins_id)
        
        return detected, total_impact

    def get_risk_summary(self, detected_additives):
        """
        Generate a structured risk assessment from detected additives.
        Returns a dict with risk_tier, counts, banned items, interaction warnings, and recommendation.
        """
        red_count = 0
        orange_count = 0
        banned_items = []
        restricted_items = []
        watchlist_items = []
        detected_ids = set()

        for entry in detected_additives:
            # Extract raw id from "Name (ID)" format
            raw_id = self._extract_id(entry["name"])
            detected_ids.add(raw_id)

            level = entry.get("risk_level", "GREEN")
            status = entry.get("fssai_status", "permitted")

            if level == "RED":
                red_count += 1
            elif level == "ORANGE":
                orange_count += 1

            if status == "banned":
                banned_items.append(entry["name"])
            elif status == "restricted":
                restricted_items.append(entry["name"])
            elif status == "watchlist":
                watchlist_items.append(entry["name"])

        # Check interactions
        interaction_warnings = self._check_interactions(detected_ids)

        # Determine risk tier
        if banned_items:
            risk_tier = "CRITICAL"
            recommendation = (
                f"[CRITICAL] This product contains BANNED substance(s): "
                f"{', '.join(banned_items)}. These are illegal under FSSAI regulations. "
                f"Do NOT consume. Report to FSSAI if found in market."
            )
        elif red_count >= self.HIGH_RISK_RED_COUNT or interaction_warnings:
            risk_tier = "HIGH_RISK"
            recommendation = (
                f"[HIGH RISK] {red_count} high-risk additive(s) detected. "
                f"Frequent consumption may pose serious health risks. "
                f"Consider switching to cleaner alternatives."
            )
        elif red_count >= self.MODERATE_RISK_RED_COUNT:
            risk_tier = "MODERATE_RISK"
            recommendation = (
                f"[MODERATE RISK] {red_count} concerning additive(s) found. "
                f"Occasional consumption is acceptable, but long-term intake should be limited."
            )
        elif orange_count > 0:
            risk_tier = "LOW_RISK"
            recommendation = (
                f"[LOW RISK] {orange_count} mildly concerning additive(s). "
                f"Generally safe for occasional consumption."
            )
        else:
            risk_tier = "SAFE"
            recommendation = (
                "[SAFE] No concerning additives detected. This product has a clean label."
            )

        return {
            "risk_tier": risk_tier,
            "red_count": red_count,
            "orange_count": orange_count,
            "total_detected": len(detected_additives),
            "banned_substances": banned_items,
            "restricted_substances": restricted_items,
            "watchlist_substances": watchlist_items,
            "interaction_warnings": interaction_warnings,
            "recommendation": recommendation
        }

    def _check_interactions(self, detected_ids):
        """
        Cross-check detected additive IDs for known dangerous combinations.
        Returns list of warning strings.
        """
        warnings = []
        checked_pairs = set()

        for additive_id in detected_ids:
            if additive_id in self._interaction_map:
                for conflict_id in self._interaction_map[additive_id]:
                    if conflict_id in detected_ids:
                        pair = tuple(sorted([additive_id, conflict_id]))
                        if pair not in checked_pairs:
                            checked_pairs.add(pair)
                            # Look up names
                            name_a = self._get_name(additive_id)
                            name_b = self._get_name(conflict_id)
                            warnings.append(
                                f"[WARNING] {name_a} + {name_b}: Known dangerous interaction. "
                                f"These substances together may produce harmful compounds."
                            )
        return warnings

    def _get_name(self, additive_id):
        """Get display name for an additive ID."""
        for a in self.additives:
            if a["id"] == additive_id:
                return f"{a['name']} ({a['id']})"
        return additive_id

    def _extract_id(self, display_name):
        """Extract the raw ID from a display name like 'Tartrazine (INS 102)' or 'Ascorbic Acid (Vitamin C) (INS 300)'."""
        matches = re.findall(r'\(([^)]+)\)', display_name)
        return matches[-1] if matches else display_name


if __name__ == "__main__":
    expert = AdditivesExpert()
    
    # Test 1: Basic detection
    test_text = "Contains Tartrazine, INS 211, and 621 flavor enhancer."
    results, impact = expert.analyze_text(test_text)
    print(f"\nTest 1 - Basic Detection:")
    print(f"  Detected: {[r['name'] for r in results]}")
    print(f"  Impact: {impact}")
    
    # Test 2: Interaction warning (Sodium Benzoate + Ascorbic Acid)
    test_text2 = "Ingredients: Sodium Benzoate, Ascorbic Acid, Sugar."
    results2, impact2 = expert.analyze_text(test_text2)
    summary2 = expert.get_risk_summary(results2)
    print(f"\nTest 2 - Interaction Warning:")
    print(f"  Detected: {[r['name'] for r in results2]}")
    print(f"  Risk Summary: {json.dumps(summary2, indent=2)}")
    
    # Test 3: Banned substance
    test_text3 = "Contains Potassium Bromate and wheat flour."
    results3, impact3 = expert.analyze_text(test_text3)
    summary3 = expert.get_risk_summary(results3)
    print(f"\nTest 3 - Banned Substance:")
    print(f"  Detected: {[r['name'] for r in results3]}")
    print(f"  Risk Tier: {summary3['risk_tier']}")
    print(f"  Recommendation: {summary3['recommendation']}")
