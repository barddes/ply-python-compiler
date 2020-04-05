class Node(object):
    """
    Base class example for the AST nodes.

    By default, instances of classes have a dictionary for attribute storage.
    This wastes space for objects having very few instance variables.
    The space consumption can become acute when creating large numbers of instances.

    The default can be overridden by defining __slots__ in a class definition.
    The __slots__ declaration takes a sequence of instance variables and reserves
    just enough space in each instance to hold a value for each variable.
    Space is saved because __dict__ is not created for each instance.
    """
    __slots__ = ()

    def children(self):
        """ A sequence of all children that are Nodes. """
        pass

    def __str__(self):
        return self.__class__.__name__ + ":"


class ArrayDecl(Node):
    __slots__ = ('values', 'coord')

    def __init__(self, values, coord=None):
        self.values = values
        self.coord = coord

    def children(self):
        return self.values

    attr_names = ('values',)


class ArrayRef(Node):
    __slots__ = ('values', 'coord')

    def __init__(self, values, coord=None):
        self.values = values
        self.coord = coord

    def children(self):
        return self.values

    attr_names = ('values',)


class Assert(Node):
    __slots__ = ('expr', 'coord')

    def __init__(self, expr, coord=None):
        self.expr = expr
        self.coord = coord

    def children(self):
        return self.expr

    attr_names = ('expr',)


class Assignment(Node):
    __slots__ = ('values', 'coord')

    def __init__(self, values, coord=None):
        self.values = values
        self.coord = coord

    def children(self):
        return self.values

    attr_names = ('values',)


class BinaryOp(Node):
    __slots__ = ('values', 'coord')

    def __init__(self, values, coord=None):
        self.values = values
        self.coord = coord

    def children(self):
        return self.values

    attr_names = ('values',)


class Break(Node):
    __slots__ = ('coord')

    def __init__(self, coord=None):
        self.coord = coord

    attr_names = ()


class Cast(Node):
    __slots__ = ('type', 'expr', 'coord')

    def __init__(self, type, expr, coord=None):
        self.type = type
        self.expr = expr
        self.coord = coord

    def children(self):
        return self.type

    attr_names = ('type', 'expr')


class Compound(Node):
    __slots__ = ('decl_list', 'stmt_list', 'coord')

    def __init__(self, decl_list, stmt_list, coord=None):
        self.decl_list = decl_list
        self.stmt_list = stmt_list
        self.coord = coord

    def children(self):
        return (self.decl_list, self.stmt_list)

    attr_names = ('decl_list', 'stmt_list')


class Constant(Node):
    __slots__ = ('type', 'value', 'coord')

    def __init__(self, type, value, coord=None):
        self.type = type
        self.value = value
        self.coord = coord

    def __iter__(self):
        return iter([])

    def __next__(self):
        raise StopIteration

    def __str__(self):
        return "Constant: %s, %s" % (self.type, self.value)

    attr_names = ('type', 'value',)


class DeclList(Node):
    __slots__ = ('list', 'coord')

    def __init__(self, list, coord=None):
        self.list = list
        self.coord = coord

    def children(self):
        return self.list

    attr_names = ('list',)


class Decl(Node):
    __slots__ = ('type', 'declarations', 'coord')

    def __init__(self, type, declarations, coord=None):
        self.type = type
        self.declarations = declarations
        self.coord = coord

    def __iter__(self):
        return iter([self.type, self.declarations])

    def __next__(self):
        yield self.type
        yield self.declarations
        raise StopIteration

    attr_names = ('type', 'declarations')


class EmptyStatement(Node):
    __slots__ = ('values', 'coord')

    def __init__(self, values, coord=None):
        self.values = values
        self.coord = coord

    def children(self):
        return self.values

    attr_names = ('values',)


class ExprList(Node):
    __slots__ = ('values', 'coord')

    def __init__(self, values, coord=None):
        self.values = values
        self.coord = coord

    def children(self):
        return self.values

    attr_names = ('values',)


class For(Node):
    __slots__ = ('p1', 'p2', 'p3', 'statement', 'coord')

    def __init__(self, p1, p2, p3, statement, coord=None):
        self.p1 = p1
        self.p2 = p2
        self.p3 = p3
        self.statement = statement
        self.coord = coord

    def children(self):
        return self.p1, self.p2, self.p3, self.statement

    attr_names = ('p1', 'p2', 'p3', 'statement')


class FuncCall(Node):
    __slots__ = ('values', 'coord')

    def __init__(self, values, coord=None):
        self.values = values
        self.coord = coord

    def children(self):
        return self.values

    attr_names = ('values',)


class FuncDecl(Node):
    __slots__ = ('values', 'coord')

    def __init__(self, values, coord=None):
        self.values = values
        self.coord = coord

    def children(self):
        return self.values

    attr_names = ('values',)


class FuncDef(Node):
    __slots__ = ('type', 'decl', 'decl_list', 'compound', 'coord')

    def __init__(self, type, decl, decl_list, compound, coord=None):
        self.type = type
        self.decl = decl
        self.decl_list = decl_list
        self.compound = compound

    def children(self):
        return []

    attr_names = ('type', 'decl', 'decl_list', 'compound')


class GlobalDecl(Node):
    __slots__ = ('decl', 'coord')

    def __init__(self, decl, coord=None):
        self.decl = decl
        self.coord = coord

    def __iter__(self):
        return iter([self.decl])

    def __next__(self):
        yield self.decl
        raise StopIteration

    attr_names = ('decl',)


class If(Node):
    __slots__ = ('expr', 'then', 'elze', 'coord')

    def __init__(self, expr, then, elze, coord=None):
        self.expr = expr
        self.then = then
        self.elze = elze
        self.coord = coord

    def children(self):
        if self.elze:
            return self.then, self.elze
        else:
            return self.then,

    attr_names = ('expr', 'then', 'else')


class Id(Node):
    __slots__ = ('name', 'coord')

    def __init__(self, name, coord=None):
        self.name = name
        self.coord = coord

    def __iter__(self):
        return iter([])

    def __next__(self):
        raise StopIteration

    def __str__(self):
        return "ID(name='%s')" % self.name

    attr_names = ('name',)


class InitList(Node):
    __slots__ = ('values', 'coord')

    def __init__(self, values, coord=None):
        self.values = values
        self.coord = coord

    def children(self):
        return self.values

    attr_names = ('values',)


class ParamList(Node):
    __slots__ = ('values', 'coord')

    def __init__(self, values, coord=None):
        self.values = values
        self.coord = coord

    def children(self):
        return self.values

    attr_names = ('values',)


class Print(Node):
    __slots__ = ('expr', 'coord')

    def __init__(self, expr, coord=None):
        self.expr = expr
        self.coord = coord

    def children(self):
        return self.expr

    attr_names = ('expr',)


class Program(Node):
    __slots__ = ('decl_list', 'coord')

    def __init__(self, decl_list, coord=None):
        self.decl_list = decl_list
        self.coord = coord

    def __iter__(self):
        return iter(self.decl_list)

    def __next__(self):
        for decl in self.decl_list:
            yield decl
        raise StopIteration

    attr_names = ('decl_list',)


class PtrDecl(Node):
    __slots__ = ('values', 'coord')

    def __init__(self, values, coord=None):
        self.values = values
        self.coord = coord

    def children(self):
        return self.values

    attr_names = ('values',)


class Read(Node):
    __slots__ = ('expr', 'coord')

    def __init__(self, expr, coord=None):
        self.expr = expr
        self.coord = coord

    def children(self):
        return self.expr

    attr_names = ('expr',)


class Return(Node):
    __slots__ = ('value', 'coord')

    def __init__(self, value, coord=None):
        self.value = value
        self.coord = coord

    def children(self):
        return self.value

    attr_names = ('value',)


class Type(Node):
    __slots__ = ('name', 'coord')

    def __init__(self, name, coord=None):
        self.name = name
        self.coord = coord

    def __iter__(self):
        return iter([])

    def __next__(self):
        raise StopIteration

    def __str__(self):
        return self.__class__.__name__ + ":\t['%s']" % self.name

    attr_names = ('name',)


class Unary(Node):
    __slots__ = ('values', 'coord')

    def __init__(self, values, coord=None):
        self.values = values
        self.coord = coord

    def children(self):
        return self.values

    attr_names = ('values',)


class VarDecl(Node):
    __slots__ = ('decl', 'initial', 'coord')

    def __init__(self, decl, initial=None, coord=None):
        self.decl = decl
        self.initial = initial
        self.coord = coord

    def __iter__(self):
        return iter([self.decl, self.initial])

    def __next__(self):
        yield self.decl
        yield self.initial
        raise StopIteration

    attr_names = ('decl', 'initial',)


class While(Node):
    __slots__ = ('expr', 'statement', 'coord')

    def __init__(self, expr, statement, coord=None):
        self.expr = expr
        self.statement = statement
        self.coord = coord

    def children(self):
        return self.expr, self.statement

    attr_names = ('expr', 'statement')
