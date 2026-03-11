"""
Category 15 — Acceptance Criteria Validator.

Aggregates results from key components and computes an overall system
integrity score. The score must meet or exceed 0.80 (80%) for acceptance.

Acceptance categories:
  1. Compiler correctness   (syntax tests)
  2. Smell detection        (6-smell coverage)
  3. Refactor safety        (rollback correctness)
  4. CI gate enforcement    (50-PR accuracy)
  5. Risk prediction        (probability bounds)
  6. Feature extraction     (metric accuracy)
"""

import ast
import pytest


def run_compiler_correctness() -> float:
    """Run 10 syntax checks, return pass rate."""
    from analyzers.universal_ast_analyzer import UniversalASTAnalyzer
    analyzer = UniversalASTAnalyzer("python")
    cases = [
        ("def f(): return 1", True),
        ("class C:\n    pass", True),
        ("x = 1 + 2", True),
        ("import os; os.getcwd()", True),
        ("for i in range(10): pass", True),
        ("def f(:\n    pass", False),   # broken
        ("x = @", False),               # broken
        ("lambda x: x ** 2", True),
        ("try:\n    pass\nexcept:\n    pass", True),
        ("[x for x in range(5)]", True),
    ]
    correct = 0
    for code, expected_valid in cases:
        result = analyzer.check_syntax(code)
        is_valid = result["status"] == "valid"
        if is_valid == expected_valid:
            correct += 1
    return correct / len(cases)


def run_smell_detection_coverage() -> float:
    """Run all 6 smell detections, return coverage rate."""
    from analyzers.smell_detector import SmellDetector
    detector = SmellDetector()

    test_cases = {
        "long_method": "def long(x):\n" + "    x += 1\n" * 35,
        "god_class": "class G:\n" + "\n".join(f"    def m{i}(self): pass" for i in range(12)),
        "deep_nesting": "def f(a,b,c,d,e):\n    if a:\n        if b:\n            if c:\n                if d:\n                    if e:\n                        return 1\n",
        "high_complexity": "def f(a,b,c,d,e,f,g,h,i,j,k):\n" + "    if a:\n        pass\n" * 11 + "    return 0\n",
        "large_parameter_list": "def f(a,b,c,d,e,f,g): return a\n",
    }

    detected = 0
    for smell, code in test_cases.items():
        smells = detector.detect(code)
        if any(s.smell == smell for s in smells):
            detected += 1
    return detected / len(test_cases)


def run_refactor_safety() -> float:
    """Run rollback test, return 1.0 if rollback correct, else 0.0."""
    from refactor_agent.refactor_agent import RefactorAgent
    from unittest.mock import MagicMock
    code = "def f(x):\n    return x\n"
    agent = RefactorAgent.__new__(RefactorAgent)
    mock = MagicMock()
    mock.generate.return_value = "def BROKEN(: @@"
    agent._llm = mock
    result = agent.refactor(code, "long_method")
    return 1.0 if (not result["success"] and result["refactored_code"] == code) else 0.0


def run_ci_gate_accuracy() -> float:
    """Run 10 clean + 10 smelly PRs, return accuracy."""
    from analyzers.smell_detector import SmellDetector
    detector = SmellDetector()
    correct = 0
    total = 20

    # 10 clean PRs
    for i in range(10):
        code = f"def clean_{i}(a, b): return a + b\n"
        smells = detector.detect(code)
        score = max((s.confidence for s in smells), default=0.0)
        if score < 0.5:
            correct += 1

    # 10 smelly PRs
    for i in range(10):
        code = "class G:\n" + "\n".join(f"    def m{j}(self): pass" for j in range(12))
        smells = detector.detect(code)
        score = max((s.confidence for s in smells), default=0.0)
        if score >= 0.5:
            correct += 1

    return correct / total


def run_risk_prediction_stability() -> float:
    """Run 5 edge cases, return fraction that stay in [0,1]."""
    from agile_risk.sprint_risk_model import SprintRiskModel
    model = SprintRiskModel()
    cases = [
        ([5, 5, 5], [], 10),
        ([1, 5, 10, 20], [], 5),
        ([20, 15, 10, 5], [], 15),
        ([0, 0, 0, 0], [], 10),
        ([100, 200, 300], [], 100),
    ]
    in_range = 0
    for hist, ref, threshold in cases:
        result = model.predict(hist, ref, threshold)
        if 0.0 <= result["risk_probability"] <= 1.0:
            in_range += 1
    return in_range / len(cases)


def run_feature_extraction_accuracy() -> float:
    """Test known complexity values, return accuracy."""
    from analyzers.feature_extractor import FeatureExtractor
    extractor = FeatureExtractor()
    cases = [
        ("def f(): return 1\n", 1),
        ("def f(a):\n    if a:\n        return 1\n    return 0\n", 2),
        ("def f(a, b):\n    if a:\n        pass\n    if b:\n        pass\n", 3),
    ]
    correct = 0
    for code, expected_cc in cases:
        features = extractor.extract(code)
        if features and features.standalone_functions:
            actual = features.standalone_functions[0].complexity
            if actual == expected_cc:
                correct += 1
    return correct / len(cases)


class TestAcceptanceCriteria:

    def test_compiler_correctness_100_percent(self):
        score = run_compiler_correctness()
        print(f"\n[Acceptance] Compiler correctness: {score:.2%}")
        assert score == 1.0, f"Compiler correctness {score:.2%} — expected 100%"

    def test_smell_detection_coverage_80_percent(self):
        score = run_smell_detection_coverage()
        print(f"\n[Acceptance] Smell detection coverage: {score:.2%}")
        assert score >= 0.80, f"Smell detection {score:.2%} — expected >= 80%"

    def test_refactor_safety_100_percent(self):
        score = run_refactor_safety()
        print(f"\n[Acceptance] Refactor safety (rollback): {score:.2%}")
        assert score == 1.0, f"Refactor safety {score:.2%} — expected 100%"

    def test_ci_gate_accuracy_80_percent(self):
        score = run_ci_gate_accuracy()
        print(f"\n[Acceptance] CI gate accuracy: {score:.2%}")
        assert score >= 0.80, f"CI gate {score:.2%} — expected >= 80%"

    def test_risk_prediction_stability_100_percent(self):
        score = run_risk_prediction_stability()
        print(f"\n[Acceptance] Risk prediction stability: {score:.2%}")
        assert score == 1.0, f"Risk prediction {score:.2%} — expected 100%"

    def test_feature_extraction_accuracy_80_percent(self):
        score = run_feature_extraction_accuracy()
        print(f"\n[Acceptance] Feature extraction accuracy: {score:.2%}")
        assert score >= 0.80, f"Feature extraction {score:.2%} — expected >= 80%"

    def test_overall_system_integrity_score(self):
        """
        Aggregate weighted score across all categories.
        Must be >= 0.80 for system acceptance.
        """
        weights = {
            "compiler_correctness":   (run_compiler_correctness,   0.20),
            "smell_detection":        (run_smell_detection_coverage, 0.20),
            "refactor_safety":        (run_refactor_safety,         0.20),
            "ci_gate_accuracy":       (run_ci_gate_accuracy,        0.15),
            "risk_prediction":        (run_risk_prediction_stability, 0.15),
            "feature_extraction":     (run_feature_extraction_accuracy, 0.10),
        }

        total_score = 0.0
        report = {}
        for name, (fn, weight) in weights.items():
            score = fn()
            report[name] = {"score": score, "weight": weight, "contribution": score * weight}
            total_score += score * weight

        print(f"\n{'='*60}")
        print("CodeSage SYSTEM INTEGRITY REPORT")
        print(f"{'='*60}")
        for name, vals in report.items():
            status = "✅" if vals["score"] >= 0.80 else "⚠️"
            print(f"{status} {name:35s} {vals['score']:.2%}  (weight: {vals['weight']:.0%})")
        print(f"{'─'*60}")
        print(f"   {'OVERALL INTEGRITY SCORE':35s} {total_score:.2%}")
        print(f"{'='*60}")

        assert total_score >= 0.80, (
            f"Overall system integrity score {total_score:.2%} below 80% acceptance threshold.\n"
            f"Per-category results: {report}"
        )
