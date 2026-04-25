"""
executor.py:
Mini-C Compiler Executor
AST-based interpreter that executes compiled Mini-C programs
"""

import re
from parser import (
    Program, Declaration, Assignment,
    BinaryOp, Number, Identifier, Printf, IfStatement, Comparison
)


class ExecutionError(Exception):
    """Exception raised during program execution"""
    def __init__(self, message, line=0):
        self.message = message
        self.line = line
        super().__init__(self.message)


class Executor:
    """AST-based interpreter for Mini-C programs"""
    
    def __init__(self):
        self.symbol_table = {}  # Runtime symbol table: {name: value}
        self.output = []  # Collected output from printf statements
    
    def execute(self, ast):
        """
        Execute the AST and return the program output
        
        Args:
            ast: The AST from the parser (Program node)
            
        Returns:
            dict: {
                'success': bool,
                'output': str (joined output lines),
                'error': str (if execution failed)
            }
        """
        self.symbol_table = {}
        self.output = []
        
        try:
            if ast is None:
                return {
                    'success': True,
                    'output': ''
                }
            
            if isinstance(ast, Program):
                for statement in ast.statements:
                    self._execute_statement(statement)
            
            return {
                'success': True,
                'output': '\n'.join(self.output)
            }
            
        except ExecutionError as e:
            return {
                'success': False,
                'output': '\n'.join(self.output),
                'error': f"Runtime Error (line {e.line}): {e.message}"
            }
        except Exception as e:
            return {
                'success': False,
                'output': '\n'.join(self.output),
                'error': f"Runtime Error: {str(e)}"
            }
    
    def _execute_statement(self, node):
        """Execute a single statement"""
        if isinstance(node, Declaration):
            self._execute_declaration(node)
        elif isinstance(node, Assignment):
            self._execute_assignment(node)
        elif isinstance(node, Printf):
            self._execute_printf(node)
        elif isinstance(node, IfStatement):
            self._execute_if(node)
    
    def _execute_declaration(self, node):
        """
        Execute variable declaration
        int x;      -> store x = 0 (default)
        int x = 5;  -> store x = 5
        """
        if node.value is not None:
            value = self._evaluate_expression(node.value)
        else:
            value = 0  # Default value for uninitialized variables
        
        self.symbol_table[node.name] = value
    
    def _execute_assignment(self, node):
        """
        Execute variable assignment
        x = x + 2;  -> evaluate RHS and update x
        """
        value = self._evaluate_expression(node.value)
        self.symbol_table[node.name] = value
    
    def _execute_printf(self, node):
        """
        Execute printf statement
        printf("%d", x);       -> output value of x
        printf("%d %d", x, y); -> output "x_value y_value"
        """
        if node.format_string is not None:
            # Parse format string and substitute values
            format_str = node.format_string[1:-1]  # Remove quotes
            
            # Find all format specifiers
            result = format_str
            arg_index = 0
            
            # Replace %d and %i with actual values
            def replace_specifier(match):
                nonlocal arg_index
                if arg_index < len(node.args):
                    value = self._evaluate_expression(node.args[arg_index])
                    arg_index += 1
                    return str(value)
                return match.group(0)
            
            result = re.sub(r'%[di]', replace_specifier, result)
            self.output.append(result)
        else:
            # Legacy format: printf(expr) - just print the expression value
            if node.args:
                value = self._evaluate_expression(node.args[0])
                self.output.append(str(value))
    
    def _execute_if(self, node):
        """
        Execute if statement
        if (x > 5) { ... } -> evaluate condition, execute body if true
        """
        condition_result = self._evaluate_condition(node.condition)
        
        if condition_result:
            for statement in node.body:
                self._execute_statement(statement)
    
    def _evaluate_condition(self, node):
        """
        Evaluate a comparison condition
        Returns: bool
        """
        if isinstance(node, Comparison):
            left = self._evaluate_expression(node.left)
            right = self._evaluate_expression(node.right)
            
            op = node.op
            if op == '<':
                return left < right
            elif op == '>':
                return left > right
            elif op == '<=':
                return left <= right
            elif op == '>=':
                return left >= right
            elif op == '==':
                return left == right
            elif op == '!=':
                return left != right
            else:
                raise ExecutionError(f"Unknown comparison operator: {op}", node.line)
        
        # If it's just an expression, treat non-zero as true
        return self._evaluate_expression(node) != 0
    
    def _evaluate_expression(self, node):
        """
        Recursively evaluate an expression
        Returns: int value
        """
        if isinstance(node, Number):
            return node.value
        
        elif isinstance(node, Identifier):
            name = node.name
            if name not in self.symbol_table:
                raise ExecutionError(f"Variable '{name}' not found", node.line)
            return self.symbol_table[name]
        
        elif isinstance(node, BinaryOp):
            left = self._evaluate_expression(node.left)
            right = self._evaluate_expression(node.right)
            
            op = node.op
            if op == '+':
                return left + right
            elif op == '-':
                return left - right
            elif op == '*':
                return left * right
            elif op == '/':
                if right == 0:
                    raise ExecutionError("Division by zero", node.line)
                return left // right  # Integer division
            else:
                raise ExecutionError(f"Unknown operator: {op}", node.line)
        
        else:
            raise ExecutionError(f"Unknown expression type: {type(node)}", 0)


# For testing
if __name__ == "__main__":
    from parser import Parser
    from semantic import SemanticAnalyzer
    
    test_cases = [
        # Basic arithmetic and printf
        ("""
int x = 5;
int y = 10;
int z;
z = x + y;
printf("%d", z);
""", "Basic arithmetic"),
        
        # Multiple printf
        ("""
int a = 3;
int b = 7;
printf("%d", a);
printf("%d", b);
printf("%d", a + b);
""", "Multiple printf"),
        
        # Printf with multiple arguments
        ("""
int x = 100;
int y = 200;
printf("%d %d", x, y);
printf("Sum: %d", x + y);
""", "Printf with format string"),
        
        # If statement - condition true
        ("""
int x = 15;
if (x > 10) {
    printf("%d", x);
}
""", "If statement (true)"),
        
        # If statement - condition false
        ("""
int x = 5;
if (x > 10) {
    printf("%d", x);
}
printf("%d", 0);
""", "If statement (false)"),
        
        # Complex expression
        ("""
int a = 10;
int b = 3;
int c;
c = a * b + 5 - 2;
printf("%d", c);
""", "Complex expression"),
        
        # Nested if with comparisons
        ("""
int x = 5;
int y = 5;
if (x == y) {
    printf("%d", 1);
}
if (x != y) {
    printf("%d", 0);
}
""", "Equality comparisons"),
    ]
    
    parser = Parser()
    analyzer = SemanticAnalyzer()
    executor = Executor()
    
    for code, description in test_cases:
        print(f"\n=== {description} ===")
        print(f"Code: {code.strip()}")
        
        # Parse
        ast, parse_errors = parser.parse(code)
        if parse_errors:
            print(f"Parse errors: {parse_errors}")
            continue
        
        # Semantic analysis
        semantic_errors = analyzer.analyze(ast)
        if semantic_errors:
            print(f"Semantic errors: {semantic_errors}")
            continue
        
        # Execute
        result = executor.execute(ast)
        print(f"Success: {result['success']}")
        print(f"Output:\n{result['output']}")
        if 'error' in result:
            print(f"Error: {result['error']}")