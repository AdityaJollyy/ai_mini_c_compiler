"""
parser.py:
Mini-C Compiler Parser
Parses Mini-C tokens into an AST using a simple recursive-descent parser.
"""

from lexer import Lexer


class ASTNode:
    """Base class for AST nodes."""
    pass


class Program(ASTNode):
    """Root node containing list of statements."""

    def __init__(self, statements):
        self.statements = statements if statements else []

    def __repr__(self):
        return f"Program({self.statements})"


class Declaration(ASTNode):
    """Variable declaration: int x; or int x = 5;"""

    def __init__(self, name, value=None, line=0):
        self.name = name
        self.value = value
        self.line = line

    def __repr__(self):
        return f"Declaration({self.name}, {self.value})"


class Assignment(ASTNode):
    """Assignment: x = expr;"""

    def __init__(self, name, value, line=0):
        self.name = name
        self.value = value
        self.line = line

    def __repr__(self):
        return f"Assignment({self.name}, {self.value})"


class BinaryOp(ASTNode):
    """Binary operation: expr op expr."""

    def __init__(self, op, left, right, line=0):
        self.op = op
        self.left = left
        self.right = right
        self.line = line

    def __repr__(self):
        return f"BinaryOp({self.op}, {self.left}, {self.right})"


class Number(ASTNode):
    """Number literal."""

    def __init__(self, value, line=0):
        self.value = value
        self.line = line

    def __repr__(self):
        return f"Number({self.value})"


class Identifier(ASTNode):
    """Variable reference."""

    def __init__(self, name, line=0):
        self.name = name
        self.line = line

    def __repr__(self):
        return f"Identifier({self.name})"


class Printf(ASTNode):
    """Printf statement: printf("%d", x); or printf("%d %d", x, y);"""

    def __init__(self, format_string, args, line=0):
        self.format_string = format_string
        self.args = args
        self.line = line

    def __repr__(self):
        return f"Printf({self.format_string}, {self.args})"


class IfStatement(ASTNode):
    """If statement: if (condition) { statements }."""

    def __init__(self, condition, body, line=0):
        self.condition = condition
        self.body = body
        self.line = line

    def __repr__(self):
        return f"If({self.condition}, {self.body})"


class Comparison(ASTNode):
    """Comparison: expr comp_op expr."""

    def __init__(self, op, left, right, line=0):
        self.op = op
        self.left = left
        self.right = right
        self.line = line

    def __repr__(self):
        return f"Comparison({self.op}, {self.left}, {self.right})"


class ParseError(Exception):
    """Internal parse exception for control flow."""

    def __init__(self, line, message):
        self.line = line
        self.message = message
        super().__init__(message)


class _SimpleTokenStream:
    """Tiny helper around token list for recursive-descent parsing."""

    def __init__(self, tokens):
        self.tokens = tokens
        self.index = 0

    def current(self):
        return self.tokens[self.index]

    def previous(self):
        if self.index == 0:
            return self.tokens[0]
        return self.tokens[self.index - 1]

    def at_end(self):
        return self.current()["type"] == "EOF"

    def advance(self):
        if not self.at_end():
            self.index += 1
        return self.previous()

    def check(self, token_type):
        if self.at_end():
            return token_type == "EOF"
        return self.current()["type"] == token_type

    def match(self, *token_types):
        for token_type in token_types:
            if self.check(token_type):
                return self.advance()
        return None


class Parser:
    """Simple recursive-descent parser with lightweight error recovery."""

    COMPARISON_OPS = {"LT": "<", "GT": ">", "LE": "<=", "GE": ">=", "EQ": "==", "NE": "!="}

    def __init__(self):
        self.lexer = Lexer()
        self.errors = []
        self.stream = None

    def parse(self, code):
        """
        Parse code and return (ast, errors).
        """
        lex_tokens, lex_errors = self.lexer.tokenize(code)
        self.errors = []

        eof_line = len(code.split("\n")) if code else 1
        if lex_tokens:
            eof_line = lex_tokens[-1]["line"]

        tokens = list(lex_tokens)
        tokens.append({"type": "EOF", "value": None, "line": eof_line})
        self.stream = _SimpleTokenStream(tokens)

        statements = []
        while not self.stream.at_end():
            try:
                stmt = self._parse_statement()
                if stmt is not None:
                    statements.append(stmt)
            except ParseError as exc:
                self._add_error(exc.line, "Syntax", exc.message)
                self._synchronize()

        ast = Program(statements)

        all_errors = list(lex_errors) + self.errors
        all_errors.sort(key=lambda x: x["line"])

        unique_errors = []
        seen = set()
        for err in all_errors:
            key = (err["line"], err["type"], err["message"])
            if key not in seen:
                seen.add(key)
                unique_errors.append(err)

        return ast, unique_errors

    def _add_error(self, line, error_type, message):
        self.errors.append({"line": line, "type": error_type, "message": message})

    def _line(self):
        return self.stream.current()["line"]

    def _expect(self, token_type, message):
        token = self.stream.match(token_type)
        if token is None:
            raise ParseError(self._line(), message)
        return token

    def _synchronize(self):
        while not self.stream.at_end():
            if self.stream.previous()["type"] == "SEMI":
                return
            if self.stream.current()["type"] in {"INT", "ID", "PRINTF", "IF", "RBRACE"}:
                return
            self.stream.advance()

    def _parse_statement(self):
        curr_type = self.stream.current()["type"]

        if curr_type == "INT":
            return self._parse_declaration()
        if curr_type == "ID":
            return self._parse_assignment()
        if curr_type == "PRINTF":
            return self._parse_printf()
        if curr_type == "IF":
            return self._parse_if()

        raise ParseError(self._line(), f"Unexpected token '{self.stream.current()['value']}'")

    def _parse_declaration(self):
        line = self._expect("INT", "Expected 'int' in declaration")["line"]
        ident = self._expect("ID", "Expected variable name after 'int'")

        value = None
        if self.stream.match("ASSIGN"):
            value = self._parse_expression()

        self._expect("SEMI", "Missing semicolon ';' at end of declaration")
        return Declaration(ident["value"], value, line=line)

    def _parse_assignment(self):
        ident = self._expect("ID", "Expected variable name")
        line = ident["line"]
        self._expect("ASSIGN", "Expected '=' in assignment")
        value = self._parse_expression()
        self._expect("SEMI", "Missing semicolon ';' at end of assignment")
        return Assignment(ident["value"], value, line=line)

    def _parse_printf(self):
        line = self._expect("PRINTF", "Expected 'printf'")["line"]
        self._expect("LPAREN", "Missing opening parenthesis '(' in printf statement")

        format_string = None
        args = []

        if self.stream.check("STRING"):
            format_string = self.stream.advance()["value"]
            if self.stream.match("COMMA"):
                args = self._parse_arg_list()
        else:
            args = [self._parse_expression()]

        self._expect("RPAREN", "Missing closing parenthesis ')' in printf statement")
        self._expect("SEMI", "Missing semicolon ';' at end of printf statement")
        return Printf(format_string, args, line=line)

    def _parse_arg_list(self):
        args = [self._parse_expression()]
        while self.stream.match("COMMA"):
            args.append(self._parse_expression())
        return args

    def _parse_if(self):
        line = self._expect("IF", "Expected 'if'")["line"]
        self._expect("LPAREN", "Missing opening parenthesis '(' after 'if'")
        condition = self._parse_condition()
        self._expect("RPAREN", "Missing closing parenthesis ')' after condition")
        self._expect("LBRACE", "Missing opening brace '{' for if statement body")

        body = []
        while not self.stream.check("RBRACE") and not self.stream.at_end():
            try:
                stmt = self._parse_statement()
                if stmt is not None:
                    body.append(stmt)
            except ParseError as exc:
                self._add_error(exc.line, "Syntax", exc.message)
                self._synchronize()

        self._expect("RBRACE", "Missing closing brace '}' for if statement body")
        return IfStatement(condition, body, line=line)

    def _parse_condition(self):
        left = self._parse_expression()
        token = self.stream.current()

        if token["type"] not in self.COMPARISON_OPS:
            raise ParseError(token["line"], "Expected comparison operator in if condition")

        self.stream.advance()
        right = self._parse_expression()
        op = self.COMPARISON_OPS[token["type"]]
        return Comparison(op, left, right, line=token["line"])

    def _parse_expression(self):
        expr = self._parse_term()

        while True:
            op = self.stream.match("PLUS", "MINUS")
            if op is None:
                break
            right = self._parse_term()
            expr = BinaryOp(op["value"], expr, right, line=op["line"])

        return expr

    def _parse_term(self):
        expr = self._parse_factor()

        while True:
            op = self.stream.match("TIMES", "DIVIDE")
            if op is None:
                break
            right = self._parse_factor()
            expr = BinaryOp(op["value"], expr, right, line=op["line"])

        return expr

    def _parse_factor(self):
        if self.stream.match("NUMBER"):
            tok = self.stream.previous()
            return Number(tok["value"], line=tok["line"])

        if self.stream.match("ID"):
            tok = self.stream.previous()
            return Identifier(tok["value"], line=tok["line"])

        if self.stream.match("LPAREN"):
            expr = self._parse_expression()
            self._expect("RPAREN", "Missing closing parenthesis ')' in expression")
            return expr

        raise ParseError(self._line(), "Expected number, identifier, or parenthesized expression")


if __name__ == "__main__":
    code = """
    int x = 5;
    int y = 10;
    int sum = x + y;
    if (x < y) {
        printf("%d %d", x, y);
    }
    """

    parser = Parser()
    ast, errors = parser.parse(code)
    print("AST:", ast)
    print("Errors:", errors)