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
    def __init__(self, decl=None):
        super().__init__()
        self.decl = decl
    def add(self, name, value):
        self[name] = value
    def lookup(self, name):
        return self.get(name, None)
    def return_type(self):
        if self.decl:
            return self.decl.returntype
        return None

class Environment(object):
    def __init__(self):
        self.stack = []
        self.root = SymbolTable()
        self.stack.append(self.root)
        self.root.update({
            "int": IntType,
            "float": FloatType,
            "char": CharType,
            "bool": BoolType,
            "array": ArrayType,
            "string": StringType,
            "prt": PtrType,
            "void": VoidType
        })

    def push(self, enclosure):
        self.stack.append(SymbolTable(decl=enclosure))

    def pop(self):
        self.stack.pop()

    def peek(self):
        return self.stack[-1]

    def scope_level(self):
        return len(self.stack)

    def add_local(self, name, value):
        self.peek().add(name, value)

    def add_root(self, name, value):
        self.root.add(name, value)

    def lookup(self, name):
        for scope in reversed(self.stack):
            hit = scope.lookup(name)
            if hit is not None:
                return hit
        return None

    def print(self):
        for indent, scope in enumerate(reversed(self.stack)):
            print("Scope for {}".format("ROOT" if scope.decl is None else scope.decl))
            pprint(scope, indent=indent*4, width=20)




class Visitor(NodeVisitor):
    '''
    Program visitor class. This class uses the visitor pattern. You need to define methods
    of the form visit_NodeName() for each kind of AST node that you want to process.
    Note: You will need to adjust the names of the AST nodes if you picked different names.
    '''
    def __init__(self):
        # Initialize the symbol table
        self.symtab = SymbolTable()

        # Add built-in type names (int, float, char) to the symbol table
        self.symtab.add("int",uctype.int_type)
        self.symtab.add("float",uctype.float_type)
        self.symtab.add("char",uctype.char_type)

    def visit_Program(self,node):
        # 1. Visit all of the global declarations
        # 2. Record the associated symbol table
        for _decl in node.gdecls:
            self.visit(_decl)

    def visit_BinaryOp(self, node):
        # 1. Make sure left and right operands have the same type
        # 2. Make sure the operation is supported
        # 3. Assign the result type
        self.visit(node.left)
        self.visit(node.right)
        node.type = node.left.type

    def visit_Assignment(self, node):
        ## 1. Make sure the location of the assignment is defined
        sym = self.symtab.lookup(node.location)
        assert sym, "Assigning to unknown sym"
        ## 2. Check that the types match
        self.visit(node.value)
        assert sym.type == node.value.type, "Type mismatch in assignment"