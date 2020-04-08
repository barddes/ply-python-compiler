import sys


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
        return []

    def __str__(self):
        return self.__class__.__name__ + ":"

    def _repr(self, obj):
        """
        Get the representation of an object, with dedicated pprint-like format for lists.
        """
        if isinstance(obj, list):
            return '[' + (',\n '.join((self._repr(e).replace('\n', '\n ') for e in obj))) + '\n]'
        else:
            return repr(obj)

    def __repr__(self):
        """ Generates a python representation of the current node
        """
        result = self.__class__.__name__ + '('
        indent = ''
        separator = ''
        for name in self.__slots__[:-2]:
            result += separator
            result += indent
            result += name + '=' + (
                self._repr(getattr(self, name)).replace('\n',
                                                        '\n  ' + (' ' * (len(name) + len(self.__class__.__name__)))))
            separator = ','
            indent = ' ' * len(self.__class__.__name__)
        result += indent + ')'
        return result

    def show(self, buf=sys.stdout, offset=0, attrnames=False, nodenames=False, showcoord=False, _my_node_name=None):
        """ Pretty print the Node and all its attributes and children (recursively) to a buffer.
            buf:
                Open IO buffer into which the Node is printed.
            offset:
                Initial offset (amount of leading spaces)
            attrnames:
                True if you want to see the attribute names in name=value pairs. False to only see the values.
            nodenames:
                True if you want to see the actual node names within their parents.
            showcoord:
                Do you want the coordinates of each Node to be displayed.
        """
        lead = ' ' * offset
        if nodenames and _my_node_name is not None:
            buf.write(lead + self.__class__.__name__ + ' <' + _my_node_name + '>: ')
        else:
            buf.write(lead + self.__class__.__name__ + ': ')

        if self.attr_names:
            if attrnames:
                nvlist = [(n, getattr(self, n)) for n in self.attr_names if getattr(self, n) is not None]
                attrstr = ', '.join('%s=%s' % nv for nv in nvlist)
            else:
                vlist = [getattr(self, n) for n in self.attr_names]
                attrstr = ', '.join('%s' % v for v in vlist)
            buf.write(attrstr)

        if showcoord and self.coord:
            buf.write('%s' % self.coord)
        buf.write('\n')

        for (child_name, child) in self.children():
            child.show(buf, offset + 4, attrnames, nodenames, showcoord, child_name)


class ArrayDecl(Node):
    __slots__ = ('dir_dec', 'const_exp', 'coord')

    def __init__(self, dir_dec, const_exp, coord=None):
        self.dir_dec = dir_dec
        self.const_exp = const_exp
        self.coord = coord

    def children(self):
        if self.dir_dec is not None:
            yield self.dir_dec
        if self.const_exp is not None:
            yield self.const_exp

    def __str__(self):
        return "ArrayDecl:"

    attr_names = ('dir_dec', 'const_exp')


class ArrayRef(Node):
    __slots__ = ('post_expr', 'expr', 'coord')

    def __init__(self, post_expr, expr, coord=None):
        self.post_expr = post_expr
        self.expr = expr
        self.coord = coord

    def children(self):
        if self.post_expr is not None:
            yield self.post_expr
        if self.expr is not None:
            yield self.expr

    def __str__(self):
        return "ArrayRef:"

    attr_names = ('post_expr', 'expr')


class Assert(Node):
    __slots__ = ('expr', 'coord')

    def __init__(self, expr, coord=None):
        self.expr = expr
        self.coord = coord

    def children(self):
        if self.expr:
            yield self.expr

    attr_names = ('expr',)


class Break(Node):
    __slots__ = ('coord',)

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
        if self.type:
            yield self.type
        if self.expr:
            yield self.expr

    attr_names = ('type', 'expr')


class Compound(Node):
    __slots__ = ('decl_list', 'stmt_list', 'coord')

    def __init__(self, decl_list, stmt_list, coord=None):
        self.decl_list = decl_list
        self.stmt_list = stmt_list
        self.coord = coord

    def children(self):
        if self.decl_list:
            yield 'decl_list', self.decl_list
        if self.stmt_list:
            yield 'stmt_list', self.stmt_list

    def __str__(self):
        return "Compound:"

    attr_names = ('decl_list', 'stmt_list')


class Constant(Node):
    __slots__ = ('type', 'value', 'coord')

    def __init__(self, type, value, coord=None):
        self.type = type
        self.value = value
        self.coord = coord

    def children(self):
        pass

    def __str__(self):
        return "Constant: %s, %s" % (self.type, self.value)

    attr_names = ('type', 'value',)


class DeclList(Node):
    __slots__ = ('list', 'coord')

    def __init__(self, list, coord=None):
        self.list = list
        self.coord = coord

    def children(self):
        if self.list:
            return self.list
        return []

    attr_names = ('list',)


class Decl(Node):
    __slots__ = ('type', 'declarations', 'coord')

    def __init__(self, type, declarations, coord=None):
        self.type = type
        self.declarations = declarations
        self.coord = coord

    def children(self):
        if self.type:
            yield self.type
        if self.declarations:
            yield self.declarations

    attr_names = ('type', 'declarations')


class EmptyStatement(Node):
    __slots__ = ('coord',)

    def __init__(self, coord=None):
        self.coord = coord

    def children(self):
        return []

    attr_names = ()


class ExprList(Node):
    __slots__ = ('expr1', 'expr2', 'coord')

    def __init__(self, expr1, expr2, coord=None):
        self.expr1 = expr1
        self.expr2 = expr2
        self.coord = coord

    def children(self):
        if self.expr1 is not None:
            yield self.expr1
        if self.expr2 is not None:
            yield self.expr2

    def __str__(self):
        return "ExprList:"

    attr_names = ('expr1', 'expr2')


class For(Node):
    __slots__ = ('p1', 'p2', 'p3', 'statement', 'coord')

    def __init__(self, p1, p2, p3, statement, coord=None):
        self.p1 = p1
        self.p2 = p2
        self.p3 = p3
        self.statement = statement
        self.coord = coord

    def children(self):
        if self.p1:
            yield self.p1
        if self.p2:
            yield self.p2
        if self.p3:
            yield self.p3
        if self.statement:
            yield self.statement

    attr_names = ('p1', 'p2', 'p3', 'statement')


class FuncCall(Node):
    __slots__ = ('expr1', 'expr2', 'coord')

    def __init__(self, expr1, expr2, coord=None):
        self.expr1 = expr1
        self.expr1 = expr2
        self.coord = coord

    def children(self):
        if self.expr1:
            yield self.expr1
        if self.expr2:
            yield self.expr2

    def __str__(self):
        return "FuncCall:"

    attr_names = ('expr1', 'expr2')


class FuncDecl(Node):
    __slots__ = ('expr1', 'expr2', 'coord')

    def __init__(self, expr1, expr2, coord=None):
        self.expr1 = expr1
        self.expr2 = expr2
        self.coord = coord

    def children(self):
        if self.expr1:
            yield 'expr1', self.expr1
        if self.expr2:
            yield 'expr2', self.expr2

    def __str__(self):
        return "FuncDecl:"

    attr_names = ('expr1', 'expr2')


class FuncDef(Node):
    __slots__ = ('type', 'decl', 'decl_list', 'compound', 'coord')

    def __init__(self, type, decl, decl_list, compound, coord=None):
        self.type = type
        self.decl = decl
        self.decl_list = decl_list
        self.compound = compound
        self.coord = coord

    def children(self):
        if self.type:
            yield 'type', self.type
        if self.decl:
            yield 'decl', self.decl
        if self.decl_list:
            # for i, d in enumerate(self.decl_list):
            yield 'decl_list', self.decl_list
        if self.compound:
            yield 'compound', self.compound

    def __str__(self):
        return "FuncDef:"

    attr_names = ('type', 'decl', 'decl_list', 'compound')


class GlobalDecl(Node):
    __slots__ = ('decl', 'coord')

    def __init__(self, decl, coord=None):
        self.decl = decl
        self.coord = coord

    def children(self):
        if self.decl:
            yield 'decl', self.decl

    attr_names = ('decl',)


class If(Node):
    __slots__ = ('expr', 'then', 'elze', 'coord')

    def __init__(self, expr, then, elze, coord=None):
        self.expr = expr
        self.then = then
        self.elze = elze
        self.coord = coord

    def children(self):
        if self.expr:
            yield self.expr
        if self.then:
            yield self.then
        if self.elze:
            yield self.elze

    attr_names = ('expr', 'then', 'else')


class Id(Node):
    __slots__ = ('name', 'coord')

    def __init__(self, name, coord=None):
        self.name = name
        self.coord = coord

    def children(self):
        return []

    def __str__(self):
        return "ID(name='%s')" % self.name

    attr_names = ('name',)


class InitList(Node):
    __slots__ = ('values', 'coord')

    def __init__(self, values, coord=None):
        self.values = values
        self.coord = coord

    def children(self):
        if self.values:
            yield self.values

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

    def children(self):
        for i, d in enumerate(self.decl_list):
            yield ('decl_list[%d]' % i, d)

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

    def children(self):
        return []

    def __str__(self):
        return self.__class__.__name__ + ":\t['%s']" % self.name

    attr_names = ('name',)


class VarDecl(Node):
    __slots__ = ('decl', 'initial', 'coord')

    def __init__(self, decl, initial=None, coord=None):
        self.decl = decl
        self.initial = initial
        self.coord = coord

    def children(self):
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


# Yuji fez, revisar!
class BinaryOp(Node):
    __slots__ = ('op', 'expr1', 'expr2', 'coord')

    def __init__(self, op, expr1, expr2, coord=None):
        self.op = op
        self.expr1 = expr1
        self.expr2 = expr2
        self.coord = coord

    def children(self):
        if self.op is not None:
            yield self.op
        if self.expr1 is not None:
            yield self.expr1
        if self.expr2 is not None:
            yield self.expr2

    def __str__(self):
        return "BinaryOP: %s" % self.op

    attr_names = ('op', 'expr1', 'expr2')


# Yuji fez, revisar!
class UnaryOp(Node):
    __slots__ = ('op', 'expr1', 'coord')

    def __init__(self, op, expr1, coord=None):
        self.op = op
        self.expr1 = expr1
        self.coord = coord

    def children(self):
        if self.op is not None:
            yield self.op
        if self.expr1 is not None:
            yield self.expr1

    def __str__(self):
        return "UnaryOP: %s" % self.op

    attr_names = ('op', 'expr1')


# Yuji fez, revisar!
class UnaryOp_postfix(Node):
    __slots__ = ('op', 'expr1', 'coord')

    def __init__(self, op, expr1, coord=None):
        self.op = op
        self.expr1 = expr1
        self.coord = coord

    def children(self):
        if self.op is not None:
            yield self.op
        if self.expr1 is not None:
            yield self.expr1

    def __str__(self):
        return "UnaryOP: p%s" % self.op

    attr_names = ('op', 'expr1')


# Yuji fez, revisar! Talvez tenha errado no children(self):
class Assignment(Node):
    __slots__ = ('op', 'coord')

    def __init__(self, op, coord=None):
        self.op = op

    # não possui filhos
    def children(self):
        return iter([])

    def __str__(self):
        return "Assignment: %s" % self.op

    attr_names = ('op',)


class Coord(object):
    """ Coordinates of a syntactic element. Consists of:
            - Line number
            - (optional) column number, for the Lexer
    """
    __slots__ = ('line', 'column')

    def __init__(self, line, column=None):
        self.line = line
        self.column = column

    def __str__(self):
        if self.line:
            coord_str = "   @ %s:%s" % (self.line, self.column)
        else:
            coord_str = ""
        return coord_str
