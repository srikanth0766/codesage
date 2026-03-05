"""
Universal AST Analyzer for Multi-Language Support.

Uses language-specific parsers:
- Python: Built-in ast module
- JavaScript/TypeScript: esprima parser
- Fallback: LLM-based analysis for unsupported languages
"""

import ast
from typing import List, Dict, Optional, Any
from dataclasses import dataclass


try:
    import esprima
    ESPRIMA_AVAILABLE = True
except ImportError:
    ESPRIMA_AVAILABLE = False


@dataclass
class CodeSyntaxError:
    """Represents a syntax error found in code"""
    line: int
    column: int
    message: str
    type: str = "SyntaxError"


class UniversalASTAnalyzer:
    """
    Universal code analyzer supporting multiple programming languages.
    
    Supported Languages:
    - Python (using ast module)
    - JavaScript/TypeScript (using esprima)
    - Others: Fallback to LLM-based analysis
    """
    
    SUPPORTED_LANGUAGES = {
        'python': 'python',
        'javascript': 'javascript',
        'typescript': 'javascript',  # TypeScript syntax is similar enough
        'javascriptreact': 'javascript',
        'typescriptreact': 'javascript',
    }
    
    def __init__(self, language: str):
        """
        Initialize analyzer for specific language.
        
        Args:
            language: Language identifier (e.g., 'python', 'javascript')
        """
        self.language = language.lower()
        self.parser_type = self.SUPPORTED_LANGUAGES.get(self.language)
        
        if not self.parser_type:
            raise ValueError(f"Language {language} not supported. Supported: {list(self.SUPPORTED_LANGUAGES.keys())}")
    
    def check_syntax(self, code: str) -> Dict[str, Any]:
        """
        Check code for syntax errors.
        
        Args:
            code: Source code to check
            
        Returns:
            Dict with 'status' and 'errors' keys
        """
        if self.parser_type == 'python':
            return self._check_python_syntax(code)
        elif self.parser_type == 'javascript':
            return self._check_javascript_syntax(code)
        else:
            return {'status': 'unknown', 'errors': []}
    
    def _check_python_syntax(self, code: str) -> Dict[str, Any]:
        """Check Python syntax using ast module"""
        try:
            ast.parse(code)
            return {'status': 'valid', 'errors': []}
        except SyntaxError as e:
            return {
                'status': 'error',
                'errors': [{
                    'line': e.lineno or 0,
                    'column': e.offset or 0,
                    'message': str(e.msg),
                    'type': 'SyntaxError'
                }]
            }
    
    def _check_javascript_syntax(self, code: str) -> Dict[str, Any]:
        """Check JavaScript syntax using esprima"""
        if not ESPRIMA_AVAILABLE:
            return {'status': 'unknown', 'errors': []}
        
        try:
            esprima.parseScript(code, {'tolerant': False})
            return {'status': 'valid', 'errors': []}
        except esprima.Error as e:
            return {
                'status': 'error',
                'errors': [{
                    'line': e.lineNumber if hasattr(e, 'lineNumber') else 0,
                    'column': e.column if hasattr(e, 'column') else 0,
                    'message': str(e.description if hasattr(e, 'description') else e),
                    'type': 'SyntaxError'
                }]
            }
    
    def find_infinite_loops(self, code: str) -> List[Dict[str, Any]]:
        """
        Detect infinite loop patterns.
        
        Args:
            code: Source code to analyze
            
        Returns:
            List of detected infinite loop issues
        """
        if self.parser_type == 'python':
            return self._find_python_infinite_loops(code)
        elif self.parser_type == 'javascript':
            return self._find_javascript_infinite_loops(code)
        else:
            return []
    
    def _find_python_infinite_loops(self, code: str) -> List[Dict[str, Any]]:
        """Find infinite loops in Python code"""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []
        
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.While):
                # Check for while True without break
                if self._is_constant_true(node.test):
                    has_break = self._contains_break(node)
                    if not has_break:
                        issues.append({
                            'type': 'infinite_loop',
                            'line': node.lineno,
                            'description': 'Infinite loop: while True without break statement',
                            'severity': 'error'
                        })
        
        return issues
    
    def _find_javascript_infinite_loops(self, code: str) -> List[Dict[str, Any]]:
        """Find infinite loops in JavaScript code"""
        if not ESPRIMA_AVAILABLE:
            return []
        
        try:
            tree = esprima.parseScript(code, {'loc': True, 'tolerant': True})
        except:
            return []
        
        issues = []
        
        def traverse(node):
            """Recursively traverse AST"""
            if not isinstance(node, dict):
                return
            
            node_type = node.get('type')
            
            # Check for while(true) loops
            if node_type == 'WhileStatement':
                test = node.get('test', {})
                # Check for literal true (JavaScript uses lowercase true)
                if test.get('type') == 'Literal' and test.get('value') == True:
                    # Check if there's a break statement
                    has_break = self._js_has_break(node.get('body'))
                    if not has_break:
                        loc = node.get('loc', {}).get('start', {})
                        issues.append({
                            'type': 'infinite_loop',
                            'line': loc.get('line', 0),
                            'description': 'Infinite loop: while(true) without break statement',
                            'severity': 'error'
                        })
            
            # Check for for(;;) loops
            elif node_type == 'ForStatement':
                if (not node.get('test') or 
                    (node.get('test', {}).get('type') == 'Literal' and 
                     node.get('test', {}).get('value') == True)):
                    has_break = self._js_has_break(node.get('body'))
                    if not has_break:
                        loc = node.get('loc', {}).get('start', {})
                        issues.append({
                            'type': 'infinite_loop',
                            'line': loc.get('line', 0),
                            'description': 'Infinite loop: for(;;) without break statement',
                            'severity': 'error'
                        })
            
            # Traverse children
            for key, value in node.items():
                if isinstance(value, dict):
                    traverse(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            traverse(item)
        
        traverse(tree.toDict())  # Convert to dict before traversing
        return issues
    
    def _js_has_break(self, node) -> bool:
        """Check if JavaScript AST node contains a break statement"""
        if not isinstance(node, dict):
            return False
        
        if node.get('type') == 'BreakStatement':
            return True
        
        # Traverse children
        for key, value in node.items():
            if isinstance(value, dict):
                if self._js_has_break(value):
                    return True
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict) and self._js_has_break(item):
                        return True
        
        return False
    
    def _is_constant_true(self, node: ast.AST) -> bool:
        """Check if Python AST node is constant True"""
        return isinstance(node, ast.Constant) and node.value is True
    
    def _contains_break(self, node: ast.AST) -> bool:
        """Check if Python AST node contains a break statement"""
        for child in ast.walk(node):
            if isinstance(child, ast.Break):
                return True
        return False
    
    def find_unreachable_code(self, code: str) -> List[Dict[str, Any]]:
        """
        Detect unreachable code after return/break statements.
        
        Args:
            code: Source code to analyze
            
        Returns:
            List of unreachable code issues
        """
        if self.parser_type == 'python':
            return self._find_python_unreachable(code)
        elif self.parser_type == 'javascript':
            return self._find_javascript_unreachable(code)
        else:
            return []
    
    def _find_python_unreachable(self, code: str) -> List[Dict[str, Any]]:
        """Find unreachable code in Python"""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []
        
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.For, ast.While)):
                body = node.body
                for i, stmt in enumerate(body):
                    if isinstance(stmt, (ast.Return, ast.Break, ast.Continue)):
                        if i < len(body) - 1:
                            next_stmt = body[i + 1]
                            stmt_type = stmt.__class__.__name__.lower()
                            issues.append({
                                'type': 'unreachable_code',
                                'line': next_stmt.lineno,
                                'description': f'Unreachable code after {stmt_type} statement',
                                'severity': 'warning'
                            })
                            break
        
        return issues
    
    def _find_javascript_unreachable(self, code: str) -> List[Dict[str, Any]]:
        """Find unreachable code in JavaScript"""
        if not ESPRIMA_AVAILABLE:
            return []
        
        try:
            tree = esprima.parseScript(code, {'loc': True, 'tolerant': True})
        except:
            return []
            
        issues = []
        
        def traverse(node):
            if not isinstance(node, dict): return
            
            node_type = node.get('type')
            
            if node_type in ['FunctionDeclaration', 'FunctionExpression', 'ArrowFunctionExpression']:
                body = node.get('body')
                if isinstance(body, dict) and body.get('type') == 'BlockStatement':
                    self._check_js_block(body.get('body', []), issues)
                    
            elif node_type == 'BlockStatement':
                self._check_js_block(node.get('body', []), issues)
                
            for key, value in node.items():
                if isinstance(value, dict): traverse(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict): traverse(item)
                        
        traverse(tree.toDict())
        return issues
        
    def _check_js_block(self, body_list: Any, issues: List[Dict[str, Any]]):
        """Helper to check a JS block for unreachable code."""
        if not isinstance(body_list, list): return
        
        for i, stmt in enumerate(body_list):
            if not isinstance(stmt, dict): continue
            
            stmt_type = stmt.get('type')
            if stmt_type in ['ReturnStatement', 'BreakStatement', 'ContinueStatement']:
                if i < len(body_list) - 1:
                    next_stmt = body_list[i + 1]
                    if isinstance(next_stmt, dict):
                        loc = next_stmt.get('loc', {}).get('start', {})
                        issues.append({
                            'type': 'unreachable_code',
                            'line': loc.get('line', 0),
                            'description': f'Unreachable code after {stmt_type.replace("Statement", "").lower()} statement',
                            'severity': 'warning'
                        })
                    break
