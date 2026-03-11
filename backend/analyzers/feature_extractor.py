"""
Feature Extractor for Code Smell Detection.

Extracts structural metrics from Python AST that are used by the smell detector:
  - LOC per method
  - Cyclomatic complexity (E - N + 2P)
  - Nesting depth
  - Fan-in / Fan-out
  - Number of parameters
  - WMC (Weighted Methods per Class)
  - CBO (Coupling Between Objects)

These metrics map directly to the CodeSage blueprint specification.
"""

import ast
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class MethodFeatures:
    """Features extracted for a single method/function."""
    name: str
    start_line: int
    end_line: int
    loc: int                        # Lines of code (non-blank)
    params: int                     # Number of parameters
    complexity: int                 # Cyclomatic complexity
    max_nesting_depth: int          # Maximum nesting depth
    calls_made: List[str] = field(default_factory=list)   # Methods/functions called
    external_calls: int = 0         # Calls to other classes/modules
    local_calls: int = 0            # Calls within same class


@dataclass
class ClassFeatures:
    """Features extracted for a single class."""
    name: str
    start_line: int
    end_line: int
    methods: List[MethodFeatures] = field(default_factory=list)
    wmc: int = 0                    # Weighted Methods per Class (sum of complexities)
    cbo: int = 0                    # Coupling Between Objects (distinct types referenced)
    loc: int = 0                    # Total class LOC
    num_methods: int = 0


@dataclass
class FileFeatures:
    """Features extracted from the whole file."""
    classes: List[ClassFeatures] = field(default_factory=list)
    standalone_functions: List[MethodFeatures] = field(default_factory=list)
    top_level_statements: List[Dict[str, Any]] = field(default_factory=list)
    total_loc: int = 0
    total_methods: int = 0
    imports: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a JSON-serializable dictionary."""
        return {
            "total_loc": self.total_loc,
            "total_methods": self.total_methods,
            "imports": self.imports,
            "classes": [
                {
                    "name": c.name,
                    "start_line": c.start_line,
                    "end_line": c.end_line,
                    "wmc": c.wmc,
                    "cbo": c.cbo,
                    "loc": c.loc,
                    "num_methods": c.num_methods,
                    "methods": [_method_to_dict(m) for m in c.methods],
                }
                for c in self.classes
            ],
            "standalone_functions": [_method_to_dict(f) for f in self.standalone_functions],
            "top_level_statements": self.top_level_statements,
        }


def _method_to_dict(m: MethodFeatures) -> Dict[str, Any]:
    return {
        "name": m.name,
        "start_line": m.start_line,
        "end_line": m.end_line,
        "loc": m.loc,
        "params": m.params,
        "complexity": m.complexity,
        "max_nesting_depth": m.max_nesting_depth,
        "external_calls": m.external_calls,
        "local_calls": m.local_calls,
    }


class FeatureExtractor:
    """
    Extracts code metrics from Python source using the built-in ast module.

    Usage:
        extractor = FeatureExtractor()
        features = extractor.extract(source_code)
    """

    def extract(self, code: str) -> Optional[FileFeatures]:
        """
        Parse code and extract all features.

        Args:
            code: Python source code string

        Returns:
            FileFeatures or None if parsing fails
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return None

        lines = code.splitlines()
        file_features = FileFeatures()

        # Collect all imported module names for CBO
        imported_names = self._collect_imports(tree, file_features)

        # Walk top-level nodes
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                class_feat = self._extract_class(node, lines, imported_names)
                file_features.classes.append(class_feat)
                file_features.total_methods += class_feat.num_methods
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                fn_feat = self._extract_function(node, lines, imported_names, class_methods=set())
                file_features.standalone_functions.append(fn_feat)
                file_features.total_methods += 1
            elif isinstance(node, (ast.Expr, ast.Assign, ast.Call)):
                # Capture top-level expressions for semantic/nonsense checking
                file_features.top_level_statements.append({
                    "type": type(node).__name__,
                    "line": node.lineno,
                    "col": node.col_offset,
                    "ast_node": node
                })

        file_features.total_loc = sum(1 for l in lines if l.strip())
        return file_features

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _collect_imports(self, tree: ast.AST, file_features: FileFeatures) -> set:
        """Collect all imported names to help identify external calls."""
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name
                    imported.add(name.split(".")[0])
                    file_features.imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported.add(node.module.split(".")[0])
                    file_features.imports.append(node.module)
                for alias in node.names:
                    imported.add(alias.asname or alias.name)
        return imported

    def _extract_class(self, node: ast.ClassDef, lines: List[str], ext_names: set) -> ClassFeatures:
        """Extract features from a class definition."""
        class_feat = ClassFeatures(
            name=node.name,
            start_line=node.lineno,
            end_line=node.end_lineno or node.lineno,
        )

        # Collect method names for local-call detection
        method_names = {
            n.name for n in ast.iter_child_nodes(node)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        }

        # Referenced external types for CBO
        external_types: set = set()

        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                fn_feat = self._extract_function(child, lines, ext_names, method_names)
                class_feat.methods.append(fn_feat)
                class_feat.wmc += fn_feat.complexity

                # CBO: collect attribute references to external names
                for n in ast.walk(child):
                    if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name):
                        if n.value.id in ext_names and n.value.id != "self":
                            external_types.add(n.value.id)

        class_feat.cbo = len(external_types)
        class_feat.num_methods = len(class_feat.methods)
        class_feat.loc = sum(
            1 for i in range(class_feat.start_line - 1, class_feat.end_line)
            if i < len(lines) and lines[i].strip()
        )
        return class_feat

    def _extract_function(
        self,
        node: Any,  # ast.FunctionDef or ast.AsyncFunctionDef
        lines: List[str],
        ext_names: set,
        class_methods: set
    ) -> MethodFeatures:
        """Extract features from a function/method definition."""
        start = node.lineno
        end = node.end_lineno or node.lineno

        loc = sum(
            1 for i in range(start - 1, end)
            if i < len(lines) and lines[i].strip()
        )

        # Parameters (exclude 'self' and 'cls')
        params = [
            a for a in node.args.args
            if a.arg not in ("self", "cls")
        ]

        complexity = self._cyclomatic_complexity(node)
        nesting = self._max_nesting(node)
        local_calls, external_calls, all_calls = self._count_calls(node, class_methods, ext_names)

        return MethodFeatures(
            name=node.name,
            start_line=start,
            end_line=end,
            loc=loc,
            params=len(params),
            complexity=complexity,
            max_nesting_depth=nesting,
            calls_made=all_calls,
            local_calls=local_calls,
            external_calls=external_calls,
        )

    def _cyclomatic_complexity(self, node: ast.AST) -> int:
        """
        Approximate cyclomatic complexity M = decision points + 1.

        Counts: if, elif, for, while, except, with, assert, and/or operators.
        """
        complexity = 1  # Base path
        for n in ast.walk(node):
            if isinstance(n, (ast.If, ast.For, ast.While, ast.ExceptHandler,
                               ast.With, ast.Assert, ast.comprehension)):
                complexity += 1
            elif isinstance(n, ast.BoolOp):
                # 'and' / 'or' each add a branch
                complexity += len(n.values) - 1
        return complexity

    def _max_nesting(self, node: ast.AST, current: int = 0) -> int:
        """Recursively compute maximum nesting depth of control structures."""
        max_depth = current
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.With,
                                   ast.Try, ast.ExceptHandler)):
                depth = self._max_nesting(child, current + 1)
                max_depth = max(max_depth, depth)
            else:
                depth = self._max_nesting(child, current)
                max_depth = max(max_depth, depth)
        return max_depth

    def _count_calls(
        self,
        node: ast.FunctionDef,
        class_methods: set,
        ext_names: set
    ):
        """Count local and external calls within a function body."""
        local = 0
        external = 0
        all_calls: List[str] = []

        for n in ast.walk(node):
            if isinstance(n, ast.Call):
                func = n.func
                if isinstance(func, ast.Name):
                    name = func.id
                    all_calls.append(name)
                    if name in class_methods:
                        local += 1
                    elif name in ext_names:
                        external += 1
                elif isinstance(func, ast.Attribute):
                    full = f"{getattr(func.value, 'id', '?')}.{func.attr}"
                    all_calls.append(full)
                    if isinstance(func.value, ast.Name) and func.value.id != "self":
                        external += 1
                    else:
                        local += 1

        return local, external, all_calls
