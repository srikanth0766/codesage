"""
Sprint Risk Model — Stochastic Smell Accumulation Predictor.

Models smell count evolution as:
    S(t+1) = S(t) + λ - μ

Where:
    λ (lambda) = new smell introduction rate  (estimated from sprint history)
    μ (mu)     = refactoring / removal rate   (estimated from refactor history)

Risk probability is computed via Z-score / normal CDF approximation, asking:
    P(S(t+1) > threshold)

This gives the Agile team an early warning of impending technical debt explosion.
"""

import math
import statistics
from typing import Dict, Any, List, Optional


class SprintRiskModel:
    """
    Predicts smell accumulation risk for the next sprint.

    No external dependencies — pure Python stdlib.
    """

    def predict(
        self,
        smell_history: List[int],
        refactor_history: Optional[List[int]] = None,
        threshold: int = 10,
    ) -> Dict[str, Any]:
        """
        Predict risk that smell count exceeds threshold in next sprint.

        Args:
            smell_history:    List of smell counts per sprint (oldest first)
            refactor_history: List of refactoring counts per sprint (optional)
            threshold:        Maximum acceptable smell count

        Returns:
            Dict with keys: risk_probability, predicted_smell_count,
                            threshold, trend, recommendation
        """
        refactor_history = refactor_history or []

        # Estimate λ: average increase per sprint
        deltas = [
            smell_history[i] - smell_history[i - 1]
            for i in range(1, len(smell_history))
        ]
        lambda_rate = max(statistics.mean(deltas), 0) if deltas else 0

        # Estimate μ: average refactorings per sprint
        mu_rate = statistics.mean(refactor_history) if refactor_history else 0

        # Net drift per sprint
        drift = lambda_rate - mu_rate

        # Currently observed smell count
        current = smell_history[-1]

        # Predicted count next sprint
        predicted = max(current + drift, 0)

        # Variance: use std dev of deltas (captures process noise)
        if len(deltas) >= 2:
            sigma = statistics.stdev(deltas)
        else:
            sigma = max(abs(drift) * 0.5, 1.0)  # Fallback estimate

        # P(S > threshold) using normal CDF approximation
        risk_prob = self._p_exceed(predicted, sigma, threshold)

        # Classify trend
        trend = self._classify_trend(drift, predicted, threshold)

        # Recommendation
        recommendation = self._recommendation(risk_prob, drift, threshold, predicted)

        return {
            "risk_probability": round(min(risk_prob, 1.0), 4),
            "predicted_smell_count": round(predicted, 2),
            "threshold": threshold,
            "trend": trend,
            "recommendation": recommendation,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _p_exceed(self, mu: float, sigma: float, threshold: int) -> float:
        """
        P(X > threshold) where X ~ Normal(mu, sigma).
        Uses Python's math.erfc for the complementary error function.
        """
        if sigma <= 0:
            return 1.0 if mu > threshold else 0.0
        z = (threshold - mu) / (sigma * math.sqrt(2))
        return 0.5 * math.erfc(z)

    def _classify_trend(self, drift: float, predicted: float, threshold: int) -> str:
        """Return a human-readable trend label."""
        if drift > 2:
            return "rapidly_increasing"
        elif drift > 0:
            return "increasing"
        elif drift < -1:
            return "improving"
        elif predicted > threshold:
            return "above_threshold"
        else:
            return "stable"

    def _recommendation(
        self, risk: float, drift: float, threshold: int, predicted: float
    ) -> str:
        """Generate actionable Agile sprint recommendation."""
        if risk > 0.8:
            return (
                "🚨 CRITICAL: High probability of smell explosion next sprint. "
                "Dedicate at least 30% of sprint capacity to refactoring. "
                "Consider a tech debt sprint."
            )
        elif risk > 0.5:
            return (
                "⚠️ WARNING: Smell density trending toward unsafe levels. "
                "Include refactoring tasks in the next sprint backlog. "
                "Target 2-3 high-confidence smells for cleanup."
            )
        elif drift > 0:
            return (
                "📈 Smells increasing. Monitor closely in sprint review. "
                "Ensure code reviews flag new smells before merge."
            )
        else:
            return (
                "✅ Smell rate is stable or improving. "
                "Continue current code review and refactoring practices."
            )
