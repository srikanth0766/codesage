"""
Mistral AI LLM provider implementation.
Uses the mistralai SDK for cloud-based code analysis and refactoring.
"""

from typing import List, Dict, Optional
from .base import LLMProvider


class MistralProvider(LLMProvider):
    """LLM provider using Mistral AI API."""

    def __init__(self, api_key: str, model: str = "mistral-small-latest"):
        self.api_key = api_key
        self.model = model
        self._client = None
        self._init_client()

    def _init_client(self):
        try:
            from mistralai import Mistral
            self._client = Mistral(api_key=self.api_key)
        except Exception as e:
            print(f"MistralProvider: Could not initialize — {e}")
            self._client = None

    def is_available(self) -> bool:
        return self._client is not None and bool(self.api_key)

    def generate(self, prompt: str) -> str:
        """Public generate method used by RefactorAgent."""
        if not self._client:
            return ""
        try:
            response = self._client.chat.complete(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=4096,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            print(f"Mistral generation error: {e}")
            return ""

    def analyze_logic(self, code: str) -> List[str]:
        prompt = (
            "You are an expert Python code reviewer focused on finding logical errors.\n"
            "Analyze code for: edge cases, off-by-one errors, incorrect conditionals, "
            "potential infinite loops, unintended behavior.\n"
            "Return ONLY genuine logical concerns as a list, one per line: 'Line X: <description>'\n"
            "If none, return 'No logical concerns detected'.\n\n"
            f"Code:\n```python\n{code}\n```\n\nList logical concerns:"
        )
        response = self.generate(prompt)
        if not response or "no logical concerns" in response.lower():
            return []
        concerns = []
        for line in response.strip().split("\n"):
            line = line.strip().lstrip("-•*123456789. ")
            if line and len(line) > 10:
                concerns.append(line)
        return concerns[:5]

    def suggest_optimizations(self, code: str) -> List[Dict]:
        prompt = (
            "You are an expert Python developer focused on code optimization.\n"
            "Suggest improvements in this format:\n"
            "TYPE | LINE | SUGGESTION | IMPACT | EXAMPLE\n\n"
            f"Code:\n```python\n{code}\n```\n\nProvide suggestions:"
        )
        response = self.generate(prompt)
        if not response or "no optimizations" in response.lower():
            return []
        suggestions = []
        for line in response.strip().split("\n"):
            if "|" in line and not line.startswith("#"):
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 4:
                    try:
                        suggestions.append({
                            "type": parts[0].lower(),
                            "line": int(parts[1]) if parts[1].isdigit() else 0,
                            "suggestion": parts[2],
                            "impact": parts[3],
                            "example": parts[4] if len(parts) > 4 else ""
                        })
                    except (ValueError, IndexError):
                        continue
        return suggestions[:5]
