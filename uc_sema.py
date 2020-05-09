from uc_type import IntType, FloatType, CharType, BoolType, ArrayType, StringType, PtrType, VoidType


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

    def visit(self, node):
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

    def generic_visit(self, node):
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
        self[name] = value

    def set(self, name: str, value):
        if self.merge_with and name not in self:
            self.merge_with[name] = value
        else:
            self[name] = value

    def lookup(self, name):
        if self.merge_with and name not in self:
            return self.merge_with.get(name, None)
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
            "bool": BoolType,
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

    # def add_local(self, name, value):
    #     self.peek().add(name, value)

    # def add_root(self, name, value):
    #     self.root.add(name, value)

    # def lookup(self, name):
    #     for scope in reversed(self.stack):
    #         hit = scope.lookup(name)
    #         if hit is not None:
    #             return hit
    #     return None

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

    def visit_Program(self, node):
        node.env = self.global_env
        node.global_env = self.global_env
        node.type = None

        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_BinaryOp(self, node):
        # 1. Make sure left and right operands have the same type
        # 2. Make sure the operation is supported
        # 3. Assign the result type

        # self.visit(node.left)
        # self.visit(node.right)
        # node.node_type = node.left.type

        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_Assignment(self, node):
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

    def visit_ArrayDecl(self, node):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_ArrayRef(self, node):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_Assert(self, node):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_Break(self, node):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_Cast(self, node):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_Compound(self, node):
        node.env = Environment(merge_with=node.env)

        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_Constant(self, node):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_DeclList(self, node):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_Decl(self, node):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_EmptyStatement(self, node):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_ExprList(self, node):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_For(self, node):
        node.env = Environment(merge_with=node.env)

        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_FuncCall(self, node):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_FuncDecl(self, node):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_FuncDef(self, node):
        node.env = Environment()

        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_GlobalDecl(self, node):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_If(self, node):
        node.env = Environment(merge_with=node.env)

        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_ID(self, node):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_InitList(self, node):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_ParamList(self, node):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_Print(self, node):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_PtrDecl(self, node):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_Read(self, node):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_Return(self, node):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_Type(self, node):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_UnaryOp(self, node):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_VarDecl(self, node):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_While(self, node):
        node.env = Environment(merge_with=node.env)

        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)
