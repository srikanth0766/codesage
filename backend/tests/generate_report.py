#!/usr/bin/env python3
"""
CodeSage Test Report Generator.

Reads pytest JSON output (coverage.json) and generates:
  - tests/test_report.json  — per-category results
  - tests/integrity_report.txt — human-readable final score

Usage:
    cd backend
    python tests/generate_report.py
"""

import json
import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path


# ─── Category Definitions ────────────────────────────────────────────────────

CATEGORIES = {
    "1_compiler_core":          ["test_lexical_analysis", "test_syntax_analysis", "test_ast_integrity"],
    "2_feature_extraction":     ["test_feature_extractor"],
    "3_ml_model":               ["test_ml_model"],
    "4_smell_detector":         ["test_smell_detector"],
    "5_refactor_safety":        ["test_refactor_safety"],
    "6_ci_gatekeeper":          ["test_ci_gatekeeper"],
    "7_agile_risk":             ["test_sprint_risk_model"],
    "8_performance":            ["test_performance"],
    "9_security":               ["test_security"],
    "10_data_integrity":        ["test_data_integrity"],
    "11_chaos":                 ["test_chaos"],
    "12_e2e":                   ["test_e2e"],
    "13_regression":            ["test_regression"],
    "14_observability":         ["test_observability"],
    "15_acceptance":            ["test_acceptance"],
}

TESTS_DIR = Path(__file__).parent
BACKEND_DIR = TESTS_DIR.parent


def run_pytest_json() -> dict:
    """Run pytest with JSON report output and return parsed results."""
    result_file = TESTS_DIR / "pytest_results.json"
    cmd = [
        sys.executable, "-m", "pytest",
        str(TESTS_DIR),
        "--tb=no",
        "-q",
        f"--json-report",
        f"--json-report-file={result_file}",
        "--ignore=" + str(TESTS_DIR / "fixtures"),
        "--no-header",
    ]

    try:
        subprocess.run(cmd, cwd=str(BACKEND_DIR), capture_output=True)
    except Exception:
        pass

    if result_file.exists():
        with open(result_file) as f:
            return json.load(f)
    return {}


def parse_category_results(pytest_data: dict) -> dict:
    """Map test results to categories."""
    category_results = {}
    tests = pytest_data.get("tests", [])

    for cat_name, file_prefixes in CATEGORIES.items():
        cat_tests = []
        for test in tests:
            node_id = test.get("nodeid", "")
            if any(prefix in node_id for prefix in file_prefixes):
                cat_tests.append(test)

        passed = sum(1 for t in cat_tests if t.get("outcome") == "passed")
        failed = sum(1 for t in cat_tests if t.get("outcome") == "failed")
        skipped = sum(1 for t in cat_tests if t.get("outcome") == "skipped")
        total = max(len(cat_tests), 1)

        category_results[cat_name] = {
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "total": total,
            "pass_rate": round(passed / total, 4),
            "status": "PASS" if failed == 0 else "FAIL",
        }

    return category_results


def compute_integrity_score(category_results: dict) -> float:
    """Compute weighted overall integrity score."""
    weights = {
        "1_compiler_core":      0.15,
        "2_feature_extraction": 0.10,
        "3_ml_model":           0.10,
        "4_smell_detector":     0.10,
        "5_refactor_safety":    0.15,
        "6_ci_gatekeeper":      0.10,
        "7_agile_risk":         0.10,
        "8_performance":        0.05,
        "9_security":           0.05,
        "10_data_integrity":    0.03,
        "11_chaos":             0.03,
        "12_e2e":               0.02,
        "13_regression":        0.01,
        "14_observability":     0.005,
        "15_acceptance":        0.005,
    }
    total = 0.0
    for cat, data in category_results.items():
        w = weights.get(cat, 0.01)
        total += data["pass_rate"] * w
    return round(total, 4)


def write_json_report(category_results: dict, score: float) -> Path:
    """Write JSON report."""
    report = {
        "generated_at": datetime.utcnow().isoformat(),
        "overall_integrity_score": score,
        "acceptance_threshold": 0.80,
        "accepted": score >= 0.80,
        "categories": category_results,
    }
    out = TESTS_DIR / "test_report.json"
    with open(out, "w") as f:
        json.dump(report, f, indent=2)
    return out


def write_text_report(category_results: dict, score: float) -> Path:
    """Write human-readable integrity report."""
    lines = [
        "=" * 65,
        "  CodeSage — SYSTEM INTEGRITY REPORT",
        f"  Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC",
        "=" * 65,
        "",
        f"  {'CATEGORY':<35} {'PASS':>6} {'FAIL':>6} {'SKIP':>6}  STATUS",
        "  " + "─" * 60,
    ]

    for cat, data in category_results.items():
        cat_label = cat.replace("_", " ").title()[:34]
        status_icon = "✅" if data["status"] == "PASS" else "❌"
        lines.append(
            f"  {cat_label:<35} {data['passed']:>6} {data['failed']:>6} "
            f"{data['skipped']:>6}  {status_icon} {data['status']}"
        )

    lines += [
        "",
        "  " + "─" * 60,
        f"  {'OVERALL INTEGRITY SCORE':<42} {score:.2%}",
        f"  {'ACCEPTANCE THRESHOLD':<42} 80.00%",
        f"  {'RESULT':<42} {'✅ ACCEPTED' if score >= 0.80 else '❌ NOT ACCEPTED'}",
        "=" * 65,
        "",
    ]

    out = TESTS_DIR / "integrity_report.txt"
    with open(out, "w") as f:
        f.write("\n".join(lines))
    return out


def main():
    print("CodeSage Report Generator")
    print("─" * 40)

    # Try to read existing pytest JSON output
    result_file = TESTS_DIR / "pytest_results.json"
    if result_file.exists():
        with open(result_file) as f:
            pytest_data = json.load(f)
        print(f"✓ Loaded pytest results from {result_file}")
    else:
        print("⚠ No pytest_results.json found. Running pytest...")
        pytest_data = run_pytest_json()

    category_results = parse_category_results(pytest_data)
    score = compute_integrity_score(category_results)

    json_report = write_json_report(category_results, score)
    text_report = write_text_report(category_results, score)

    print(f"✓ JSON report: {json_report}")
    print(f"✓ Text report: {text_report}")
    print()

    # Print summary to stdout
    with open(text_report) as f:
        print(f.read())

    sys.exit(0 if score >= 0.80 else 1)


if __name__ == "__main__":
    main()
