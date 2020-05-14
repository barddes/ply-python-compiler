import ply.lex as lex


class UCLexer:
    """ A lexer for the uC language. After building it, set the
        input text with input(), and call token() to get new
        tokens.
    """

    def __init__(self, error_func):
        """ Create a new Lexer.
        """
        self.error_func = error_func
        self.filename = ''
        self.lexer = None

        # Keeps track of the last token returned from self.token()
        self.last_token = None

    def build(self, **kwargs):
        """ Builds the lexer from the specification.

            This method exists separately, because the PLY
            manual warns against calling lex.lex inside __init__
        """
        self.lexer = lex.lex(object=self, **kwargs)
        return self

    def reset_lineno(self):
        """ Resets the internal line number counter of the lexer.
        """
        self.lexer.lineno = 1

    def input(self, text):
        self.lexer.input(text)

    def token(self):
        self.last_token = self.lexer.token()
        return self.last_token

    def find_tok_column(self, token):
        """ Find the column of the token in its line.
        """
        last_cr = self.lexer.lexdata.rfind('\n', 0, token.lexpos)
        return token.lexpos - last_cr

    # Internal auxiliary methods
    def _error(self, msg, token):
        """
            An error function. Will be called with an error
            message and a token as arguments, in case of
            an error during lexing.
        """
        location = self._make_tok_location(token)
        self.error_func(msg, location[0], location[1])
        self.lexer.skip(1)

    def _make_tok_location(self, token):
        return token.lineno, self.find_tok_column(token)

    # Reserved keywords
    keywords = (
        'ASSERT', 'BREAK', 'CHAR', 'ELSE', 'FLOAT', 'FOR', 'IF',
        'INT', 'PRINT', 'READ', 'RETURN', 'VOID', 'WHILE',
    )

    keyword_map = {}
    for keyword in keywords:
        keyword_map[keyword.lower()] = keyword

    #
    # All the tokens recognized by the lexer
    #
    tokens = keywords + (
        # Identifiers
        'ID', 'EQ', 'LE', 'GE', 'LT', 'GT', 'NE', 'AND', 'OR', 'PLUSPLUS', 'MINUSMINUS', 'TIMESEQUALS',
        'PLUSEQUALS', 'MINUSEQUALS', 'DIVIDEEQUALS', 'MODEQUALS', 'PLUS', 'MINUS', 'TIMES',
        'DIVIDE', 'ADDRESS', 'MOD', 'EQUALS', 'SEMI', 'LBRACE', 'RBRACE', 'LBRACKET', 'RBRACKET',
        'LPAREN', 'RPAREN', 'FLOAT_CONST', 'INT_CONST', 'STR_CONST', 'CHAR_CONST', 'COMMA', 'EXMARK'
    )

    #
    # Rules
    #
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
    t_COMMA = r','
    t_EXMARK = r'!'
    t_ignore = ' \t'
    t_ignore_comment = r'//.*'
    t_ignore_commentblock = r'/\*(.|\n)*?\*/'

    # Newlines
    def t_NEWLINE(self, t):
        r'\n+'
        t.lexer.lineno += t.value.count("\n")

    def t_ID(self, t):
        r'[a-zA-Z_][0-9a-zA-Z_]*'
        t.type = self.keyword_map.get(t.value, "ID")
        return t

    def t_FLOAT_CONST(self, t):
        r'([0-9]+\.[0-9]*)|([0-9]*\.[0-9]+)'
        t.value = float(t.value)
        return t

    def t_INT_CONST(self, t):
        r'[0-9]+'
        t.value = int(t.value)
        return t

    def t_CHAR_CONST(self, t):
        r"'.'"
        t.value = t.value[1]
        return t

    def t_STR_CONST(self, t):
        r'"[^\n"]*"'
        t.value = t.value[1:]
        t.value = t.value[:-1]
        return t

    def t_comment(self, t):
        r'/\*(.|\n)*?\*/'
        t.lexer.lineno += t.value.count('\n')

    def t_unfinishedcommentblock(self, t):
        r'/\*(.(?!\*/)|\n)*$'
        print(str(t.lexer.lineno) + ": Unterminated comment: " + t.value)
        t.lexer.skip(1)

    def t_unfinishedstring(self, t):
        r'"[^"]*?\n'
        print(str(t.lexer.lineno) + ": Unterminated string")
        t.lexer.lineno += 1
        t.lexer.skip(1)

    def t_error(self, t):
        msg = "Illegal character %s" % repr(t.value[0])
        self._error(msg, t)

    # Scanner (used only for test)
    def scan(self, data):
        self.lexer.input(data)
        while True:
            tok = self.lexer.token()
            if not tok:
                break
            print(tok)


if __name__ == '__main__':
    import sys


    def print_error(msg, x, y):
        print("Lexical error: %s at %d:%d" % (msg, x, y))


    m = UCLexer(print_error).build()  # Build the lexer
    # m.scan(open(sys.argv[1]).read())  # print tokens
    m.scan(open('teste.uc').read())  # print tokens
