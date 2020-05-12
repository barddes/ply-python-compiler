import sys

from objects import Decl, While, VarDecl, UnaryOp, Type, Return, Read, Program, BinaryOp, Assignment, ArrayDecl, \
    ArrayRef, Assert, Break, Cast, Compound, Constant, DeclList, EmptyStatement, ExprList, For, FuncCall, FuncDecl, \
    FuncDef, GlobalDecl, If, ID, InitList, ParamList, Print, PtrDecl, Node
from uc_parser import UCParser
from uc_type import IntType, FloatType, CharType, ArrayType, StringType, PtrType, VoidType


class NodeVisitor(object):
    """ A base NodeVisitor class for visiting uc_ast nodes.
        Subclass it and define your own visit_XXX methods, where
        XXX is the class name you want to visit with these
        methods.

        For example:

        class ConstantVisitor(NodeVisitor):
            def __init__(self):
                self.values = []

            def visit_Constant(self, node):
                self.values.append(node.value)

        Creates a list of values of all the constant nodes
        encountered below the given node. To use it:

        cv = ConstantVisitor()
        cv.visit(node)

        Notes:

        *   generic_visit() will be called for AST nodes for which
            no visit_XXX method was defined.
        *   The children of nodes for which a visit_XXX was
            defined will not be visited - if you need this, call
            generic_visit() on the node.
            You can use:
                NodeVisitor.generic_visit(self, node)
        *   Modeled after Python's own AST visiting facilities
            (the ast module of Python 3.0)
    """

    _method_cache = None

    def visit(self, node: Node):
        """ Visit a node.
        """

        if self._method_cache is None:
            self._method_cache = {}

        visitor = self._method_cache.get(node.__class__.__name__, None)
        if visitor is None:
            method = 'visit_' + node.__class__.__name__
            visitor = getattr(self, method, self.generic_visit)
            self._method_cache[node.__class__.__name__] = visitor

        return visitor(node)

    def generic_visit(self, node: Node):
        """ Called if no explicit visitor function exists for a
            node. Implements preorder visiting of the node.
        """
        for c in node:
            self.visit(c)


class SymbolTable(dict):
    '''
    Class representing a symbol table.  It should provide functionality
    for adding and looking up nodes associated with identifiers.
    '''

    __slots__ = ('merge_with',)

    def __init__(self, merge_with: 'SymbolTable' = None):
        super().__init__()
        # self.decl = decl
        self.merge_with = merge_with

    def add(self, name: str, value):
        if name in self:
            raise Exception("Variavel '%s' já definida no escopo." % name)

        self[name] = value

    def set(self, name: str, value):
        if self.merge_with and name not in self:
            self.merge_with[name] = value
        else:
            self[name] = value

    def lookup(self, name: str):
        if self.merge_with and name not in self:
            return self.merge_with.lookup(name)
        else:
            return self.get(name, None)

    # def return_type(self):
    #     if self.decl:
    #         return self.decl.returntype
    #     return None


class Environment(object):
    def __init__(self, merge_with: 'Environment' = None):
        # self.stack = []
        # self.stack.append(self.symtab)

        merge_symtable = None if not merge_with else merge_with.symtable
        self.symtable = SymbolTable(merge_with=merge_symtable)
        self.symtable.update({
            "int": IntType,
            "float": FloatType,
            "char": CharType,
            "array": ArrayType,
            "string": StringType,
            "prt": PtrType,
            "void": VoidType
        })

    # def push(self, enclosure):
    #     self.stack.append(SymbolTable(decl=enclosure))

    # def pop(self):
    #     self.stack.pop()

    # def peek(self):
    #     return self.stack[-1]

    # def scope_level(self):
    #     return len(self.stack)

    def add_local_var(self, name, info):
        try:
            self.symtable.add(name, info)
        except Exception as e:
            print('ERROR: ' + str(e), file=sys.stderr)

    # def add_root(self, name, value):
    #     self.root.add(name, value)

    def lookup(self, name):
        return self.symtable.lookup(name)

    # def print(self):
    #     for indent, scope in enumerate(reversed(self.stack)):
    #         print("Scope for {}".format("ROOT" if scope.decl is None else scope.decl))
    #         print(scope, indent=indent * 4, width=20)


class Visitor(NodeVisitor):
    '''
    Program visitor class. This class uses the visitor pattern. You need to define methods
    of the form visit_NodeName() for each kind of AST node that you want to process.
    Note: You will need to adjust the names of the AST nodes if you picked different names.
    '''

    def __init__(self):
        self.global_env = Environment()
        self.global_symtable = self.global_env.symtable

    def BinaryOp_check(self, node: BinaryOp):
        expr1 = node.expr1
        expr2 = node.expr2
        op = node.op

        if expr1.name_type.typename != expr2.name_type.typename:
            print("Error. ", expr1.name_type.typename, op, expr2.name_type.typename, file=sys.stderr)
        elif op not in expr1.name_type.binary_ops:
            print("Error (unsupported op %s)" % op, file=sys.stderr)

        return expr1.name_type

    def UnaryOp_check(self, node: UnaryOp):
        expr1 = node.expr1
        op = node.op

        if op not in expr1.name_type.unary_ops:
            print("Error (unsupported op %s)" % op, file=sys.stderr)

        return expr1.name_type

    def visit_Program(self, node: Program):
        node.env = self.global_env
        node.global_env = self.global_env
        node.name_type = None

        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_BinaryOp(self, node: BinaryOp):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

        node.name_type = self.BinaryOp_check(node)

    def visit_Assignment(self, node: Assignment):
        # ## 1. Make sure the location of the assignment is defined
        # sym = self.symtab.lookup(node.location)
        # assert sym, "Assigning to unknown sym"
        # ## 2. Check that the types match
        # self.visit(node.value)
        # assert sym.type == node.value.type, "Type mismatch in assignment"

        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_ArrayDecl(self, node: ArrayDecl):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_ArrayRef(self, node: ArrayRef):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_Assert(self, node: Assert):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_Break(self, node: Break):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_Cast(self, node: Cast):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_Compound(self, node: Compound):
        node.env = Environment(merge_with=node.env)

        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_Constant(self, node: Constant):

        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_DeclList(self, node: DeclList):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_Decl(self, node: Decl):
        name = node.name.name
        info = {
            'func': isinstance(node.decl, FuncDecl),
            'type': {
                'int': IntType,
                'char': CharType,
                'float': FloatType,
                'string': StringType,
                'void': VoidType
            }[node.type.name[0]]
        }

        if info['func']:
            node.global_env.add_local_var(name, info)
        node.env.add_local_var(name, info)

        node.name_type = info['type']

        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

        if node.init and node.init.name_type != node.name_type:
            print('Error.  %s = %s' % (node.name_type, node.init.name_type), file=sys.stderr)

    def visit_EmptyStatement(self, node: EmptyStatement):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_ExprList(self, node: ExprList):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_For(self, node: For):
        node.env = Environment(merge_with=node.env)

        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_FuncCall(self, node: FuncCall):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_FuncDecl(self, node: FuncDecl):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_FuncDef(self, node: FuncDef):
        node.env = Environment()

        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_GlobalDecl(self, node: GlobalDecl):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_If(self, node: If):
        node.env = Environment(merge_with=node.env)

        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_ID(self, node: ID):
        name = node.name

        if not node.env.lookup(name) and not node.global_env.lookup(name):
            print("ERROR: Variável '%s' não definida." % name, file=sys.stderr)
            node.env.add_local_var(name, {
                'func': False,
                'type': VoidType
            })

        if node.env.lookup(name):
            node.name_type = node.env.lookup(name)['type']
        else:
            node.name_type = node.global_env.lookup(name)['type']

    def visit_InitList(self, node: InitList):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_ParamList(self, node: ParamList):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_Print(self, node: Print):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_PtrDecl(self, node: PtrDecl):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_Read(self, node: Read):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_Return(self, node: Return):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_Type(self, node: Type):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_UnaryOp(self, node: UnaryOp):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

        node.name_type = self.UnaryOp_check(node)

    def visit_VarDecl(self, node: VarDecl):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_While(self, node: While):
        node.env = Environment(merge_with=node.env)

        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)


if __name__ == '__main__':
    m = UCParser()
    ast = m.parse(source=open('teste.c').read(), _=None, debug=True)
    ast.show()

    visitor = Visitor()
    visitor.visit(ast)
