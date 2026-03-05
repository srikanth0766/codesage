"""
Rule-based Code Smell Detector.

Detects the following smells using extracted AST features:
  - Long Method          (LOC per method > 30)
  - God Class            (>10 methods or WMC > 40)
  - Feature Envy         (external_calls >> local_calls)
  - Large Parameter List  (params > 5)
  - Deep Nesting         (nesting depth > 3)
  - High Complexity      (cyclomatic complexity > 10)

Each smell result includes a confidence score (0.0-1.0) computed from
how far the metric exceeds the threshold — using sigmoid normalization
so the score is interpretable as a probability.

Integrates with the existing CodeReviewAgent via agent_orchestrator.py.
"""

import math
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from analyzers.feature_extractor import FeatureExtractor, FileFeatures, MethodFeatures, ClassFeatures


# ─── Smell Thresholds (tunable) ─────────────────────────────────────────────

THRESHOLDS = {
    "long_method":           {"loc": 30},
    "god_class":             {"methods": 10, "wmc": 40},
    "feature_envy":          {"ext_ratio": 0.7},   # >70% external calls
    "large_parameter_list":  {"params": 5},
    "deep_nesting":          {"depth": 3},
    "high_complexity":       {"complexity": 10},
}


# ─── Data Model ──────────────────────────────────────────────────────────────

@dataclass
class SmellResult:
    """A single detected code smell."""
    smell: str                    # Smell identifier (snake_case)
    display_name: str             # Human-readable name
    confidence: float             # 0.0 → 1.0 probability
    location: str                 # e.g. "Class.method" or "function_name"
    start_line: int
    end_line: int
    metric_value: Any             # The raw metric that triggered the smell
    threshold: Any                # The threshold that was exceeded
    refactor_hint: str            # Short suggestion for fixing it
    severity: str                 # "error" | "warning" | "info"


# ─── Main Detector ───────────────────────────────────────────────────────────

class SmellDetector:
    """
    Detects code smells from Python source code.

    Usage:
        detector = SmellDetector()
        smells = detector.detect(source_code)

    Each returned SmellResult has a confidence score so it can feed
    directly into the ML service pipeline or be used standalone.
    """

    def __init__(self):
        self._extractor = FeatureExtractor()

    def detect(self, code: str) -> List[SmellResult]:
        """
        Run all smell checks on the given source code.

        Args:
            code: Python source as string

        Returns:
            List of SmellResult objects (may be empty)
        """
        features = self._extractor.extract(code)
        if features is None:
            return []

        smells: List[SmellResult] = []

        # Check standalone functions
        for fn in features.standalone_functions:
            smells.extend(self._check_method_smells(fn, parent_name=None))

        # Check classes and their methods
        for cls in features.classes:
            smells.extend(self._check_class_smells(cls))
            for method in cls.methods:
                smells.extend(self._check_method_smells(method, parent_name=cls.name))

        # Sort by confidence descending
        smells.sort(key=lambda s: s.confidence, reverse=True)
        return smells

    def detect_to_dict(self, code: str) -> List[Dict[str, Any]]:
        """Detect smells and return serializable dicts."""
        return [_smell_to_dict(s) for s in self.detect(code)]

    # ─── Per-Method Checks ───────────────────────────────────────────────────

    def _check_method_smells(
        self, fn: MethodFeatures, parent_name: Optional[str]
    ) -> List[SmellResult]:
        smells = []
        location = f"{parent_name}.{fn.name}" if parent_name else fn.name

        smells.extend(self._check_long_method(fn, location))
        smells.extend(self._check_large_params(fn, location))
        smells.extend(self._check_deep_nesting(fn, location))
        smells.extend(self._check_high_complexity(fn, location))
        smells.extend(self._check_feature_envy(fn, location))

        return smells

    def _check_long_method(self, fn: MethodFeatures, location: str) -> List[SmellResult]:
        smells = []
        if fn.loc > THRESHOLDS["long_method"]["loc"]:
            excess = fn.loc - THRESHOLDS["long_method"]["loc"]
            confidence = _sigmoid(excess, scale=20)
            smells.append(SmellResult(
                smell="long_method", display_name="Long Method", confidence=round(confidence, 3), location=location,
                start_line=fn.start_line, end_line=fn.end_line, metric_value=fn.loc, threshold=THRESHOLDS["long_method"]["loc"],
                refactor_hint="Extract sub-routines using the 'Extract Method' refactoring.",
                severity="warning" if fn.loc < 60 else "error",
            ))
        return smells

    def _check_large_params(self, fn: MethodFeatures, location: str) -> List[SmellResult]:
        smells = []
        if fn.params > THRESHOLDS["large_parameter_list"]["params"]:
            excess = fn.params - THRESHOLDS["large_parameter_list"]["params"]
            confidence = _sigmoid(excess, scale=3)
            smells.append(SmellResult(
                smell="large_parameter_list", display_name="Large Parameter List", confidence=round(confidence, 3), location=location,
                start_line=fn.start_line, end_line=fn.end_line, metric_value=fn.params, threshold=THRESHOLDS["large_parameter_list"]["params"],
                refactor_hint="Introduce a Parameter Object or Builder pattern.", severity="warning",
            ))
        return smells

    def _check_deep_nesting(self, fn: MethodFeatures, location: str) -> List[SmellResult]:
        smells = []
        if fn.max_nesting_depth > THRESHOLDS["deep_nesting"]["depth"]:
            excess = fn.max_nesting_depth - THRESHOLDS["deep_nesting"]["depth"]
            confidence = _sigmoid(excess, scale=2)
            smells.append(SmellResult(
                smell="deep_nesting", display_name="Deep Nesting", confidence=round(confidence, 3), location=location,
                start_line=fn.start_line, end_line=fn.end_line, metric_value=fn.max_nesting_depth, threshold=THRESHOLDS["deep_nesting"]["depth"],
                refactor_hint="Flatten using early returns or extract nested blocks into separate methods.", severity="warning",
            ))
        return smells

    def _check_high_complexity(self, fn: MethodFeatures, location: str) -> List[SmellResult]:
        smells = []
        if fn.complexity > THRESHOLDS["high_complexity"]["complexity"]:
            excess = fn.complexity - THRESHOLDS["high_complexity"]["complexity"]
            confidence = _sigmoid(excess, scale=5)
            smells.append(SmellResult(
                smell="high_complexity", display_name="High Cyclomatic Complexity", confidence=round(confidence, 3), location=location,
                start_line=fn.start_line, end_line=fn.end_line, metric_value=fn.complexity, threshold=THRESHOLDS["high_complexity"]["complexity"],
                refactor_hint="Simplify branches: extract conditions, use polymorphism, or redesign logic.",
                severity="error" if fn.complexity > 20 else "warning",
            ))
        return smells

    def _check_feature_envy(self, fn: MethodFeatures, location: str) -> List[SmellResult]:
        smells = []
        total_calls = fn.local_calls + fn.external_calls
        if total_calls >= 3:
            ext_ratio = fn.external_calls / total_calls
            thresh = THRESHOLDS["feature_envy"]["ext_ratio"]
            if ext_ratio > thresh:
                excess = ext_ratio - thresh
                confidence = _sigmoid(excess * 10, scale=3)
                smells.append(SmellResult(
                    smell="feature_envy", display_name="Feature Envy", confidence=round(confidence, 3), location=location,
                    start_line=fn.start_line, end_line=fn.end_line, metric_value=round(ext_ratio, 2), threshold=thresh,
                    refactor_hint="Move the method closer to the data it uses via 'Move Method' refactoring.", severity="warning",
                ))
        return smells

    # ─── Per-Class Checks ────────────────────────────────────────────────────

    def _check_class_smells(self, cls: ClassFeatures) -> List[SmellResult]:
        smells = []

        # God Class (method count)
        if cls.num_methods > THRESHOLDS["god_class"]["methods"]:
            excess = cls.num_methods - THRESHOLDS["god_class"]["methods"]
            confidence = _sigmoid(excess, scale=5)
            smells.append(SmellResult(
                smell="god_class",
                display_name="God Class",
                confidence=round(confidence, 3),
                location=cls.name,
                start_line=cls.start_line,
                end_line=cls.end_line,
                metric_value=cls.num_methods,
                threshold=THRESHOLDS["god_class"]["methods"],
                refactor_hint="Split the class by responsibility using the Single Responsibility Principle.",
                severity="error" if cls.num_methods > 20 else "warning",
            ))

        # God Class (WMC)
        elif cls.wmc > THRESHOLDS["god_class"]["wmc"]:
            excess = cls.wmc - THRESHOLDS["god_class"]["wmc"]
            confidence = _sigmoid(excess, scale=20)
            smells.append(SmellResult(
                smell="god_class",
                display_name="God Class (High WMC)",
                confidence=round(confidence, 3),
                location=cls.name,
                start_line=cls.start_line,
                end_line=cls.end_line,
                metric_value=cls.wmc,
                threshold=THRESHOLDS["god_class"]["wmc"],
                refactor_hint="Decompose complex methods and distribute responsibilities across smaller classes.",
                severity="error",
            ))

        return smells


# ─── Utilities ───────────────────────────────────────────────────────────────

def _sigmoid(x: float, scale: float = 1.0) -> float:
    """
    Sigmoid function normalized to give ~0.5 when x=0, ~1.0 as x→ scale.
    Used to convert raw excess over threshold into a 0-1 probability.
    """
    return 1.0 / (1.0 + math.exp(-x / scale))


def _smell_to_dict(s: SmellResult) -> Dict[str, Any]:
    return {
        "smell": s.smell,
        "display_name": s.display_name,
        "confidence": s.confidence,
        "location": s.location,
        "start_line": s.start_line,
        "end_line": s.end_line,
        "metric_value": s.metric_value,
        "threshold": s.threshold,
        "refactor_hint": s.refactor_hint,
        "severity": s.severity,
    }
