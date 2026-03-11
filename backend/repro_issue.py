from analyzers.smell_detector import SmellDetector

code = """def vishnu():
    print("modgud")
vishnu();
hehehehehheee;
"""

detector = SmellDetector()
smells = detector.detect(code)
print(f"Smells found: {len(smells)}")
for s in smells:
    print(s)
