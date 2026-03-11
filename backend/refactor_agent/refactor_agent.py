"""
LLM-based Refactoring Agent.

Uses the existing Ollama LLM provider to apply smell-specific refactoring strategies.
After receiving the LLM suggestion it validates the result by re-parsing with Python AST.
If AST validation fails it rolls back and returns the original code with a failure note.
"""

import ast
import re
from typing import Dict, Any, Optional
from refactor_agent.refactor_rules import get_rule


class RefactorAgent:
    """
    Orchestrates smell refactoring using the existing LLM provider.

    Works offline with Ollama. Falls back gracefully when no LLM is available.
    """

    def __init__(self):
        """Lazily initialise the best available LLM provider."""
        try:
            from llm_providers.factory import get_best_available_provider
            self._llm = get_best_available_provider()
        except Exception as e:
            print(f"RefactorAgent: LLM provider unavailable — {e}")
            self._llm = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def refactor(
        self,
        code: str,
        smell: str,
        confidence: float = 0.8,
    ) -> Dict[str, Any]:
        """
        Attempt to refactor the code to eliminate the given smell.

        Args:
            code:       Python source code
            smell:      Smell identifier (e.g. 'long_method')
            confidence: Smell confidence score (0-1) from detector

        Returns:
            Dict with keys: original_code, refactored_code, smell,
                            strategy, success, notes
        """
        rule = get_rule(smell)
        strategy = rule["strategy"]

        if self._llm is None:
            return self._no_llm_response(code, smell, strategy)

        # Build prompt
        prompt = rule["prompt_template"].format(code=code)

        try:
            raw_response = self._llm.generate(prompt)
            refactored = self._extract_code(raw_response)

            # Validate the refactored code parses correctly
            if self._is_valid_python(refactored):
                return {
                    "original_code": code,
                    "refactored_code": refactored,
                    "smell": smell,
                    "strategy": strategy,
                    "success": True,
                    "notes": (
                        f"Successfully applied '{strategy}' refactoring. "
                        f"AST validation passed. Confidence was {confidence:.2%}."
                    ),
                }
            else:
                # AST failed → rollback
                return {
                    "original_code": code,
                    "refactored_code": code,  # Return original
                    "smell": smell,
                    "strategy": strategy,
                    "success": False,
                    "notes": (
                        "LLM suggestion failed AST validation — rolled back to original. "
                        "Please review the code manually and try again."
                    ),
                }

        except Exception as e:
            return {
                "original_code": code,
                "refactored_code": code,
                "smell": smell,
                "strategy": strategy,
                "success": False,
                "notes": f"LLM error during refactoring: {str(e)}",
            }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _extract_code(self, raw: str) -> str:
        """
        Extract Python code from the LLM response.
        Handles both fenced code blocks and plain text.
        """
        # Try ```python ... ``` block first
        match = re.search(r"```python\s*([\s\S]+?)```", raw)
        if match:
            return match.group(1).strip()

        # Try ``` ... ``` block (no language tag)
        match = re.search(r"```\s*([\s\S]+?)```", raw)
        if match:
            return match.group(1).strip()

        # Fall back to full response
        return raw.strip()

    def _is_valid_python(self, code: str) -> bool:
        """Return True if code parses successfully with Python ast."""
        if not code or not code.strip():
            return False
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False

    def _no_llm_response(self, code: str, smell: str, strategy: str) -> Dict[str, Any]:
        """Response when no LLM is configured."""
        rule = get_rule(smell)
        return {
            "original_code": code,
            "refactored_code": code,
            "smell": smell,
            "strategy": strategy,
            "success": False,
            "notes": (
                f"No LLM available. Recommended strategy: '{strategy}'. "
                f"Hint: {rule.get('description', '')}. "
                "Start Ollama with 'ollama serve' and set OLLAMA_MODEL in .env to enable auto-refactoring."
            ),
        }
