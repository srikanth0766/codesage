#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
#  CodeSage — Master Test Runner
#  Usage: bash run_all_tests.sh [--fast | --coverage | --report-only]
# ═══════════════════════════════════════════════════════════════════════════════
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR"
TESTS_DIR="$BACKEND_DIR/tests"
REPORT_FILE="$TESTS_DIR/integrity_report.txt"
JSON_REPORT="$TESTS_DIR/test_report.json"
PYTEST_JSON="$TESTS_DIR/pytest_results.json"

FAST_MODE=false
COVERAGE=true
REPORT_ONLY=false

for arg in "$@"; do
  case $arg in
    --fast)        FAST_MODE=true ;;
    --no-coverage) COVERAGE=false ;;
    --report-only) REPORT_ONLY=true ;;
  esac
done

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║         CodeSage — AUTOMATED TESTING & INTEGRITY SUITE          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

cd "$BACKEND_DIR"

# ── Step 1: Install test dependencies ────────────────────────────────────────
if [[ "$REPORT_ONLY" == "false" ]]; then
  echo "▶ Checking test dependencies..."
  pip install --quiet pytest pytest-asyncio pytest-cov httpx psutil scikit-learn networkx pytest-json-report 2>/dev/null || true
  echo "  ✓ Dependencies ready"
  echo ""
fi

# ── Step 2: Run pytest ───────────────────────────────────────────────────────
if [[ "$REPORT_ONLY" == "false" ]]; then
  echo "▶ Running test suite..."
  echo ""

  PYTEST_ARGS=(
    "tests/"
    "--tb=short"
    "-v"
    "--ignore=tests/fixtures"
    "--json-report"
    "--json-report-file=$PYTEST_JSON"
  )

  if [[ "$COVERAGE" == "true" ]]; then
    PYTEST_ARGS+=(
      "--cov=."
      "--cov-report=term-missing"
      "--cov-report=json:tests/coverage.json"
    )
  fi

  if [[ "$FAST_MODE" == "true" ]]; then
    # Skip slow tests in fast mode
    PYTEST_ARGS+=("-m" "not slow")
    echo "  ⚡ Fast mode: skipping @pytest.mark.slow tests"
  fi

  set +e
  python3 -m pytest "${PYTEST_ARGS[@]}" 2>&1 | tee /tmp/codesage_test_output.txt
  PYTEST_EXIT=$?
  set -e

  echo ""
  if [[ $PYTEST_EXIT -eq 0 ]]; then
    echo "  ✅ All tests passed"
  elif [[ $PYTEST_EXIT -eq 1 ]]; then
    echo "  ⚠️  Some tests failed — check output above"
  else
    echo "  ❌ pytest error (exit code $PYTEST_EXIT)"
  fi
  echo ""
fi

# ── Step 3: Generate report ───────────────────────────────────────────────────
echo "▶ Generating integrity report..."
set +e
python3 tests/generate_report.py
REPORT_EXIT=$?
set -e

echo ""

# ── Step 4: Show report ────────────────────────────────────────────────────────
if [[ -f "$REPORT_FILE" ]]; then
  cat "$REPORT_FILE"
fi

# ── Step 5: Coverage summary ───────────────────────────────────────────────────
if [[ -f "$TESTS_DIR/coverage.json" ]] && [[ "$COVERAGE" == "true" ]]; then
  echo ""
  echo "▶ Test Coverage Summary"
  TOTAL_COV=$(python3 -c "
import json
with open('tests/coverage.json') as f:
    data = json.load(f)
print(f\"{data.get('totals', {}).get('percent_covered', 0):.1f}%\")
" 2>/dev/null || echo "N/A")
  echo "  Total coverage: $TOTAL_COV"
fi

echo ""
echo "══════════════════════════════════════════════════════════════"
echo "  Reports saved to:"
echo "    • $JSON_REPORT"
echo "    • $REPORT_FILE"
if [[ "$COVERAGE" == "true" ]]; then
  echo "    • $TESTS_DIR/coverage.json"
fi
echo "══════════════════════════════════════════════════════════════"

exit $REPORT_EXIT
