import json
from pathlib import Path

from core.storage import load_json, save_json

class RelationshipManager:
    """Manages continuous dynamic relationships based on PARTY_RELATIONSHIP_ENGINE.md and ADULT_RELATIONSHIP_CALIBRATION.md"""

    def __init__(self):
        self.filename = "PARTY_RELATIONSHIPS.json"

    def _load_data(self) -> dict:
        try:
            return load_json(self.filename)
        except Exception:
            # Create default structure if not exists/migration
            return {"version": "1.0", "schema": "PARTY_RELATIONSHIPS.json", "relationships": []}

    def _save_data(self, data: dict):
        save_json(self.filename, data)

    def _match_pair(self, rel: dict, char1: str, char2: str) -> bool:
        pair = set(rel.get("pair", []))
        return {char1, char2} == pair

    def get_relationship(self, char1: str, char2: str) -> dict:
        """Returns the relationship dict for a pair. If it doesn't exist, returns the engine baseline."""
        data = self._load_data()
        for rel in data.get("relationships", []):
            if self._match_pair(rel, char1, char2):
                return rel
        
        # Engine baseline for day 1
        return {
            "pair": [char1, char2],
            "affection": 25,
            "trust": 40,
            "tension": 10,
            "public_perception": 5,
            "intimacy": 10
        }

    def update_metrics(self, char1: str, char2: str, affection=0, trust=0, tension=0, intimacy=0, public_perception=0) -> dict:
        """Updates metrics for a pair, clamps between 0-100, and saves."""
        data = self._load_data()
        relationships = data.get("relationships", [])
        
        target_rel = None
        for rel in relationships:
            if self._match_pair(rel, char1, char2):
                target_rel = rel
                break
                
        if not target_rel:
            target_rel = self.get_relationship(char1, char2)
            relationships.append(target_rel)
            
        target_rel["affection"] = max(0, min(100, target_rel.get("affection", 25) + affection))
        target_rel["trust"] = max(0, min(100, target_rel.get("trust", 40) + trust))
        target_rel["tension"] = max(0, min(100, target_rel.get("tension", 10) + tension))
        target_rel["intimacy"] = max(0, min(100, target_rel.get("intimacy", 10) + intimacy))
        target_rel["public_perception"] = max(0, min(100, target_rel.get("public_perception", 5) + public_perception))
        
        data["relationships"] = relationships
        self._save_data(data)
        
        return target_rel

    def set_metrics(self, char1: str, char2: str, **kwargs) -> dict:
        """Sets metrics to absolute values."""
        data = self._load_data()
        relationships = data.get("relationships", [])
        
        target_rel = None
        for rel in relationships:
            if self._match_pair(rel, char1, char2):
                target_rel = rel
                break
                
        if not target_rel:
            target_rel = self.get_relationship(char1, char2)
            relationships.append(target_rel)
            
        for k, v in kwargs.items():
            if k in ["affection", "trust", "tension", "intimacy", "public_perception"]:
                target_rel[k] = max(0, min(100, v))
                
        data["relationships"] = relationships
        self._save_data(data)
        return target_rel

    def get_status_labels(self, rel: dict) -> list[str]:
        """Calculates narrative status labels based on current metrics."""
        labels = []
        
        aff = rel.get("affection", 0)
        tru = rel.get("trust", 0)
        ten = rel.get("tension", 0)
        intm = rel.get("intimacy", 0)
        
        # General Status
        if ten >= 75: labels.append("Fractured")
        elif ten >= 50: labels.append("Strained")
        
        if tru <= 25: labels.append("Distrustful")
        
        if aff >= 80: labels.append("Devoted")
        elif aff >= 60: labels.append("Bonded")
        elif aff >= 40: labels.append("Friendly")
        elif aff < 40 and ten < 50: labels.append("Neutral")
        
        # Intimacy Status
        if intm >= 85: labels.append("Exclusive Romance")
        elif intm >= 70: labels.append("Physical Romance")
        elif intm >= 50: labels.append("Romantic Bond")
        elif intm >= 30: labels.append("Emotional Closeness")
        
        return labels

# Global instance for easy import
relationship_manager = RelationshipManager()
