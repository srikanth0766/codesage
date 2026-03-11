from analyzers.smell_detector import SmellDetector

code = """
class GodClass:
    def m1(self): pass
    def m2(self): pass
    def m3(self): pass
    def m4(self): pass
    def m5(self): pass
    def m6(self): pass
    def m7(self): pass
    def m8(self): pass
    def m9(self): pass
    def m10(self): pass
    def m11(self): pass
    def m12(self): pass
"""

detector = SmellDetector()
smells = detector.detect_to_dict(code)
print("SMELLS:", smells)
