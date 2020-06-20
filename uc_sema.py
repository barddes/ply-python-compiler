import sys

from objects import Decl, While, VarDecl, UnaryOp, Type, Return, Read, Program, BinaryOp, Assignment, ArrayDecl, \
    ArrayRef, Assert, Break, Cast, Compound, Constant, DeclList, EmptyStatement, ExprList, For, FuncCall, FuncDecl, \
    FuncDef, GlobalDecl, If, ID, InitList, ParamList, Print, PtrDecl, Node, NodeInfo
from uc_parser import UCParser


def print_error(*args):
    msg = ' '.join([str(x) for x in args])
    assert False, msg
    # print(msg, file=sys.stderr)


class uCType(object):
    '''
    Class that represents a type in the uC language.  Types
    are declared as singleton instances of this type.
    '''

    def __init__(self, typename, binary_ops=None, unary_ops=None, rel_ops=None, assign_ops=None):
        self.typename = typename
        self.unary_ops = unary_ops if unary_ops else set()
        self.binary_ops = binary_ops if binary_ops else set()
        self.rel_ops = rel_ops if rel_ops else set()
        self.assign_ops = assign_ops if assign_ops else set()

    def __eq__(self, other):
        if not self or not other:
            return False
        elif self.typename == 'any' or other.typename == 'any':
            return True
        else:
            return self.typename == other.typename

    def __ne__(self, other):
        return not self == other

    def __str__(self):
        return self.typename

    def __repr__(self):
        return self.typename


EmptyType = uCType(None)

AnyType = uCType('any',
                 unary_ops={"-", "+", "--", "++", "p--", "p++", "*", "&"},
                 binary_ops={"+", "-", "*", "/", "%"},
                 rel_ops={"==", "!=", "<", ">", "<=", ">=", "&&", "||"},
                 assign_ops={"=", "+=", "-=", "*=", "/=", "%="}
                 )

IntType = uCType("int",
                 unary_ops={"-", "+", "--", "++", "p--", "p++", "*", "&"},
                 binary_ops={"+", "-", "*", "/", "%"},
                 rel_ops={"==", "!=", "<", ">", "<=", ">="},
                 assign_ops={"=", "+=", "-=", "*=", "/=", "%="}
                 )

FloatType = uCType("float",
                   unary_ops={"-", "+", "*", "&"},
                   binary_ops={"+", "-", "*", "/", "%"},
                   rel_ops={"==", "!=", "<", ">", "<=", ">="},
                   assign_ops={"=", "+=", "-=", "*=", "/=", "%="}
                   )

CharType = uCType("char",
                  unary_ops={"*", "&"},
                  rel_ops={"==", "!=", "&&", "||"},
                  )

ArrayType = uCType("array",
                   unary_ops={"*", "&"},
                   rel_ops={"==", "!="}
                   )

StringType = uCType("string",
                    unary_ops={},
                    binary_ops={"+"},
                    rel_ops={"==", "!="}
                    )

PtrType = uCType("ptr",
                 unary_ops={"*", "&"},
                 rel_ops={"==", "!="}
                 )

VoidType = uCType("void",
                  unary_ops={"*", "&"},
                  binary_ops={}
                  )

BoolType = uCType("bool",
                  rel_ops={"==", "!=", "&&", "||"}
                  )


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
        for i, c in node.children():
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
    def __init__(self, merge_with: 'Environment' = None, func_def=None):
        # self.stack = []
        # self.stack.append(self.symtab)
        self.consts = []
        self.vars = []
        self.functions = []

        if merge_with:
            self.func_def = merge_with.func_def

        if func_def:
            self.func_def = func_def

        merge_symtable = None if not merge_with else merge_with.symtable
        self.symtable = SymbolTable(merge_with=merge_symtable)
        self.symtable.update({
            "int": {'type': IntType},
            "float": {'type': FloatType},
            "char": {'type': CharType},
            "array": {'type': ArrayType},
            "string": {'type': StringType},
            "prt": {'type': PtrType},
            "void": {'type': VoidType}
        })

    # def push(self, enclosure):
    #     self.stack.append(SymbolTable(decl=enclosure))

    # def pop(self):
    #     self.stack.pop()

    # def peek(self):
    #     return self.stack[-1]

    # def scope_level(self):
    #     return len(self.stack)

    def add_global_const(self, const):
        if isinstance(const, str):
            return self.add_global_str(const)
        else:
            return self.add_global_array(const)

    def unbox_InitList(self, list):
        return [x.value if type(x) != InitList else self.unbox_InitList(x.list) for x in list]

    def add_global_array(self, array):
        array = self.unbox_InitList(array.list)
        self.consts.append(array)

        idx = self.consts.index(array)
        # self.symtable[] = NodeInfo({
        #     'location': '.str.%d' % idx,
        #     'global': True
        # })
        return idx

    def add_global_str(self, str):
        if str not in self.consts:
            self.consts.append(str)

        idx = self.consts.index(str)
        # self.symtable[] = NodeInfo({
        #     'location': '.str.%d' % idx,
        #     'global': True
        # })

        return idx

    def add_global_var(self, var):
        self.vars.append(var)

    def add_local_var(self, name, info):
        try:
            self.symtable.add(name, info)
        except Exception as e:
            print_error('Error. ' + str(e))

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

        if expr1.node_info != expr2.node_info:
            print_error("Error. ", expr1.node_info['type'].typename, op, expr2.node_info['type'].typename)

        # nao tenho certeza se esta certo mas concerta o erro do teste 1
        elif op not in expr1.node_info['type'].binary_ops and op not in expr1.node_info['type'].rel_ops:
            print_error("Error (unsupported op %s)" % op)

        if op in expr1.node_info['type'].rel_ops:
            return BoolType

        return expr1.node_info['type']

    def UnaryOp_check(self, node: UnaryOp):
        expr1 = node.expr1
        op = node.op

        if op not in expr1.node_info['type'].unary_ops:
            print_error("Error (unsupported op %s)" % op)

        return expr1.node_info['type']

    def visit_Program(self, node: Program):
        node.env = self.global_env
        node.global_env = self.global_env
        node.node_info = None

        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_BinaryOp(self, node: BinaryOp):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

        node.node_info = NodeInfo({'type': self.BinaryOp_check(node)})

    def visit_Assignment(self, node: Assignment):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

        if node.name.node_info != node.assign_expr.node_info:
            print_error('Error (cannot assign %s to %s)' % (
                ''.join(['*' for _ in range(node.assign_expr.node_info['depth'])]) + str(
                    node.assign_expr.node_info['type']),
                ''.join(['*' for _ in range(node.name.node_info['depth'])]) + str(node.name.node_info['type'])))

    def visit_ArrayDecl(self, node: ArrayDecl):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

        node.node_info = NodeInfo({
            'array': True,
            'length': None if not node.const_exp else node.const_exp.value,
            'type': node.dir_dec.node_info['type'],
            'depth': node.dir_dec.node_info['depth'] + 1
        })

    def visit_ArrayRef(self, node: ArrayRef):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

        if node.expr.node_info['type'] != IntType:
            print_error('Error (array index must be of type int)')

        node.node_info = NodeInfo(node.post_expr.node_info)
        node.node_info['depth'] -= 1
        if node.node_info['depth'] == 0:
            node.node_info['array'] = False
        node.node_info['length'] = None

    def visit_Assert(self, node: Assert):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

        if node.expr.node_info['type'] != BoolType:
            print_error('Error. Assert expression must evaluate a BoolType')

        node.error_str = self.global_env.add_global_const(
            'assertion_fail on %d:%d' % (node.coord.line, node.coord.column + len('assert ')))

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

        node.node_info = NodeInfo({
            'type': {
                'int': IntType,
                'char': CharType,
                'float': FloatType,
                'string': StringType,
                'void': VoidType
            }[node.type.name[0]]
        })

    def visit_Compound(self, node: Compound):
        node.env = Environment(merge_with=node.env)

        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_Constant(self, node: Constant):
        pass

    def visit_DeclList(self, node: DeclList):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_Decl(self, node: Decl):
        if node.decl:
            func_names = list(map(lambda x: x['name'], node.global_env.functions))
            if node.decl.name.name in func_names:
                if not self.compare_func_decl(node.decl,
                                              node.global_env.functions[func_names.index(node.decl.name.name)]['node']):
                    print_error('Error. function definition does not match the function declaration')
                else:
                    node.decl = node.global_env.functions[func_names.index(node.decl.name.name)]['node']
            else:
                node.decl.env = node.env
                node.decl.global_env = node.global_env
                self.visit(node.decl)

        if node.init:
            node.init.env = node.env
            node.init.global_env = node.global_env
            self.visit(node.init)

        name = node.name.name
        if isinstance(name, VarDecl):
            name = name.name
        info = node.decl.node_info

        if info['func'] and name not in list(map(lambda x: x['name'], node.global_env.functions)):
            node.global_env.add_local_var(name, info)

            node.global_env.functions.append({
                'name': node.decl.name.name,
                'node': node
            })
        node.env.add_local_var(name, info)

        node.node_info = info

        # size mismatch on initialization
        if isinstance(node.decl, ArrayDecl) and node.decl.const_exp and node.init:
            decl_size = node.decl.const_exp.value
            list_size = len(node.init.list)
            if decl_size != list_size:
                print_error("Error (size mismatch on initialization)")

        if node.init and node.init.node_info != node.node_info:
            print_error('Error.  %s = %s' % (node.node_info['type'], node.init.node_info['type']))

        if node.init and node.init.node_info['type'] == StringType:
            node.lookup_envs(node.decl.dir_dec.name.name)['location'] = \
                node.node_info['index'] = node.global_env.add_global_const(node.init.value[1:-1])
            node.lookup_envs(node.decl.dir_dec.name.name)['params'] = node.init.value[1:-1]

        elif node.init and isinstance(node.decl, ArrayDecl):
            node.lookup_envs(node.decl.dir_dec.name.name)['location'] = \
                node.node_info['index'] = node.global_env.add_global_const(node.init)
            node.lookup_envs(node.decl.dir_dec.name.name)['params'] = node.global_env.unbox_InitList(node.init.list)
        pass

    def visit_EmptyStatement(self, node: EmptyStatement):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

    def visit_ExprList(self, node: ExprList):
        children = []

        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)
            children.append(d)

        node.node_info = children[-1].node_info

    def visit_For(self, node: For):
        node.env = Environment(merge_with=node.env)

        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

        if node.p2.node_info['type'] != BoolType:
            print_error('Error. For condition must evaluate a BoolType')

    def visit_FuncCall(self, node: FuncCall):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

        if node.expr2:
            params = [x.node_info['type'] for x in
                      ([node.expr2] if not isinstance(node.expr2, ExprList) else node.expr2.list)]
            if len(params) != len(node.expr1.node_info['params']):
                print_error(
                    "Number of arguments for call to function '%s' do not match function parameter declaration" % node.expr1.name)
            elif params != node.expr1.node_info['params']:
                print_error(
                    "Types of arguments for call to function '%s' do not match function parameter declaration" % node.expr1.name)

        node.node_info = NodeInfo(node.expr1.node_info)
        node.node_info['func'] = False
        node.node_info['params'] = None

    def visit_FuncDecl(self, node: FuncDecl):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

        node.node_info = node.decl.node_info
        node.node_info['func'] = True
        if node.init:
            node.node_info['params'] = node.init.node_info['params']
        else:
            node.node_info['params'] = []

    def visit_FuncDef(self, node: FuncDef):
        node.env = Environment(func_def=node)

        if node.type:
            node.type.env = node.env
            node.type.global_env = node.global_env
            self.visit(node.type)

        if node.decl:
            node.decl.env = node.env
            node.decl.global_env = node.global_env
            self.visit(node.decl)

        node.node_info = node.decl.node_info

        if node.decl_list:
            node.decl_list.env = node.env
            node.decl_list.global_env = node.global_env
            self.visit(node.decl_list)

        if node.compound:
            node.compound.env = node.env
            node.compound.global_env = node.global_env
            self.visit(node.compound)



    def visit_GlobalDecl(self, node: GlobalDecl):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

        for d in node.decl:
            d.node_info['global'] = True

        for d in node.decl:
            self.global_env.add_global_var(d)

    def visit_If(self, node: If):
        node.env = Environment(merge_with=node.env)

        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

        if node.expr.node_info['type'] != BoolType:
            print_error('Error. If expression must evaluate a BoolType')

    def visit_ID(self, node: ID):
        name = node.name

        if not node.env.lookup(name) and not node.global_env.lookup(name):
            print_error("Error. Variable '%s' not defined." % name)
            node.env.add_local_var(name, NodeInfo({
                'type': AnyType
            }))

        if node.env.lookup(name):
            node.node_info = NodeInfo(node.env.lookup(name))
        else:
            node.node_info = NodeInfo(node.global_env.lookup(name))

    def visit_InitList(self, node: InitList):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

        node.type = {
            'size': max([x.node_info['depth'] for x in node.list])
        }

        # verifica se o vetor possui todos os elementos de mesmo tipo
        type_aux = None
        for element in node.list:
            if type_aux and type_aux != element.type:
                print_error("Error mismatch type in array's elements")
            type_aux = element.type

        node.node_info = NodeInfo({
            'array': True,
            'length': len(node.list),
            'type': EmptyType if len(node.list) == 0 else node.list[0].node_info['type'],
            'depth': max([x.node_info['depth'] for x in node.list]) + 1
        })

    def visit_ParamList(self, node: ParamList):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

        node.node_info = NodeInfo({
            'params': [x.node_info['type'] for x in node.list]
        })

        pass

    def visit_Print(self, node: Print):
        params = []

        if isinstance(node.expr, ExprList):
            params = node.expr.list
        elif node.expr:
            params = [node.expr]

        for d in params:
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

            if isinstance(d, Constant) and d.type == 'string':
                d.node_info['index'] = self.global_env.add_global_const(d.value[1:-1])

    def get_ptr_depth(self, node):
        if node.value:
            return 1 + self.get_ptr_depth(node.value)
        return 1

    def visit_PtrDecl(self, node: PtrDecl):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

        node.node_info = NodeInfo({
            'array': True,
            'depth': self.get_ptr_depth(node),
            'type': {
                'int': IntType,
                'char': CharType,
                'float': FloatType,
                'string': StringType,
                'void': VoidType
            }[node.type.name[0]]
        })
        pass

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

        node.node_info = node.value.node_info
        if not node.node_info:
            node.node_info = NodeInfo({
                'type': VoidType
            })

        node.func_def = node.env.func_def
        if node.node_info['type'] != node.func_def.node_info['type']:
            print_error(
                'Type of return statement expression does not match declared return type for function')


    def visit_Type(self, node: Type):
        node.node_info = NodeInfo({
            'type': {
                'int': IntType,
                'char': CharType,
                'float': FloatType,
                'string': StringType,
                'void': VoidType
            }[node.name[0]]
        })

    def visit_UnaryOp(self, node: UnaryOp):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

        is_array = False
        depth = 0
        if node.expr1:
            is_array = node.expr1.node_info['array']
            depth = node.expr1.node_info['depth']

        if node.op == '&':
            is_array = True
            depth += 1

        node.node_info = NodeInfo({'array': is_array, 'depth': depth, 'type': self.UnaryOp_check(node)})

    def visit_VarDecl(self, node: VarDecl):
        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

        node.node_info = node.type.node_info

    def visit_While(self, node: While):
        node.env = Environment(merge_with=node.env)

        for i, d in node.children():
            d.env = node.env
            d.global_env = node.global_env
            self.visit(d)

        if node.expr.node_info['type'] != BoolType:
            print_error('Error. While expression must evaluate a BoolType')

    def compare_func_decl(self, decl1, decl2):
        try:
            if decl1.decl.name.name != decl2.decl.name.name:
                return False

            if decl1.type.name[0] != decl2.type.name[0]:
                return False

            param1 = list(map(lambda x: {
                'name': x.decl.name.name,
                'type': x.decl.type.name[0]
            }, decl1.init.list))

            param2 = list(map(lambda x: {
                'name': x.decl.name.name,
                'type': x.decl.type.name[0]
            }, decl2.init.list))

            if param1 != param2:
                return False

            return True
        except:
            return False


if __name__ == '__main__':
    m = UCParser()
    ast = m.parse(source=open('teste.uc').read(), _=None, debug=False)
    ast.show()

    visitor = Visitor()
    visitor.visit(ast)
