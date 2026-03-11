import sys
import os
import ast

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from analyzers.smell_detector import SmellDetector

def test_nonsense_detection():
    code = """def vishnu():
    print("modgud")
vishnu();
hehehehehheee;
"""
    detector = SmellDetector()
    smells = detector.detect(code)
    
    # Check for Useless Statement
    useless_stmts = [s for s in smells if s.smell == "useless_statement"]
    assert len(useless_stmts) > 0
    print(f"✓ Detected {len(useless_stmts)} useless statements")
    
    # Check for Redundant Semicolon
    semicolons = [s for s in smells if s.smell == "redundant_semicolon"]
    assert len(semicolons) >= 2
    print(f"✓ Detected {len(semicolons)} redundant semicolons")
    
    print("All nonsense detection tests passed!")

if __name__ == "__main__":
    test_nonsense_detection()
