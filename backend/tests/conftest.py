"""
Shared fixtures for the CodeSage test suite.

All fixtures are available globally via conftest.py auto-discovery.
"""

import ast
import sys
import os
import pytest
import pytest_asyncio

# ─── Path setup ──────────────────────────────────────────────────────────────
# Ensure backend package is importable regardless of cwd
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

# ─── Code Snippets ───────────────────────────────────────────────────────────

CLEAN_CODE = """\
def add(a: int, b: int) -> int:
    return a + b

def greet(name: str) -> str:
    return f"Hello, {name}!"
"""

LONG_METHOD_CODE = """\
def very_long_function(x):
    result = 0
    # 35+ lines of logic
    result += x * 1
    result += x * 2
    result += x * 3
    result += x * 4
    result += x * 5
    result += x * 6
    result += x * 7
    result += x * 8
    result += x * 9
    result += x * 10
    result += x * 11
    result += x * 12
    result += x * 13
    result += x * 14
    result += x * 15
    result += x * 16
    result += x * 17
    result += x * 18
    result += x * 19
    result += x * 20
    result += x * 21
    result += x * 22
    result += x * 23
    result += x * 24
    result += x * 25
    result += x * 26
    result += x * 27
    result += x * 28
    result += x * 29
    result += x * 30
    result += x * 31
    result += x * 32
    return result
"""

GOD_CLASS_CODE = """\
class GodClass:
    def method1(self): pass
    def method2(self): pass
    def method3(self): pass
    def method4(self): pass
    def method5(self): pass
    def method6(self): pass
    def method7(self): pass
    def method8(self): pass
    def method9(self): pass
    def method10(self): pass
    def method11(self): pass
    def method12(self): pass
"""

DEEP_NESTING_CODE = """\
def deeply_nested(a, b, c, d, e):
    if a:
        if b:
            if c:
                if d:
                    if e:
                        return True
    return False
"""

HIGH_COMPLEXITY_CODE = """\
def complex_func(a, b, c, d, e, f, g, h, i, j, k):
    if a and b:
        pass
    if c or d:
        pass
    for x in range(10):
        if e:
            pass
    while f:
        if g:
            pass
    if h:
        pass
    if i:
        pass
    if j:
        pass
    if k:
        pass
    return 0
"""

LARGE_PARAM_CODE = """\
def big_params(a, b, c, d, e, f, g):
    return a + b + c + d + e + f + g
"""

MALFORMED_CODE = """\
def broken(:
    return
"""

INVALID_SYNTAX_CODE = "x = @"

UNICODE_CODE = "café = 'coffee'\nnaïve = True\n"


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def clean_code():
    return CLEAN_CODE

@pytest.fixture
def long_method_code():
    return LONG_METHOD_CODE

@pytest.fixture
def god_class_code():
    return GOD_CLASS_CODE

@pytest.fixture
def deep_nesting_code():
    return DEEP_NESTING_CODE

@pytest.fixture
def high_complexity_code():
    return HIGH_COMPLEXITY_CODE

@pytest.fixture
def large_param_code():
    return LARGE_PARAM_CODE

@pytest.fixture
def malformed_code():
    return MALFORMED_CODE

@pytest.fixture
def smell_detector():
    from analyzers.smell_detector import SmellDetector
    return SmellDetector()

@pytest.fixture
def feature_extractor():
    from analyzers.feature_extractor import FeatureExtractor
    return FeatureExtractor()

@pytest.fixture
def ast_analyzer_python():
    from analyzers.universal_ast_analyzer import UniversalASTAnalyzer
    return UniversalASTAnalyzer("python")

@pytest.fixture
def sprint_risk_model():
    from agile_risk.sprint_risk_model import SprintRiskModel
    return SprintRiskModel()

@pytest.fixture
def refactor_agent_no_llm():
    """RefactorAgent with LLM explicitly disabled."""
    from refactor_agent.refactor_agent import RefactorAgent
    agent = RefactorAgent.__new__(RefactorAgent)
    agent._llm = None
    return agent

@pytest_asyncio.fixture
async def async_client():
    """Async HTTP client for FastAPI endpoint testing."""
    import httpx
    from main import app
    async with httpx.AsyncClient(app=app, base_url="http://testserver") as client:
        yield client
