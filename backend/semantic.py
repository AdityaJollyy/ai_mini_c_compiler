"""
semantic.py:
Mini-C Compiler Semantic Analyzer
Performs semantic analysis on the AST
- Symbol table management
- Type checking
- Undeclared/duplicate variable detection
- Printf format validation
"""

import re
from parser import (
    ASTNode, Program, Declaration, Assignment, 
    BinaryOp, Number, Identifier, Printf, IfStatement, Comparison
)


class SymbolTable:
    """Symbol table for tracking declared variables"""
    
    def __init__(self):
        self.symbols = {}  # name -> {'type': type, 'line': line, 'initialized': bool}
    
    def declare(self, name, var_type, line, initialized=False):
        """Declare a new variable"""
        if name in self.symbols:
            return False, f"Variable '{name}' already declared (first declared at line {self.symbols[name]['line']})"
        self.symbols[name] = {'type': var_type, 'line': line, 'initialized': initialized}
        return True, None
    
    def lookup(self, name):
        """Look up a variable"""
        return self.symbols.get(name)
    
    def is_declared(self, name):
        """Check if a variable is declared"""
        return name in self.symbols
    
    def mark_initialized(self, name):
        """Mark a variable as initialized"""
        if name in self.symbols:
            self.symbols[name]['initialized'] = True


class SemanticAnalyzer:
    """Performs semantic analysis on the AST"""
    
    def __init__(self):
        self.symbol_table = SymbolTable()
        self.errors = []
        self.warnings = []
    
    def analyze(self, ast):
        """
        Analyze the AST for semantic errors
        
        Args:
            ast: The AST from the parser
            
        Returns:
            list: List of semantic errors
        """
        self.symbol_table = SymbolTable()
        self.errors = []
        self.warnings = []
        
        if ast is None:
            return self.errors
        
        if isinstance(ast, Program):
            for statement in ast.statements:
                # Skip None statements (from error recovery)
                if statement is not None:
                    self._analyze_statement(statement)
        
        return self.errors
    
    def _analyze_statement(self, node):
        """Analyze a statement node"""
        if isinstance(node, Declaration):
            self._analyze_declaration(node)
        elif isinstance(node, Assignment):
            self._analyze_assignment(node)
        elif isinstance(node, Printf):
            self._analyze_printf(node)
        elif isinstance(node, IfStatement):
            self._analyze_if(node)
    
    def _analyze_declaration(self, node):
        """Analyze a variable declaration"""
        has_init = node.value is not None
        success, error_msg = self.symbol_table.declare(node.name, 'int', node.line, has_init)
        
        if not success:
            self.errors.append({
                'line': node.line,
                'type': 'Semantic',
                'message': error_msg
            })
        
        # If there's an initialization value, analyze it
        if node.value is not None:
            self._analyze_expression(node.value)
    
    def _analyze_assignment(self, node):
        """Analyze a variable assignment"""
        # Check if variable is declared
        if not self.symbol_table.is_declared(node.name):
            self.errors.append({
                'line': node.line,
                'type': 'Semantic',
                'message': f"Variable '{node.name}' is not declared. Add 'int {node.name};' before using it"
            })
        else:
            self.symbol_table.mark_initialized(node.name)
        
        # Analyze the expression being assigned
        self._analyze_expression(node.value)
    
    def _analyze_printf(self, node):
        """Analyze a printf statement with format validation"""
        if node.format_string is not None:
            # Parse format string (remove quotes)
            format_str = node.format_string[1:-1]  # Remove surrounding quotes
            
            # Count format specifiers
            # Only support %d and %i for integers
            format_specifiers = re.findall(r'%[di]', format_str)
            num_specifiers = len(format_specifiers)
            num_args = len(node.args)
            
            # Check for unsupported format specifiers
            all_specifiers = re.findall(r'%[a-zA-Z]', format_str)
            for spec in all_specifiers:
                if spec not in ['%d', '%i']:
                    self.errors.append({
                        'line': node.line,
                        'type': 'Semantic',
                        'message': f"Unsupported format specifier '{spec}' in printf. Only %d and %i are supported"
                    })
            
            # Check argument count matches format specifiers
            if num_specifiers != num_args:
                if num_specifiers > num_args:
                    self.errors.append({
                        'line': node.line,
                        'type': 'Semantic',
                        'message': f"printf format expects {num_specifiers} argument(s), but {num_args} provided. Missing arguments for format specifiers"
                    })
                else:
                    self.errors.append({
                        'line': node.line,
                        'type': 'Semantic',
                        'message': f"printf format expects {num_specifiers} argument(s), but {num_args} provided. Too many arguments"
                    })
        
        # Analyze all argument expressions
        for arg in node.args:
            self._analyze_expression(arg)
    
    def _analyze_if(self, node):
        """Analyze an if statement"""
        # Analyze the condition
        self._analyze_condition(node.condition)
        
        # Analyze the body statements
        for statement in node.body:
            self._analyze_statement(statement)
    
    def _analyze_condition(self, node):
        """Analyze a comparison condition"""
        if isinstance(node, Comparison):
            self._analyze_expression(node.left)
            self._analyze_expression(node.right)
    
    def _analyze_expression(self, node):
        """Analyze an expression"""
        if isinstance(node, Number):
            pass  # Numbers are always valid
        elif isinstance(node, Identifier):
            if not self.symbol_table.is_declared(node.name):
                self.errors.append({
                    'line': node.line,
                    'type': 'Semantic',
                    'message': f"Variable '{node.name}' is not declared. Add 'int {node.name};' before using it"
                })
        elif isinstance(node, BinaryOp):
            self._analyze_expression(node.left)
            self._analyze_expression(node.right)
            
            # Check for division by zero (if right side is literal 0)
            if node.op == '/' and isinstance(node.right, Number) and node.right.value == 0:
                self.errors.append({
                    'line': node.line,
                    'type': 'Semantic',
                    'message': "Division by zero"
                })


class Compiler:
    """Main compiler class that combines all phases"""
    
    def __init__(self):
        from parser import Parser
        self.parser = Parser()
        self.analyzer = SemanticAnalyzer()
    
    def compile(self, code):
        """
        Compile the input code through all phases
        
        Args:
            code: String containing Mini-C source code
            
        Returns:
            dict: {
                'success': bool,
                'errors': list of errors,
                'ast': AST if successful
            }
        """
        # Handle empty or whitespace-only code
        if not code or not code.strip():
            return {
                'success': True,
                'errors': [],
                'ast': None
            }
        
        # Phase 1 & 2: Lexing and Parsing
        ast, parse_errors = self.parser.parse(code)
        
        # Phase 3: Semantic Analysis (run even with parse errors to collect all errors)
        semantic_errors = []
        if ast is not None:
            semantic_errors = self.analyzer.analyze(ast)
        
        # Combine all errors and sort by line number (chronological)
        all_errors = parse_errors + semantic_errors
        all_errors.sort(key=lambda x: x['line'])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_errors = []
        for err in all_errors:
            key = (err['line'], err['type'], err['message'][:50])
            if key not in seen:
                seen.add(key)
                unique_errors.append(err)
        
        if unique_errors:
            return {
                'success': False,
                'errors': unique_errors,
                'ast': ast  # Return partial AST for potential use
            }
        
        return {
            'success': True,
            'errors': [],
            'ast': ast
        }


# For testing
if __name__ == "__main__":
    # Test with various error cases
    test_cases = [
        # Valid code with printf format
        ("""
        int x = 10;
        int y = 20;
        printf("%d", x);
        printf("%d %d", x, y);
        """, "Valid code with printf format"),
        
        # Undeclared variable
        ("""
        x = 5;
        printf("%d", x);
        """, "Undeclared variable"),
        
        # Duplicate declaration
        ("""
        int x;
        int x;
        """, "Duplicate declaration"),
        
        # Printf format mismatch - too few args
        ("""
        int x = 5;
        printf("%d %d", x);
        """, "Printf format mismatch - too few args"),
        
        # Printf format mismatch - too many args
        ("""
        int x = 5;
        int y = 10;
        printf("%d", x, y);
        """, "Printf format mismatch - too many args"),
        
        # Unsupported format specifier
        ("""
        int x = 5;
        printf("%s", x);
        """, "Unsupported format specifier"),
        
        # Division by zero
        ("""
        int x = 10;
        int y;
        y = x / 0;
        """, "Division by zero"),
    ]
    
    compiler = Compiler()
    
    for code, description in test_cases:
        print(f"\n=== {description} ===")
        print(f"Code: {code.strip()[:60]}...")
        result = compiler.compile(code)
        print(f"Success: {result['success']}")
        if result['errors']:
            print("Errors:")
            for err in result['errors']:
                print(f"  Line {err['line']}: [{err['type']}] {err['message']}")