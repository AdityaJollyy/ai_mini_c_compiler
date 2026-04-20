"""
lexer.py:
Mini-C Compiler Lexer
Tokenizes a subset of C language without external lexer libraries
"""

# List of token names
tokens = (
    # Keywords
    'INT',
    'IF',
    'PRINTF',
    
    # Identifiers and literals
    'ID',
    'NUMBER',
    'STRING',
    
    # Operators
    'PLUS',
    'MINUS',
    'TIMES',
    'DIVIDE',
    'ASSIGN',
    
    # Comparison operators
    'LT',
    'GT',
    'LE',
    'GE',
    'EQ',
    'NE',
    
    # Delimiters
    'LPAREN',
    'RPAREN',
    'LBRACE',
    'RBRACE',
    'SEMI',
    'COMMA',
)

# Reserved words mapping
reserved = {
    'int': 'INT',
    'if': 'IF',
    'printf': 'PRINTF',
}

# Ignored characters (spaces and tabs)
t_ignore = ' \t\r'


class Token:
    """Simple token object."""

    def __init__(self, token_type, value, lineno, lexpos):
        self.type = token_type
        self.value = value
        self.lineno = lineno
        self.lexpos = lexpos


class MiniCLexerEngine:
    """Lexer engine with input/token API."""

    def __init__(self):
        self.data = ""
        self.pos = 0
        self.length = 0
        self.lineno = 1
        self.errors = []

    def input(self, code):
        self.data = code or ""
        self.pos = 0
        self.length = len(self.data)
        self.lineno = 1
        self.errors = []

    def _peek(self, offset=0):
        idx = self.pos + offset
        if idx >= self.length:
            return ""
        return self.data[idx]

    def _advance(self, count=1):
        for _ in range(count):
            if self.pos >= self.length:
                return
            if self.data[self.pos] == '\n':
                self.lineno += 1
            self.pos += 1

    def _add_error(self, message):
        self.errors.append({
            'line': self.lineno,
            'type': 'Lexical',
            'message': message
        })

    def token(self):
        while self.pos < self.length:
            ch = self._peek()

            # Skip whitespace
            if ch in t_ignore:
                self._advance()
                continue

            # Newlines
            if ch == '\n':
                self._advance()
                continue

            # Comments
            if ch == '/' and self._peek(1) == '/':
                self._advance(2)
                while self.pos < self.length and self._peek() != '\n':
                    self._advance()
                continue

            if ch == '/' and self._peek(1) == '*':
                self._advance(2)
                while self.pos < self.length:
                    if self._peek() == '*' and self._peek(1) == '/':
                        self._advance(2)
                        break
                    self._advance()
                else:
                    self._add_error("Unterminated block comment")
                continue

            start_pos = self.pos
            line = self.lineno

            # Two-character operators
            two = ch + self._peek(1)
            if two in {'<=', '>=', '==', '!='}:
                token_type = {
                    '<=': 'LE',
                    '>=': 'GE',
                    '==': 'EQ',
                    '!=': 'NE',
                }[two]
                self._advance(2)
                return Token(token_type, two, line, start_pos)

            # Single-character tokens
            single_char_tokens = {
                '+': 'PLUS',
                '-': 'MINUS',
                '*': 'TIMES',
                '/': 'DIVIDE',
                '=': 'ASSIGN',
                '<': 'LT',
                '>': 'GT',
                '(': 'LPAREN',
                ')': 'RPAREN',
                '{': 'LBRACE',
                '}': 'RBRACE',
                ';': 'SEMI',
                ',': 'COMMA',
            }
            if ch in single_char_tokens:
                self._advance()
                return Token(single_char_tokens[ch], ch, line, start_pos)

            # String literal
            if ch == '"':
                value_chars = ['"']
                self._advance()
                escaped = False

                while self.pos < self.length:
                    curr = self._peek()

                    if curr == '\n' and not escaped:
                        self._add_error("Unterminated string literal")
                        return None

                    value_chars.append(curr)
                    self._advance()

                    if escaped:
                        escaped = False
                        continue

                    if curr == '\\':
                        escaped = True
                        continue

                    if curr == '"':
                        value = ''.join(value_chars)
                        return Token('STRING', value, line, start_pos)

                self._add_error("Unterminated string literal")
                return None

            # Identifier / reserved word
            if ch.isalpha() or ch == '_':
                ident = []
                while self.pos < self.length:
                    curr = self._peek()
                    if curr.isalnum() or curr == '_':
                        ident.append(curr)
                        self._advance()
                    else:
                        break
                value = ''.join(ident)
                token_type = reserved.get(value, 'ID')
                return Token(token_type, value, line, start_pos)

            # Number literal
            if ch.isdigit():
                digits = []
                while self.pos < self.length and self._peek().isdigit():
                    digits.append(self._peek())
                    self._advance()
                return Token('NUMBER', int(''.join(digits)), line, start_pos)

            # Error handling
            if ch == "'":
                message = "Single quotes not supported. Use double quotes for strings"
            elif ch in '[]':
                message = f"Arrays are not supported in Mini-C (found '{ch}')"
            elif ch == '&':
                message = "Pointers/address-of operator not supported in Mini-C"
            elif ch == '#':
                message = "Preprocessor directives not supported in Mini-C"
            else:
                message = f"Illegal character '{ch}'"

            self._add_error(message)
            self._advance()

        return None


class Lexer:
    
    def __init__(self):
        self.lexer = MiniCLexerEngine()
    
    def tokenize(self, code):
        """
        Tokenize the input code and return tokens and errors
        
        Args:
            code: String containing Mini-C source code
            
        Returns:
            tuple: (list of tokens, list of errors)
        """
        self.lexer.input(code)
        
        tokens_list = []
        while True:
            tok = self.lexer.token()
            if not tok:
                break
            tokens_list.append({
                'type': tok.type,
                'value': tok.value,
                'line': tok.lineno,
            })
        
        return tokens_list, self.lexer.errors
    
    def get_lexer(self):
        """Return the lexer engine for parser integration."""
        return self.lexer


# For testing
if __name__ == "__main__":
    test_code = """
    int x;
    int y = 10;
    x = 5;
    if (x > 3) {
        printf("%d", x);
    }
    printf("%d %d", x, y);
    """
    
    lexer = Lexer()
    tokens, errors = lexer.tokenize(test_code)
    
    print("Tokens:")
    for tok in tokens:
        print(f"  {tok}")
    
    if errors:
        print("\nErrors:")
        for err in errors:
            print(f"  Line {err['line']}: {err['message']}")