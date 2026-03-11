import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import os
import sys

# Add backend to path to import main
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from main import app

client = TestClient(app)

def test_reset_logs():
    # 1. Ensure action.log has some content
    log_path = Path("action.log")
    with open(log_path, "a") as f:
        f.write("Test log entry\n")
    
    # 2. Verify it's not empty
    assert log_path.exists()
    assert log_path.stat().st_size > 0
    
    # 3. Call reset endpoint
    response = client.post("/logs/reset")
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    # 4. Verify it's empty
    assert log_path.exists()
    assert log_path.stat().st_size == 0

if __name__ == "__main__":
    test_reset_logs()
    print("Test passed!")
