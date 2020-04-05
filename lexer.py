import ply.lex as lex


class Lexer:
    tokens = [
        'EQ', 'LE', 'GE', 'LT', 'GT', 'NE', 'AND', 'OR', 'PLUSPLUS', 'MINUSMINUS', 'TIMESEQUALS',
        'PLUSEQUALS', 'MINUSEQUALS', 'DIVIDEEQUALS', 'MODEQUALS', 'PLUS', 'MINUS', 'TIMES',
        'DIVIDE', 'ADDRESS', 'MOD', 'EQUALS', 'SEMI', 'LBRACE', 'RBRACE', 'LBRACKET', 'RBRACKET',
        'LPAREN', 'RPAREN', 'FLOAT_CONST', 'INT_CONST', 'SCONST', 'CHAR_CONST', 'COMMA', 'EXMARK', 'ID'
    ]

    reserved = {
        'void': 'VOID',
        'char': 'CHAR',
        'int': 'INT',
        'float': 'FLOAT',
        'if': 'IF',
        'else': 'ELSE',
        'while': 'WHILE',
        'for': 'FOR',
        'return': 'RETURN',
        'break': 'BREAK',
        'assert': 'ASSERT',
        'print': 'PRINT',
        'read': 'READ'
    }

    tokens = tokens + list(reserved.values())

    t_EQ = r'=='
    t_LE = r'<='
    t_GE = r'>='
    t_LT = r'<'
    t_GT = r'>'
    t_NE = r'!='
    t_AND = r'&&'
    t_OR = r'\|\|'
    t_PLUSPLUS = r'\+\+'
    t_MINUSMINUS = r'--'
    t_TIMESEQUALS = r'\*='
    t_PLUSEQUALS = r'\+='
    t_MINUSEQUALS = r'-='
    t_DIVIDEEQUALS = r'/='
    t_MODEQUALS = r'%='
    t_PLUS = r'\+'
    t_MINUS = r'-'
    t_TIMES = r'\*'
    t_DIVIDE = r'/'
    t_ADDRESS = r'&'
    t_MOD = r'%'
    t_EQUALS = r'='
    t_SEMI = r';'
    t_LBRACE = r'\{'
    t_RBRACE = r'\}'
    t_LBRACKET = r'\['
    t_RBRACKET = r'\]'
    t_LPAREN = r'\('
    t_RPAREN = r'\)'
    t_SCONST = r'"[^\n"]*"'
    t_COMMA = r','
    t_EXMARK = r'!'
    t_ignore = ' \t'
    t_ignore_comment = r'//.*'
    t_ignore_commentblock = r'/\*(.|\n)*?\*/'

    def __init__(self, module=None, input=None, debug=False):
        self._module = module if module else self
        self._input = input
        self._debug = debug
        self._lexer = lex.lex(module=self._module, debug=self._debug)

        if self._input:
            self.execute()

    def __iter__(self):
        return self

    def __next__(self):
        token = self.token()
        if token:
            return token

        raise StopIteration

    def ply_lexer(self):
        return self._lexer

    def reset(self):
        self._lexer = lex.lex(module=self._module, debug=self._debug)

    def input(self, input=None):
        if input:
            self._input = input
            self.execute()
            return self
        else:
            return self._input

    def module(self, module=None):
        if module:
            self._module = module
            self._lexer = lex.lex(module=self._module, debug=self._debug)
            self.execute()
            return self
        else:
            return self._module

    def debug(self, debug=None):
        if debug:
            self._debug = debug
            self.execute()
            return self
        else:
            return self._debug

    def execute(self):
        if self._lexer and self._input:
            self._lexer.input(self._input)

    def token(self):
        if self._lexer:
            return self._lexer.token()
        else:
            return None

    def t_FLOAT_CONST(self, t):
        r"""([0-9]+\.[0-9]*)|([0-9]*\.[0-9]+)"""
        t.value = float(t.value)
        return t

    def t_INT_CONST(self, t):
        r"""[0-9]+"""
        t.value = int(t.value)
        return t

    def t_CHAR_CONST(self, t):
        r"""'.'"""
        t.value = t.value[1]
        return t

    def t_ID(self, t):
        r"""[a-zA-Z_][0-9a-zA-Z_]*"""
        t.type = self.reserved.get(t.value, 'ID')  # Confere se não é uma palavra reservada
        return t

    def t_newline(self, t):
        r"""\n+"""
        t.lexer.lineno += len(t.value)

    def t_unfinishedstring(self, t):
        r'"[^"]*?\n'
        print(str(t.lexer.lineno) + ": Unterminated string")
        t.lexer.lineno += 1
        t.lexer.skip(1)

    def t_unfinishedcommentblock(self, t):
        r"""/\*(.(?!\*/)|\n)*$"""
        print(str(t.lexer.lineno) + ": Unterminated comment: " + t.value)
        t.lexer.skip(1)

    def t_error(self, t):
        print("Illegal character '%s' at line %d column %d" % (t.value[0], t.lineno, self.find_column(t)))
        t.lexer.skip(1)

    # Compute column.
    #     input is the input text string
    #     token is a token instance
    def find_column(self, token):
        line_start = self._input.rfind('\n', 0, token.lexpos) + 1
        return (token.lexpos - line_start) + 1

