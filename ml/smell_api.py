"""
Heuristic ML Smell Classifier — Standalone FastAPI Microservice.

Runs on port 8001. Takes extracted feature vectors and returns smell probabilities
using sigmoid normalization over rule-based thresholds.

This is the MVP version of the GNN-based smell classifier from the CodeSage blueprint.

# ─── ML TRAINING NOTE ──────────────────────────────────────────────────────────
# In production, replace `_heuristic_score()` with:
#
#   class SmellGNN(torch.nn.Module):
#       def __init__(self):
#           super().__init__()
#           self.conv1 = GCNConv(in_channels, 64)
#           self.conv2 = GCNConv(64, 32)
#           self.fc = torch.nn.Linear(32, num_smells)
#
#       def forward(self, x, edge_index):
#           x = self.conv1(x, edge_index).relu()
#           x = self.conv2(x, edge_index)
#           return torch.sigmoid(self.fc(x))
#
# Training requirements:
#   - Labeled Java/Python smell dataset (e.g. from GitHub or Qualitas Corpus)
#   - torch-geometric >= 2.0
#   - loss = BCEWithLogitsLoss()
#   - optimizer = Adam(model.parameters(), lr=0.001)
#   - Save trained model to: ml/models/smell_gnn.pt
#   - Load at startup with: model = SmellGNN(); model.load_state_dict(torch.load(...))
# ───────────────────────────────────────────────────────────────────────────────
"""

import math
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn


# ─── Thresholds (same as smell_detector.py for consistency) ──────────────────

_T = {
    "loc":        30,
    "params":      5,
    "complexity": 10,
    "nesting":     3,
    "wmc":        40,
    "cbo":         6,
    "ext_ratio":  0.7,
}


def _sigmoid(x: float, scale: float = 1.0) -> float:
    return 1.0 / (1.0 + math.exp(-x / scale))


def _heuristic_score(features: Dict[str, Any]) -> Dict[str, float]:
    """
    Convert raw feature values to 0-1 smell probabilities using sigmoid normalization.

    # TO TRAIN: Replace this function body with a GNN forward pass.
    """
    loc = features.get("loc", 0)
    params = features.get("params", 0)
    complexity = features.get("complexity", 0)
    nesting = features.get("nesting", 0)
    wmc = features.get("wmc", 0)
    cbo = features.get("cbo", 0)
    ext_ratio = features.get("ext_ratio", 0.0)

    return {
        "long_method":          round(_sigmoid(loc - _T["loc"],        scale=20), 3),
        "god_class":            round(_sigmoid(max(wmc - _T["wmc"], 0), scale=20), 3),
        "feature_envy":         round(_sigmoid((ext_ratio - _T["ext_ratio"]) * 10, scale=3), 3),
        "large_parameter_list": round(_sigmoid(params - _T["params"],  scale=3), 3),
        "deep_nesting":         round(_sigmoid(nesting - _T["nesting"], scale=2), 3),
        "high_complexity":      round(_sigmoid(complexity - _T["complexity"], scale=5), 3),
    }


# ─── FastAPI App ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="CodeSage ML Smell Service",
    description=(
        "Heuristic smell probability scorer (MVP). "
        "Replace _heuristic_score() with a trained GNN for production accuracy."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class SmellPredictRequest(BaseModel):
    """Feature vector extracted from source code."""
    features: Dict[str, Any] = Field(
        ...,
        description="Feature dict: loc, params, complexity, nesting, wmc, cbo, ext_ratio",
        example={
            "loc": 80, "params": 6, "complexity": 12,
            "nesting": 4, "wmc": 45, "cbo": 8, "ext_ratio": 0.8
        }
    )


class SmellPredictResponse(BaseModel):
    probabilities: Dict[str, float] = Field(..., description="Per-smell probability 0-1")
    top_smell: str = Field(..., description="Smell with highest probability")
    top_confidence: float = Field(..., description="Highest probability value")
    backend: str = Field(default="heuristic_mvp")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ml-smell-service", "backend": "heuristic_mvp"}


@app.post("/predict-smell", response_model=SmellPredictResponse)
async def predict_smell(request: SmellPredictRequest):
    """
    Predict smell probabilities from feature vector.

    In the full CodeSage, this endpoint receives AST graph JSON and runs it through
    a trained GCN. In this MVP it uses threshold-based sigmoid scoring.
    """
    if not request.features:
        raise HTTPException(status_code=400, detail="features cannot be empty")

    try:
        probs = _heuristic_score(request.features)
        top = max(probs, key=probs.get)
        return SmellPredictResponse(
            probabilities=probs,
            top_smell=top,
            top_confidence=probs[top],
            backend="heuristic_mvp",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
