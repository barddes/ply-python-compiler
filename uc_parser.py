import ply.yacc as yacc

from objects import *
from uc_lexer import UCLexer
from functools import partial as bind


class UCParser:
    """ A parser for the uC language. After building it, parse the input
        with parse()
    """

    tokens = ()

    precedence = (
        ('left', 'EQUALS'),
        ('left', 'OR', 'AND'),
        ('left', 'EQ', 'NE', 'GT', 'GE', 'LT', 'LE'),
        ('left', 'PLUSPLUS', 'MINUSMINUS'),
        ('left', 'PLUS', 'MINUS'),
        ('left', 'TIMES', 'DIVIDE', 'MOD')
    )

    def __init__(self, error_func=None):
        """ Create a new Parser.
        """
        self.error_func = error_func if error_func else self.error
        self.filename = ''
        self.parser = None
        self.lexer = None

        self.last_generated_tree = None

        self.lexer = UCLexer(error_func=bind(self.error, lexer=True)).build()
        self.tokens = self.lexer.tokens
        self.parser = yacc.yacc(module=self)

    def error(self, msg, lineno=None, colno=None, p=None, lexer=False):
        if lineno and colno:
            print('%s Error: [%d,%d] %s' % ('Lexer' if lexer else 'Parser', lineno, colno, msg))
        else:
            print('%s Error: %s' % ('Lexer' if lexer else 'Parser', msg))

        if p:
            stack_state_str = ' '.join([symbol.type for symbol in self.parser.symstack][1:])
            print('Parser State:{} {} . {}'
                  .format(self.parser.state,
                          stack_state_str,
                          p))

    def parse(self, source, _, debug):
        # self.lexer.scan(source)
        self.parser.parse(source, lexer=self.lexer.lexer, debug=debug)
        return self.last_generated_tree

    def _token_coord(self, p, token_idx):
        last_cr = p.lexer.lexdata.rfind('\n', 0, p.lexpos(token_idx))
        if last_cr < 0:
            last_cr = -1
        column = (p.lexpos(token_idx) - last_cr)
        return Coord(p.lineno(token_idx), column)

    def p_program(self, p):
        """ program : global_declaration_list
        """
        p[0] = Program(decl_list=p[1])

        self.last_generated_tree = p[0]

    def p_global_declaration_list(self, p):
        """ global_declaration_list : global_declaration
                                    | global_declaration_list global_declaration
        """
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1] + [p[2]]

    def p_global_declaration_0(self, p):
        """ global_declaration : declaration
        """
        p[0] = GlobalDecl(p[1])

    def p_global_declaration_1(self, p):
        """ global_declaration : function_definition
        """
        p[0] = p[1]

    def p_function_definition(self, p):
        """ function_definition : type_specifier declarator declaration_list_opt compound_statement
                                | declarator declaration_list_opt compound_statement
        """
        if len(p) == 5:
            p[0] = FuncDef(p[1], p[2], p[3], p[4])
        else:
            p[0] = FuncDef(None, p[1], p[2], p[3])

    def p_declaration_list(self, p):
        """ declaration_list : declaration
                             | declaration_list declaration
        """
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = p[1] + p[2]

    def p_declaration_list_opt(self, p):
        """ declaration_list_opt : declaration_list
                                 | empty
        """
        p[0] = p[1]

    def p_type_specifier(self, p):
        """ type_specifier : VOID
                           | CHAR
                           | INT
                           | FLOAT
        """
        p[0] = Type([p[1]], coord=self._token_coord(p, 1))

    def p_declaration(self, p):
        """ declaration : type_specifier init_declarator_list_opt SEMI
        """

        if p[2]:
            for decl in p[2]:
                decl.set_type(p[1])

        p[0] = p[2]

    def p_declarator(self, p):
        """ declarator : direct_declarator
                       | pointer_opt direct_declarator
        """
        if len(p) == 2:
            p[0] = p[1]

            if type(p[0]) == ArrayDecl:
                p[0] = self.invert_array_decl(p[0])
        else:
            p[1].set_name(p[2])
            p[0] = p[1]

    def p_pointer_opt(self, p):
        """ pointer_opt : TIMES pointer
                        | TIMES empty
        """
        p[0] = PtrDecl(p[2])

    def p_pointer(self, p):
        """ pointer : pointer_opt
        """
        p[0] = p[1]

    def p_direct_declarator(self, p):
        """ direct_declarator : identifier
                              | LPAREN declarator RPAREN
                              | direct_declarator LBRACKET constant_expression_opt RBRACKET
                              | direct_declarator LPAREN parameter_list RPAREN
                              | direct_declarator LPAREN identifier_list_opt RPAREN
        """
        if len(p) == 2:
            p[0] = VarDecl(p[1])
        elif len(p) == 4:
            p[0] = p[2]
        elif p[2] == '[':
            p[0] = ArrayDecl(p[1], p[3])
        else:
            p[0] = FuncDecl(p[1], p[3])

    def p_identifier(self, p):
        """ identifier : ID
        """
        p[0] = ID(name=p[1], coord=self._token_coord(p, 1))

    def p_constant_expression_opt(self, p):
        """ constant_expression_opt : constant_expression
                                    | empty
        """
        p[0] = p[1]

    def p_identifier_list(self, p):
        """ identifier_list : identifier
                            | identifier_list identifier
        """
        if len(p) == 2:
            p[0] = p[1]
        elif len(p) == 3:
            p[0] = p[1] + [p[2]]

    def p_identifier_list_opt(self, p):
        """ identifier_list_opt : identifier_list
                                | empty
        """
        p[0] = p[1]

    def p_constant_expression(self, p):
        """ constant_expression : binary_expression
        """
        p[0] = p[1]

    def p_binary_expression(self, p):
        """ binary_expression : cast_expression
                              | binary_expression TIMES binary_expression
                              | binary_expression DIVIDE binary_expression
                              | binary_expression MOD binary_expression
                              | binary_expression PLUS binary_expression
                              | binary_expression MINUS binary_expression
                              | binary_expression LT binary_expression
                              | binary_expression LE binary_expression
                              | binary_expression GT binary_expression
                              | binary_expression GE binary_expression
                              | binary_expression EQ binary_expression
                              | binary_expression NE binary_expression
                              | binary_expression AND binary_expression
                              | binary_expression OR binary_expression
        """
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = BinaryOp(p[2], p[1], p[3])

    def p_cast_expression(self, p):
        """ cast_expression : unary_expression
                            | LPAREN type_specifier RPAREN cast_expression
        """
        if len(p) == 2:
            p[0] = p[1]
        elif len(p) == 5:
            p[0] = Cast(type=p[2], expr=p[4])

    def p_unary_expression(self, p):
        """ unary_expression : postfix_expression
                             | PLUSPLUS unary_expression
                             | MINUSMINUS unary_expression
                             | unary_operator cast_expression
        """
        if len(p) == 2:
            p[0] = p[1]
        elif len(p) == 3:
            p[0] = UnaryOp(p[1], p[2])

    def p_postfix_expression(self, p):
        """ postfix_expression : primary_expression
                               | postfix_expression LBRACKET expression RBRACKET
                               | postfix_expression LPAREN argument_expression_opt RPAREN
                               | postfix_expression PLUSPLUS
                               | postfix_expression MINUSMINUS
        """
        if len(p) == 2:
            p[0] = p[1]
        elif len(p) == 3:
            p[0] = UnaryOp('p' + p[2], p[1])
        elif p[2] == '[':
            p[0] = ArrayRef(p[1], p[3])
        elif p[2] == '(':
            p[0] = FuncCall(p[1], p[3])

    def p_argument_expression_opt(self, p):
        """ argument_expression_opt : argument_expression
                                    | empty
        """
        p[0] = p[1]

    def p_primary_expression(self, p):
        """ primary_expression : identifier
                               | constant
                               | LPAREN expression RPAREN
        """
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = p[2]

    def p_constant_1(self, p):
        """ constant : INT_CONST
                     | FLOAT_CONST
                     | STR_CONST
        """
        p[0] = Constant(type=type(p[1]).__name__, value=p[1], coord=self._token_coord(p, 1))

    def p_constant_2(self, p):
        """ constant : CHAR_CONST
        """
        p[0] = Constant(type='char', value=p[1], coord=self._token_coord(p, 1))

    def p_expression(self, p):
        """ expression : assignment_expression
                       | expression COMMA assignment_expression
        """
        if len(p) == 2:
            p[0] = p[1]
        else:
            if isinstance(p[1], ExprList):
                p[0] = p[1] + ExprList([p[3]])
            else:
                p[0] = ExprList([p[1], p[3]])

    def p_argument_expression(self, p):
        """ argument_expression : assignment_expression
                                | argument_expression COMMA assignment_expression
        """
        if len(p) == 2:
            p[0] = p[1]
        else:
            if isinstance(p[1], ExprList):
                p[0] = p[1] + ExprList([p[3]])
            else:
                p[0] = ExprList([p[1], p[3]])

    def p_assignment_expression(self, p):
        """ assignment_expression : binary_expression
                                  | unary_expression assignment_operator assignment_expression
        """
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = Assignment(p[2], p[1], p[3])

    def p_assignment_operator(self, p):
        """ assignment_operator : EQUALS
                                | TIMESEQUALS
                                | DIVIDEEQUALS
                                | MODEQUALS
                                | PLUSEQUALS
                                | MINUSEQUALS
        """
        p[0] = p[1]

    def p_unary_operator(self, p):
        """ unary_operator : ADDRESS
                           | TIMES
                           | PLUS
                           | MINUS
                           | EXMARK
        """
        p[0] = p[1]

    def p_parameter_list(self, p):
        """ parameter_list : parameter_declaration
                           | parameter_list COMMA parameter_declaration
        """
        if len(p) == 2:
            p[0] = ParamList([p[1]])
        else:
            p[0] = p[1] + ParamList([p[3]])

    def p_parameter_declaration(self, p):
        """ parameter_declaration : type_specifier declarator
        """
        p[2].set_type(p[1])
        p[0] = Decl(p[2])

    def p_init_declarator_list_opt(self, p):
        """ init_declarator_list_opt : init_declarator_list
                                     | empty
        """
        p[0] = p[1]

    def p_init_declarator_list(self, p):
        """ init_declarator_list : init_declarator
                                 | init_declarator_list COMMA init_declarator
        """

        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1] + [p[3]]

    def p_init_declarator(self, p):
        """ init_declarator : declarator
                            | declarator EQUALS initializer
        """
        if len(p) == 2:
            p[0] = Decl(decl=p[1], init=EmptyStatement())
        else:
            p[0] = Decl(decl=p[1], init=p[3])

    def p_initializer(self, p):
        """ initializer : assignment_expression
                        | LBRACE initializer_list RBRACE
                        | LBRACE initializer_list COMMA RBRACE
        """
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = p[2]

    def p_initializer_list(self, p):
        """ initializer_list : initializer
                             | initializer_list COMMA initializer
        """
        if len(p) == 2:
            p[0] = InitList([p[1]], coord=p[1].coord)
        else:
            p[0] = p[1] + InitList([p[3]])

    def p_compound_statement(self, p):
        """ compound_statement : LBRACE declaration_list_opt statement_list_opt RBRACE
        """
        p[0] = Compound(p[2], p[3])

    def p_statement_list(self, p):
        """ statement_list : statement
                           | statement_list statement
        """
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1] + [p[2]]

    def p_statement_list_opt(self, p):
        """ statement_list_opt : statement_list
                               | empty
        """
        p[0] = p[1]

    def p_statement(self, p):
        """ statement : expression_statement
                      | compound_statement
                      | selection_statement
                      | iteration_statement
                      | jump_statement
                      | assert_statement
                      | print_statement
                      | read_statement
        """
        p[0] = p[1]

    def p_expression_statement(self, p):
        """ expression_statement : expression_opt SEMI
        """
        p[0] = p[1]

    def p_expression_opt(self, p):
        """ expression_opt : expression
                           | empty
        """
        p[0] = p[1]

    def p_selection_statement(self, p):
        """ selection_statement : IF LPAREN expression RPAREN statement
                                | IF LPAREN expression RPAREN statement ELSE statement
        """
        if len(p) == 6:
            p[0] = If(expr=p[3], then=p[5], elze=None, coord=self._token_coord(p, 1))
        else:
            p[0] = If(expr=p[3], then=p[5], elze=p[7], coord=self._token_coord(p, 1),
                      coord_else=self._token_coord(p, 6))

    def p_iteration_statement(self, p):
        """ iteration_statement : WHILE LPAREN expression RPAREN statement
                                | FOR LPAREN expression_opt SEMI expression_opt SEMI expression_opt RPAREN statement
                                | FOR LPAREN declaration expression_opt SEMI expression_opt RPAREN statement
        """
        if len(p) == 6:
            p[0] = While(expr=p[3], statement=p[5], coord=self._token_coord(p, 1))
        elif len(p) == 9:
            p[0] = For(p1=DeclList(p[3], coord=self._token_coord(p, 1)), p2=p[4], p3=p[6], statement=p[8],
                       coord=self._token_coord(p, 1))
        else:
            p[0] = For(p1=p[3], p2=p[5], p3=p[7], statement=p[9], coord=self._token_coord(p, 1))

    def p_jump_statement(self, p):
        """ jump_statement : BREAK SEMI
                           | RETURN expression_opt SEMI
        """
        if len(p) == 3:
            p[0] = Break()
        else:
            p[0] = Return(value=p[2], coord=self._token_coord(p, 1))

    def p_assert_statement(self, p):
        """ assert_statement : ASSERT expression SEMI
        """
        p[0] = Assert(expr=p[2], coord=self._token_coord(p, 1))

    def p_print_statement(self, p):
        """ print_statement : PRINT LPAREN expression_opt RPAREN SEMI
        """
        p[0] = Print(expr=p[3], coord=self._token_coord(p, 1))

    def p_read_statement(self, p):
        """ read_statement : READ LPAREN argument_expression RPAREN SEMI
        """
        p[0] = Read(expr=p[3], coord=self._token_coord(p, 1))

    def p_empty(self, p):
        """ empty :
        """
        p[0] = EmptyStatement()

    def p_error(self, p):
        self.error('Unvalid token!', p.lineno, self.find_tok_column(p))

    def find_tok_column(self, token):
        """ Find the column of the token in its line.
        """
        last_cr = self.lexer.lexdata.rfind('\n', 0, token.lexpos)
        return token.lexpos - last_cr

    def invert_array_decl(self, p):
        arrays = []

        while type(p) == ArrayDecl:
            arrays.append(p)
            p = p.dir_dec

        arrays.reverse()
        for i in range(len(arrays)):
            if i == len(arrays) - 1:
                arrays[i].dir_dec = p
            else:
                arrays[i].dir_dec = arrays[i + 1]

        return arrays[0]


if __name__ == '__main__':
    m = UCParser()
    ast = m.parse(source=open('teste.uc').read(), _=None, debug=True)
    ast.show()
