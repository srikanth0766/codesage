"""
Control Flow Analyzer for Visual Program Error Explanation.

This module analyzes Python code for control flow issues and generates
visual representations using Mermaid.js flowcharts.

Detects:
- Infinite loops (while True without break)
- Loop variables not being updated
- Unreachable code after return/break
"""

import ast
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass, asdict


@dataclass
class CFGNode:
    """Control Flow Graph Node"""
    id: str
    type: str  # 'entry', 'condition', 'block', 'exit', 'unreachable'
    label: str
    line: int
    is_problematic: bool = False
    problem_description: Optional[str] = None


@dataclass
class CFGEdge:
    """Control Flow Graph Edge"""
    from_node: str
    to_node: str
    label: Optional[str] = None  # 'true', 'false', etc.


@dataclass
class ControlFlowIssue:
    """Detected control flow issue"""
    type: str  # 'infinite_loop', 'unreachable_code', 'variable_not_updated'
    line: int
    description: str
    severity: str  # 'error', 'warning'


@dataclass
class ControlFlowResult:
    """Result of control flow analysis"""
    has_issues: bool
    issues: List[ControlFlowIssue]
    graph_nodes: List[CFGNode]
    graph_edges: List[CFGEdge]
    mermaid_code: str  # Ready-to-render Mermaid diagram
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        # Handle issues that might already be dicts (from universal analyzer)
        issues_list = []
        for issue in self.issues:
            if isinstance(issue, dict):
                issues_list.append(issue)
            else:
                issues_list.append(asdict(issue))
        
        return {
            'has_issues': self.has_issues,
            'issues': issues_list,
            'graph_nodes': [asdict(node) for node in self.graph_nodes],
            'graph_edges': [asdict(edge) for edge in self.graph_edges],
            'mermaid_code': self.mermaid_code
        }


class ControlFlowAnalyzer:
    """Analyzes code for control flow issues across multiple languages"""
    
    def analyze(self, code: str, language: str = "python") -> ControlFlowResult:
        """
        Main analysis entry point.
        Returns control flow issues and graph visualization data.
        """
        # Import here to avoid circular dependency
        from analyzers.universal_ast_analyzer import UniversalASTAnalyzer
        
        tree = None
        issues = []
        
        try:
            tree, issues = self._analyze_supported_language(code, language, UniversalASTAnalyzer)
        except ValueError:
            tree, issues = self._analyze_fallback(code)
            
        nodes, edges = self._build_graph_for_first_issue(tree, issues, code)
        # Convert to Mermaid syntax
        generator = MermaidGenerator()
        mermaid_code = generator.generate(nodes, edges)
        
        return ControlFlowResult(
            has_issues=len(issues) > 0,
            issues=issues,
            graph_nodes=nodes,
            graph_edges=edges,
            mermaid_code=mermaid_code
        )
        
    def _analyze_supported_language(self, code: str, language: str, UniversalASTAnalyzer) -> Tuple[Optional[ast.AST], List[ControlFlowIssue]]:
        analyzer = UniversalASTAnalyzer(language)
        raw_issues = analyzer.find_infinite_loops(code) + analyzer.find_unreachable_code(code)
        
        issues = []
        for issue in raw_issues:
            if isinstance(issue, dict):
                issues.append(ControlFlowIssue(
                    type=issue.get('type', 'unknown'),
                    line=issue.get('line', 0),
                    description=issue.get('description', ''),
                    severity=issue.get('severity', 'warning')
                ))
            else:
                issues.append(issue)
                
        tree = None
        if language.lower() == 'python':
            try:
                tree = ast.parse(code)
                for py_issue in self._detect_infinite_loops(tree):
                    if py_issue.type != 'infinite_loop':
                        issues.append(py_issue)
            except SyntaxError:
                pass
                
        return tree, issues
        
    def _analyze_fallback(self, code: str) -> Tuple[Optional[ast.AST], List[ControlFlowIssue]]:
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return None, []
            
        issues = self._detect_infinite_loops(tree) + self._detect_unreachable_code(tree)
        return tree, issues
        
    def _build_graph_for_first_issue(self, tree: Optional[ast.AST], issues: List[ControlFlowIssue], code: str) -> Tuple[List[CFGNode], List[CFGEdge]]:
        if not issues:
            return [], []
        return self._generate_graph_for_issue(tree, issues[0], code)
    
    def _detect_infinite_loops(self, tree: ast.AST) -> List[ControlFlowIssue]:
        """Detect infinite loop patterns"""
        issues = []
        
        for node in ast.walk(tree):
            # Pattern 1: while True without break
            if isinstance(node, ast.While):
                if self._is_constant_true(node.test):
                    has_break = self._contains_break(node)
                    if not has_break:
                        issues.append(ControlFlowIssue(
                            type='infinite_loop',
                            line=node.lineno,
                            description='Infinite loop: while True without break statement',
                            severity='error'
                        ))
                else:
                    # Pattern 2: Loop condition variable never modified
                    condition_vars = self._get_condition_variables(node.test)
                    modified_vars = self._get_modified_variables(node.body)
                    
                    if condition_vars and not condition_vars.intersection(modified_vars):
                        vars_str = ', '.join(sorted(condition_vars))
                        issues.append(ControlFlowIssue(
                            type='variable_not_updated',
                            line=node.lineno,
                            description=f'Loop condition variable(s) "{vars_str}" never modified in loop body',
                            severity='warning'
                        ))
            
            # Pattern 3: For loop with variable not updated (less common)
            if isinstance(node, ast.For):
                target_name = self._get_target_name(node.target)
                if target_name and self._is_target_overwritten_with_constant(node.body, target_name):
                    issues.append(ControlFlowIssue(
                        type='variable_not_updated',
                        line=node.lineno,
                        description=f'Loop variable "{target_name}" overwritten with constant in loop body',
                        severity='warning'
                    ))
        
        return issues
    
    def _detect_unreachable_code(self, tree: ast.AST) -> List[ControlFlowIssue]:
        """Detect unreachable code after return/break/continue"""
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.For, ast.While)):
                body = node.body
                for i, stmt in enumerate(body):
                    # Check if statement is return/break/continue
                    if isinstance(stmt, (ast.Return, ast.Break, ast.Continue)):
                        # Check if there are statements after this
                        if i < len(body) - 1:
                            next_stmt = body[i + 1]
                            stmt_type = stmt.__class__.__name__.lower()
                            issues.append(ControlFlowIssue(
                                type='unreachable_code',
                                line=next_stmt.lineno,
                                description=f'Unreachable code after {stmt_type} statement',
                                severity='warning'
                            ))
                            break  # Only report first unreachable code
        
        return issues
    
    def _generate_graph_for_issue(
        self, 
        tree: ast.AST, 
        issue,  # Can be dict or ControlFlowIssue
        code: str
    ) -> Tuple[List[CFGNode], List[CFGEdge]]:
        """Generate control flow graph for a specific issue"""
        nodes = []
        edges = []
        
        # Determine strict issue type and convert if necessary
        if isinstance(issue, dict):
            issue = ControlFlowIssue(
                type=issue.get('type', 'unknown'),
                line=issue.get('line', 0),
                description=issue.get('description', ''),
                severity=issue.get('severity', 'warning')
            )
        
        # If no AST tree is available (non-Python languages), generate generic graph
        if tree is None:
            return self._generate_generic_graph(issue)
            
        # Find the problematic node in AST
        problem_node = self._find_node_at_line(tree, issue.line)
        
        if problem_node is None:
             # Fallback if node not found
             return self._generate_generic_graph(issue)
        
        if isinstance(problem_node, ast.While):
            nodes, edges = self._generate_while_loop_graph(problem_node, issue)
        elif isinstance(problem_node, ast.For):
            nodes, edges = self._generate_for_loop_graph(problem_node, issue)
        else:
            # Generic graph for unreachable code
            nodes, edges = self._generate_unreachable_code_graph(tree, issue, code)
        
        return nodes, edges

    def _generate_generic_graph(self, issue: ControlFlowIssue) -> Tuple[List[CFGNode], List[CFGEdge]]:
        """Generate generic graph when AST is not available"""
        nodes = []
        edges = []
        
        if issue.type == 'infinite_loop':
             nodes = [
                 CFGNode('start', 'entry', 'Start', issue.line),
                 CFGNode('condition', 'condition', 'Loop Condition', issue.line, is_problematic=True, problem_description=issue.description),
                 CFGNode('body', 'block', 'Loop Body', issue.line + 1),
             ]
             edges = [
                 CFGEdge('start', 'condition'),
                 CFGEdge('condition', 'body', 'true'),
                 CFGEdge('body', 'condition', 'repeat'),
             ]
        elif issue.type == 'unreachable_code':
             nodes = [
                 CFGNode('start', 'entry', 'Start', max(1, issue.line - 2)),
                 CFGNode('statement', 'block', 'Return/Break Statement', max(1, issue.line - 1)),
                 CFGNode('unreachable', 'unreachable', 'Unreachable Code', issue.line, is_problematic=True, problem_description=issue.description)
             ]
             edges = [
                 CFGEdge('start', 'statement'),
                 CFGEdge('statement', 'unreachable', 'never reached')
             ]
             
        return nodes, edges
    
    def _generate_while_loop_graph(
        self, 
        node: ast.While, 
        issue: ControlFlowIssue
    ) -> Tuple[List[CFGNode], List[CFGEdge]]:
        """Generate graph for while loop"""
        condition_text = ast.unparse(node.test)
        
        nodes = [
            CFGNode('start', 'entry', 'Start', node.lineno),
            CFGNode(
                'condition', 
                'condition', 
                condition_text, 
                node.lineno,
                is_problematic=True,
                problem_description=issue.description
            ),
            CFGNode('body', 'block', 'Loop Body', node.lineno + 1),
        ]
        
        edges = [
            CFGEdge('start', 'condition'),
            CFGEdge('condition', 'body', 'true'),
            CFGEdge('body', 'condition', 'repeat'),
        ]
        
        # Check if there's a break
        if self._contains_break(node):
            nodes.append(CFGNode('exit', 'exit', 'Exit', node.end_lineno or node.lineno))
            edges.append(CFGEdge('body', 'exit', 'break'))
            edges.append(CFGEdge('condition', 'exit', 'false'))
        else:
            # No exit - infinite loop!
            nodes.append(CFGNode(
                'exit', 
                'unreachable', 
                'Exit (unreachable)', 
                node.end_lineno or node.lineno,
                is_problematic=True,
                problem_description='This exit is never reached'
            ))
            edges.append(CFGEdge('condition', 'exit', 'false (never taken)'))
        
        return nodes, edges
    
    def _generate_for_loop_graph(
        self, 
        node: ast.For, 
        issue: ControlFlowIssue
    ) -> Tuple[List[CFGNode], List[CFGEdge]]:
        """Generate graph for for loop"""
        target_name = self._get_target_name(node.target)
        iter_text = ast.unparse(node.iter)
        
        nodes = [
            CFGNode('start', 'entry', 'Start', node.lineno),
            CFGNode('init', 'block', f'{target_name} = ...', node.lineno),
            CFGNode(
                'condition', 
                'condition', 
                f'More items in {iter_text}?', 
                node.lineno,
                is_problematic=issue.type == 'variable_not_updated',
                problem_description=issue.description if issue.type == 'variable_not_updated' else None
            ),
            CFGNode('body', 'block', 'Loop Body', node.lineno + 1),
            CFGNode('exit', 'exit', 'Exit', node.end_lineno or node.lineno),
        ]
        
        edges = [
            CFGEdge('start', 'init'),
            CFGEdge('init', 'condition'),
            CFGEdge('condition', 'body', 'true'),
            CFGEdge('body', 'condition', 'next item'),
            CFGEdge('condition', 'exit', 'false'),
        ]
        
        return nodes, edges
    
    def _generate_unreachable_code_graph(
        self, 
        tree: ast.AST, 
        issue: ControlFlowIssue,
        code: str
    ) -> Tuple[List[CFGNode], List[CFGEdge]]:
        """Generate graph showing unreachable code"""
        # Find the return/break statement before unreachable code
        lines = code.split('\n')
        unreachable_line = issue.line
        
        nodes = [
            CFGNode('start', 'entry', 'Start', 1),
            CFGNode('code', 'block', 'Code before return/break', max(1, unreachable_line - 1)),
            CFGNode('terminator', 'block', 'return/break statement', max(1, unreachable_line - 1)),
            CFGNode(
                'unreachable', 
                'unreachable', 
                f'Line {unreachable_line} (unreachable)', 
                unreachable_line,
                is_problematic=True,
                problem_description=issue.description
            ),
        ]
        
        edges = [
            CFGEdge('start', 'code'),
            CFGEdge('code', 'terminator'),
            # No edge to unreachable - that's the point!
        ]
        
        return nodes, edges
    
class MermaidGenerator:
    """Helper class to generate Mermaid syntax from CFG nodes and edges."""
    
    def generate(self, nodes: List[CFGNode], edges: List[CFGEdge]) -> str:
        """Convert nodes and edges to Mermaid flowchart syntax"""
        if not nodes:
            return ""
        
        lines = ["flowchart TD"]
        
        # Add nodes
        for node in nodes:
            shape_start, shape_end = self._get_mermaid_shape(node.type)
            style_class = ""
            
            if node.is_problematic:
                style_class = ":::problem"
            
            # Escape quotes in label
            label = node.label.replace('"', "'")
            lines.append(f"    {node.id}{shape_start}\"{label}\"{shape_end}{style_class}")
        
        # Add edges
        for edge in edges:
            label = f"|{edge.label}|" if edge.label else ""
            lines.append(f"    {edge.from_node} --{label}--> {edge.to_node}")
        
        # Add styling
        lines.append("")
        lines.append("    classDef problem fill:#ff6b6b,stroke:#c92a2a,stroke-width:3px,color:#fff")
        
        return "\n".join(lines)
    
    def _get_mermaid_shape(self, node_type: str) -> Tuple[str, str]:
        """Get Mermaid shape syntax for node type"""
        shapes = {
            'entry': ('[', ']'),        # Rectangle
            'exit': ('[', ']'),         # Rectangle
            'condition': ('{', '}'),    # Diamond
            'block': ('[', ']'),        # Rectangle
            'unreachable': ('[[', ']]'), # Subroutine shape
        }
        return shapes.get(node_type, ('[', ']'))
    
    # Helper methods
    def _is_constant_true(self, node: ast.AST) -> bool:
        """Check if node is constant True"""
        return isinstance(node, ast.Constant) and node.value is True
    
    def _contains_break(self, node: ast.AST) -> bool:
        """Check if node contains a break statement"""
        for child in ast.walk(node):
            if isinstance(child, ast.Break):
                return True
        return False
    
    def _get_condition_variables(self, node: ast.AST) -> Set[str]:
        """Extract variable names from condition"""
        vars = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                vars.add(child.id)
        return vars
    
    def _get_modified_variables(self, body: List[ast.AST]) -> Set[str]:
        """Get variables that are assigned in body"""
        vars = set()
        for stmt in body:
            for node in ast.walk(stmt):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            vars.add(target.id)
                elif isinstance(node, ast.AugAssign):
                    if isinstance(node.target, ast.Name):
                        vars.add(node.target.id)
        return vars
    
    def _get_target_name(self, target: ast.AST) -> Optional[str]:
        """Get variable name from for loop target"""
        if isinstance(target, ast.Name):
            return target.id
        return None
    
    def _is_target_overwritten_with_constant(self, body: List[ast.AST], target_name: str) -> bool:
        """Check if target is overwritten with constant in body"""
        for stmt in body:
            if isinstance(stmt, ast.Assign):
                for t in stmt.targets:
                    if isinstance(t, ast.Name) and t.id == target_name:
                        if isinstance(stmt.value, ast.Constant):
                            return True
        return False
    
    def _find_node_at_line(self, tree: ast.AST, line: int) -> Optional[ast.AST]:
        """Find AST node at specific line number"""
        for node in ast.walk(tree):
            if hasattr(node, 'lineno') and node.lineno == line:
                return node
        return None
