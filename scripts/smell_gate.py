#!/usr/bin/env python3
"""
CodeSage CI/CD Smell Gate CLI.

Usage:
    python scripts/smell_gate.py <file_or_directory> [--threshold 0.75] [--ci]

Exit codes:
    0 = passed (no smells above threshold)
    1 = failed (high-confidence smell found)

In CI mode (--ci) it writes smell_report.json for artifact upload.
"""

import sys
import os
import json
import argparse
import requests
from pathlib import Path
from typing import List, Dict

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
SMELL_ENDPOINT = f"{BACKEND_URL}/analyze-smells"


def collect_python_files(path: str) -> List[Path]:
    """Collect all .py files from a path (file or directory)."""
    p = Path(path)
    if p.is_file() and p.suffix == ".py":
        return [p]
    elif p.is_dir():
        return [f for f in p.rglob("*.py") if not any(
            part.startswith(".") or part in ("venv", ".venv", "__pycache__", "node_modules")
            for part in f.parts
        )]
    return []


def analyze_file(file_path: Path, threshold: float) -> Dict:
    """Send file to backend and return smell analysis."""
    code = file_path.read_text(encoding="utf-8", errors="ignore")
    try:
        resp = requests.post(
            SMELL_ENDPOINT,
            json={"code": code, "language": "python"},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        data["file"] = str(file_path)
        data["failed"] = data["overall_smell_score"] > threshold
        return data
    except requests.ConnectionError:
        print(f"  ✗ Cannot connect to backend at {BACKEND_URL}")
        print("    Start the backend first: cd backend && python main.py")
        sys.exit(2)
    except Exception as e:
        return {
            "file": str(file_path),
            "error": str(e),
            "failed": False,
            "smells": [],
            "smell_count": 0,
            "overall_smell_score": 0,
        }


def main():
    parser = argparse.ArgumentParser(
        description="CodeSage Smell Gate — CI/CD threshold checker"
    )
    parser.add_argument("path", help="File or directory to analyse")
    parser.add_argument(
        "--threshold", type=float, default=0.75,
        help="Smell confidence threshold to fail on (default: 0.75)"
    )
    parser.add_argument(
        "--ci", action="store_true",
        help="Write smell_report.json for CI artifact upload"
    )
    args = parser.parse_args()

    files = collect_python_files(args.path)
    if not files:
        print(f"No Python files found at: {args.path}")
        sys.exit(0)

    print(f"\n🔍 CodeSage Smell Gate")
    print(f"   Threshold : {args.threshold}")
    print(f"   Files     : {len(files)}\n")

    results = []
    any_failed = False

    for f in files:
        print(f"  Analysing {f.name} ...", end="  ")
        result = analyze_file(f, args.threshold)
        results.append(result)

        if result.get("error"):
            print(f"⚠️  error: {result['error']}")
            continue

        score = result["overall_smell_score"]
        count = result["smell_count"]
        mark = "❌ FAIL" if result["failed"] else "✅ PASS"
        print(f"{mark}  score={score:.3f}  smells={count}")

        if result["failed"]:
            any_failed = True
            high = [
                s for s in result.get("smells", [])
                if s["confidence"] > args.threshold
            ]
            for s in high:
                print(
                    f"      └─ {s['display_name']} @ {s['location']}  "
                    f"confidence={s['confidence']:.2%}  line {s['start_line']}"
                )

    if args.ci:
        report_path = Path("smell_report.json")
        report_path.write_text(json.dumps({"results": results, "threshold": args.threshold}, indent=2))
        print(f"\n📄 Report written to {report_path}")

    print()
    if any_failed:
        print("❌ GATE FAILED — high-confidence code smells exceed threshold.")
        print("   Fix the smells above or run:  POST /refactor")
        sys.exit(1)
    else:
        print("✅ GATE PASSED — all files within smell threshold.")
        sys.exit(0)


if __name__ == "__main__":
    main()
