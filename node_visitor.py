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

    def visit(self, node, depth):
        """ Visit a node.
        """

        return self.generic_visit(node, depth)

    def generic_visit(self, node, depth):
        """ Called if no explicit visitor function exists for a
            node. Implements preorder visiting of the node.
        """
        tabs = "".join(['\t' for _ in range(depth)])

        try:
            print(tabs + str(node))
            for c in node:
                self.visit(c, depth + 1)
        except Exception as _:
            print(tabs + "FALTA IMPLEMENTAR " + node.__class__.__name__)
