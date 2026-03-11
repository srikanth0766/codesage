"""
Ollama LLM provider implementation.
Uses local Llama models via Ollama for code analysis.
"""

import requests
import json
from typing import List, Dict, Optional
from .base import LLMProvider


class OllamaProvider(LLMProvider):
    """LLM provider using Ollama for local inference."""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2:3b"):
        """
        Initialize Ollama provider.
        
        Args:
            base_url: Ollama API base URL
            model: Model name to use (e.g., "llama3.2:3b", "codellama")
        """
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.timeout = 30  # seconds
    
    def is_available(self) -> bool:
        """Check if Ollama is running and model is available."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return any(m.get("name") == self.model for m in models)
            return False
        except Exception:
            return False
    
    def generate(self, prompt: str) -> str:
        """Public generate method used by RefactorAgent."""
        return self._generate(prompt)

    def _generate(self, prompt: str, system: Optional[str] = None) -> str:
        """
        Generate response from Ollama.
        
        Args:
            prompt: User prompt
            system: Optional system message
            
        Returns:
            Generated text response
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,  # Lower temperature for more focused responses
                "top_p": 0.9,
            }
        }
        
        if system:
            payload["system"] = system
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json().get("response", "")
            else:
                return ""
        
        except Exception as e:
            print(f"Ollama generation error: {e}")
            return ""
    
    def analyze_logic(self, code: str) -> List[str]:
        """
        Analyze code for logical errors using Ollama.
        
        Args:
            code: Python source code
            
        Returns:
            List of logical concerns
        """
        system_prompt = """You are an expert Python code reviewer focused on finding logical errors.
Analyze code for:
- Edge cases not handled (empty lists, None values, zero division)
- Off-by-one errors in loops
- Incorrect conditional logic
- Potential infinite loops
- Unintended behavior vs likely intent

Return ONLY genuine logical concerns, not style issues.
Format each concern as: "Line X: <brief description>"
If no concerns, return "No logical concerns detected"."""

        user_prompt = f"""Analyze this Python code for logical errors:

```python
{code}
```

List any logical concerns:"""

        response = self._generate(user_prompt, system=system_prompt)
        
        if not response or "no logical concerns" in response.lower():
            return []
        
        # Parse response into list of concerns
        concerns = []
        for line in response.strip().split('\n'):
            line = line.strip()
            if line and not line.startswith('#') and len(line) > 10:
                # Clean up formatting
                line = line.lstrip('-•*123456789. ')
                if line:
                    concerns.append(line)
        
        return concerns[:5]  # Limit to top 5 concerns
    
    def suggest_optimizations(self, code: str) -> List[Dict]:
        """
        Suggest code optimizations using Ollama.
        
        Args:
            code: Python source code
            
        Returns:
            List of optimization suggestions
        """
        system_prompt = """You are an expert Python developer focused on code optimization.
Suggest improvements for:
- Performance (better algorithms, data structures)
- Readability (Pythonic patterns, clearer logic)
- Safety (error handling, bounds checking)

Return suggestions in this exact format:
TYPE | LINE | SUGGESTION | IMPACT | EXAMPLE

Where:
- TYPE: performance, readability, or safety
- LINE: line number or 0 for general
- SUGGESTION: brief description
- IMPACT: expected benefit
- EXAMPLE: short code example (one line)

If no suggestions, return "No optimizations needed"."""

        user_prompt = f"""Suggest optimizations for this Python code:

```python
{code}
```

Provide optimization suggestions:"""

        response = self._generate(user_prompt, system=system_prompt)
        
        if not response or "no optimizations" in response.lower():
            return []
        
        # Parse response into structured suggestions
        suggestions = []
        for line in response.strip().split('\n'):
            line = line.strip()
            if '|' in line and not line.startswith('#'):
                parts = [p.strip() for p in line.split('|')]
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
        
        return suggestions[:5]  # Limit to top 5 suggestions
