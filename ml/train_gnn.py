"""
CodeSage ML Training Stub — GNN Smell Classifier.

This file documents the FULL ML training pipeline for when you are ready to
replace the heuristic scorer in smell_api.py with a trained GNN.

HOW TO USE:
  1. Prepare a labeled dataset (see Dataset section below)
  2. Install: pip install torch torch-geometric networkx
  3. Run: python train_gnn.py
  4. The trained model is saved to: ml/models/smell_gnn.pt
  5. In smell_api.py, uncomment the GNN inference code

──────────────────────────────────────────────────────────────────────────────
DATASET OPTIONS (publicly available):
  - Qualitas Corpus:  https://qualitascorpus.com/
  - PMD smell labels: https://pmd.github.io/
  - MLCQ dataset:     https://github.com/atlanmod/MLCQ
  - SmellDetector:    https://github.com/tsantalis/RefactoringMiner

Expected CSV format (smell_dataset.csv):
  file_id, smell_label, loc, params, complexity, nesting, wmc, cbo, ext_ratio
  1, long_method, 82, 3, 14, 5, 0, 0, 0.3
  2, god_class, 25, 2, 3, 2, 55, 9, 0.5
  ...
──────────────────────────────────────────────────────────────────────────────
"""

# ──────────────────────────────────────────────────────────────────────────────
# 1. IMPORTS (uncomment when ready to train)
# ──────────────────────────────────────────────────────────────────────────────

# import torch
# import torch.nn as nn
# import torch.nn.functional as F
# from torch_geometric.nn import GCNConv
# from torch_geometric.data import Data, DataLoader
# import networkx as nx
# import pandas as pd
# import numpy as np
# from pathlib import Path

SMELL_LABELS = [
    "long_method",
    "god_class",
    "feature_envy",
    "large_parameter_list",
    "deep_nesting",
    "high_complexity",
]
NUM_SMELLS    = len(SMELL_LABELS)
IN_CHANNELS   = 7   # Number of features: loc, params, complexity, nesting, wmc, cbo, ext_ratio


# ──────────────────────────────────────────────────────────────────────────────
# 2. MODEL DEFINITION
# ──────────────────────────────────────────────────────────────────────────────

# class SmellGNN(torch.nn.Module):
#     """
#     Graph Convolutional Network for multi-label smell classification.
#     Input:  AST feature vectors (N nodes x IN_CHANNELS features)
#     Output: Per-smell probabilities (sigmoid)
#     """
#     def __init__(self):
#         super().__init__()
#         self.conv1 = GCNConv(IN_CHANNELS, 64)
#         self.conv2 = GCNConv(64, 32)
#         self.fc    = nn.Linear(32, NUM_SMELLS)
#         self.dropout = nn.Dropout(0.3)
#
#     def forward(self, x, edge_index):
#         x = self.conv1(x, edge_index).relu()
#         x = self.dropout(x)
#         x = self.conv2(x, edge_index).relu()
#         # Global mean pooling to get graph-level representation
#         x = x.mean(dim=0, keepdim=True)
#         return torch.sigmoid(self.fc(x))


# ──────────────────────────────────────────────────────────────────────────────
# 3. TRAINING LOOP
# ──────────────────────────────────────────────────────────────────────────────

# def train():
#     df = pd.read_csv("ml/datasets/smell_dataset.csv")
#
#     # Build PyG Data objects from feature rows
#     graphs = []
#     for _, row in df.iterrows():
#         features = torch.tensor([[
#             row["loc"], row["params"], row["complexity"],
#             row["nesting"], row["wmc"], row["cbo"], row["ext_ratio"]
#         ]], dtype=torch.float)
#
#         # Minimal graph: single node (can extend to class/method hierarchy)
#         edge_index = torch.zeros((2, 0), dtype=torch.long)
#
#         label = torch.zeros(NUM_SMELLS)
#         if row["smell_label"] in SMELL_LABELS:
#             label[SMELL_LABELS.index(row["smell_label"])] = 1.0
#
#         graphs.append(Data(x=features, edge_index=edge_index, y=label.unsqueeze(0)))
#
#     loader = DataLoader(graphs, batch_size=32, shuffle=True)
#
#     model     = SmellGNN()
#     optimizer = torch.optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-4)
#     criterion = nn.BCEWithLogitsLoss()
#
#     for epoch in range(50):
#         model.train()
#         total_loss = 0
#         for batch in loader:
#             optimizer.zero_grad()
#             out  = model(batch.x, batch.edge_index)
#             loss = criterion(out, batch.y.float())
#             loss.backward()
#             optimizer.step()
#             total_loss += loss.item()
#         print(f"Epoch {epoch+1:3d} | Loss: {total_loss/len(loader):.4f}")
#
#     Path("ml/models").mkdir(parents=True, exist_ok=True)
#     torch.save(model.state_dict(), "ml/models/smell_gnn.pt")
#     print("✅ Model saved to ml/models/smell_gnn.pt")


# ──────────────────────────────────────────────────────────────────────────────
# 4. INFERENCE REPLACEMENT FOR smell_api.py
# ──────────────────────────────────────────────────────────────────────────────

# In smell_api.py, replace _heuristic_score() with:
#
# _model = SmellGNN()
# _model.load_state_dict(torch.load("ml/models/smell_gnn.pt", map_location="cpu"))
# _model.eval()
#
# def _gnn_score(features: dict) -> dict:
#     x = torch.tensor([[
#         features.get("loc", 0), features.get("params", 0),
#         features.get("complexity", 0), features.get("nesting", 0),
#         features.get("wmc", 0), features.get("cbo", 0),
#         features.get("ext_ratio", 0.0)
#     ]], dtype=torch.float)
#     edge_index = torch.zeros((2, 0), dtype=torch.long)
#     with torch.no_grad():
#         probs = _model(x, edge_index).squeeze().tolist()
#     return dict(zip(SMELL_LABELS, [round(p, 3) for p in probs]))


if __name__ == "__main__":
    print("CodeSage GNN Training Stub")
    print("Uncomment the training code above and ensure you have:")
    print("  pip install torch torch-geometric pandas networkx")
    print("  ml/datasets/smell_dataset.csv (labeled smell data)")
    print("\nCurrent backend uses heuristic sigmoid scoring (no training needed).")
    print(f"Smell labels: {SMELL_LABELS}")
