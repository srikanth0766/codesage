"""
JSON-File Sprint Store.

Persists sprint smell data without requiring a database.
Data is stored in backend/agile_risk/sprint_data.json.
This is the MVP approach — swap for TimescaleDB in production.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

_DATA_FILE = Path(__file__).parent / "sprint_data.json"


class SprintStore:
    """
    Simple JSON file-based store for sprint metrics.

    Each entry:
        {
            "sprint_id":      "Sprint-1",
            "timestamp":      "2026-02-27T09:00:00",
            "smell_count":    12,
            "refactor_count": 3,
            "module":         "backend"
        }
    """

    def __init__(self):
        """Ensure data file exists."""
        if not _DATA_FILE.exists():
            _DATA_FILE.write_text(json.dumps({"sprints": []}, indent=2))

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def log_sprint(
        self,
        sprint_id: str,
        smell_count: int,
        refactor_count: int = 0,
        module: str = "default",
    ) -> None:
        """Append a sprint record."""
        data = self._load()
        data["sprints"].append({
            "sprint_id": sprint_id,
            "timestamp": datetime.utcnow().isoformat(),
            "smell_count": smell_count,
            "refactor_count": refactor_count,
            "module": module,
        })
        self._save(data)

    def update_latest_sprint(self, smells_delta: int, refactor_delta: int) -> Optional[str]:
        """Update the most recent sprint with new smell/refactor deltas."""
        data = self._load()
        if not data.get("sprints"):
            return None
            
        latest_sprint = data["sprints"][-1]
        latest_sprint["smell_count"] = max(0, latest_sprint["smell_count"] + smells_delta)
        latest_sprint["refactor_count"] = max(0, latest_sprint.get("refactor_count", 0) + refactor_delta)
        
        self._save(data)
        return latest_sprint["sprint_id"]

    def delete_sprint(self, sprint_id: str) -> bool:
        """Delete a specific sprint by ID."""
        data = self._load()
        initial_count = len(data.get("sprints", []))
        data["sprints"] = [s for s in data.get("sprints", []) if s["sprint_id"] != sprint_id]
        
        if len(data["sprints"]) < initial_count:
            self._save(data)
            return True
        return False

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_all(self) -> Dict[str, Any]:
        """Return full sprint history with summary statistics."""
        data = self._load()
        sprints = data.get("sprints", [])

        smell_counts = [s["smell_count"] for s in sprints]
        refactor_counts = [s["refactor_count"] for s in sprints]

        summary = {
            "total_sprints": len(sprints),
            "total_smells_detected": sum(smell_counts),
            "total_refactored": sum(refactor_counts),
            "average_smell_per_sprint": round(
                sum(smell_counts) / len(smell_counts), 2
            ) if smell_counts else 0,
            "trend": self._compute_trend(smell_counts),
        }

        return {
            "sprints": sprints,
            "summary": summary,
        }

    def get_smell_history(self) -> List[int]:
        """Return just the smell count list (for risk model)."""
        data = self._load()
        return [s["smell_count"] for s in data.get("sprints", [])]

    def get_refactor_history(self) -> List[int]:
        """Return just the refactor count list (for risk model)."""
        data = self._load()
        return [s["refactor_count"] for s in data.get("sprints", [])]

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _load(self) -> Dict:
        try:
            return json.loads(_DATA_FILE.read_text())
        except Exception:
            return {"sprints": []}

    def _save(self, data: Dict) -> None:
        _DATA_FILE.write_text(json.dumps(data, indent=2))

    def _compute_trend(self, counts: List[int]) -> str:
        if len(counts) < 2:
            return "insufficient_data"
        delta = counts[-1] - counts[-2]
        if delta > 2:
            return "increasing"
        elif delta < -2:
            return "decreasing"
        return "stable"
