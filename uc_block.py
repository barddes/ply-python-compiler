from objects import Program, BinaryOp, Assignment, ArrayDecl, ArrayRef, Assert, Break, Cast, Compound, Constant, \
    DeclList, Decl, EmptyStatement, ExprList, For, FuncCall, FuncDecl, FuncDef, GlobalDecl, If, ID, InitList, ParamList, \
    Print, PtrDecl, Read, Return, Type, UnaryOp, VarDecl, While, NodeInfo
from uc_sema import NodeVisitor, StringType, CharType, VoidType


# An example of how to create basic blocks

class Block(object):
    def __init__(self, label):
        self.label = label  # Label that identifies the block
        self.instructions = []  # Instructions in the block
        self.predecessors = []  # List of predecessors
        self.next_block = None  # Link to the next block

    def append(self, instr):
        self.instructions.append(instr)

    def __iter__(self):
        return iter(self.instructions)


class BasicBlock(Block):
    '''
    Class for a simple basic block.  Control flow unconditionally
    flows to the next block.
    '''

    def __init__(self, label):
        super(BasicBlock, self).__init__(label)
        self.branch = None  # Not necessary the same as next_block in the linked list


class ConditionBlock(Block):
    """
    Class for a block representing an conditional statement.
    There are two branches to handle each possibility.
    """

    def __init__(self, label):
        super(ConditionBlock, self).__init__(label)
        self.taken = None
        self.fall_through = None


class BlockVisitor(object):
    '''
    Class for visiting basic blocks.  Define a subclass and define
    methods such as visit_BasicBlock or visit_IfBlock to implement
    custom processing (similar to ASTs).
    '''

    def visit(self, block):
        while isinstance(block, Block):
            name = "visit_%s" % type(block).__name__
            if hasattr(self, name):
                getattr(self, name)(block)
            block = block.next_block

class GenerateCode(NodeVisitor):
    unary_ops = {
        '+': '',
        '-': 'sub',
        '++': 'add',
        '--': 'sub',
        'p++': 'add',
        'p--': 'sub',
        '*': 'pointer',
        '&': 'address',
    }

    binary_ops = {
        '+': 'add',
        '-': 'sub',
        '*': 'mul',
        '/': 'div',
        '%': 'mod',
        '&&': 'and',
        '||': 'or',
        '==': 'eq',
        '!=': 'ne',
        '>': 'gt',
        '<': 'lt',
        '>=': 'ge',
        '<=': 'le',
    }

    '''
    Node visitor class that creates 3-address encoded instruction sequences.
    '''

    def __init__(self):
        super(GenerateCode, self).__init__()

        # version dictionary for temporaries
        self.fname = 'main'  # We use the function name as a key
        self.versions = {self.fname: 0}

        # The generated code (list of tuples)
        self.code = []

    def new_temp(self):
        '''
        Create a new temporary variable of a given scope (function name).
        '''
        if self.fname not in self.versions:
            self.versions[self.fname] = 0
        name = "%" + "%d" % (self.versions[self.fname])
        self.versions[self.fname] += 1

        return name

    # You must implement visit_Nodename methods for all of the other
    # AST nodes.  In your code, you will need to make instructions
    # and append them to the self.code list.
    #
    # A few sample methods follow.  You may have to adjust depending
    # on the names of the AST nodes you've defined.

    def visit_Literal(self, node):
        # Create a new temporary variable name
        target = self.new_temp()

        # Make the SSA opcode and append to list of generated instructions
        inst = ('literal_' + node.type.name, node.value, target)
        self.code.append(inst)

        # Save the name of the temporary variable where the value was placed
        node.gen_location = target

    def visit_BinaryOp(self, node: BinaryOp):
        # Visit the left and right expressions
        self.visit(node.expr1)
        self.visit(node.expr2)

        if isinstance(node.expr1, ArrayRef):
            nt = self.new_temp()
            self.code.append(('load_%s_*' % node.expr1.node_info['type'], node.expr1.gen_location, nt))
            node.expr1.gen_location = nt

        if isinstance(node.expr2, ArrayRef):
            nt = self.new_temp()
            self.code.append(('load_%s_*' % node.expr2.node_info['type'], node.expr2.gen_location, nt))
            node.expr2.gen_location = nt

        target = self.new_temp()

        # Create the opcode and append to list
        opcode = self.binary_ops[node.op] + "_" + node.expr1.node_info['type'].typename
        inst = (opcode, node.expr1.gen_location, node.expr2.gen_location, target)
        self.code.append(inst)

        # Store location of the result on the node
        node.gen_location = target

    def visit_VarDeclaration(self, node):
        # allocate on stack memory
        inst = ('alloc_' + node.type.name, node.id)
        self.code.append(inst)
        # store optional init val
        if node.value:
            self.visit(node.value)
            inst = ('store_' + node.type.name, node.value.gen_location, node.id)
            self.code.append(inst)

    def visit_LoadLocation(self, node):
        target = self.new_temp()
        inst = ('load_' + node.type.name, node.name, target)
        self.code.append(inst)
        node.gen_location = target

    def visit_AssignmentStatement(self, node):
        self.visit(node.value)
        inst = ('store_' + node.value.type.name, node.value.gen_location, node.location)
        self.code.append(inst)

    def visit_UnaryOp(self, node: UnaryOp):
        self.visit(node.expr1)

        node_t = node.expr1.node_info['type'].typename

        if node.op == '&':
            if node.assign_left:
                nt = node.lookup_envs(node.assign_left.name.name)['location']
            else:
                nt = self.new_temp()
            self.code.append(('get_%s_*' % node_t, node.expr1.gen_location, nt))
            node.gen_location = nt
            node.node_info = NodeInfo(node.node_info)
            node.node_info['depth'] += 1
            node.node_info['array'] = True
            return

        if node.op == '+':
            node.gen_location = node.expr1.gen_location
            return

        if node.op == '-':
            nt = self.new_temp()
            self.code.append(('literal_%s' % node_t, 0, nt))
            nt2 = self.new_temp()
            self.code.append(('sub_%s' % node_t, nt, node.expr1.gen_location, nt2))
            node.gen_location = nt2
            return

        if node.op in ('--', '++'):
            op = 'add' if node.op == '++' else 'sub'
            nt = self.new_temp()
            self.code.append(('literal_%s' % node_t, 1, nt))
            nt2 = self.new_temp()
            self.code.append(('%s_%s' % (op, node_t), node.expr1.gen_location, nt, nt2))
            var_loc = node.lookup_envs(node.expr1.name)['location']
            self.code.append(('store_%s' % node_t, nt2, var_loc))
            node.gen_location = nt2

        if node.op in ('p--', 'p++'):
            op = 'add' if node.op[1:] == '++' else 'sub'
            nt = self.new_temp()
            self.code.append(('literal_%s' % node_t, 1, nt))
            nt2 = self.new_temp()
            self.code.append(('%s_%s' % (op, node_t), node.expr1.gen_location, nt, nt2))
            var_loc = node.lookup_envs(node.expr1.name)['location']
            self.code.append(('store_%s' % node_t, nt2, var_loc))
            node.gen_location = node.expr1.gen_location

    def get_const_type(self, const):
        if type(const) == list:
            return self.get_const_type(const[0])
        return type(const).__name__

    def get_const_dim(self, const):
        if type(const) == list:
            return ('_%s' % str(len(const))) + self.get_const_dim(const[0])
        return ''

    def visit_Program(self, node: Program):
        for var in node.global_env.vars:
            if var.init:
                if isinstance(var.init, InitList):
                    inst = ('global_%s' % var.decl.type.name[0], '@%s' % var.decl.name.name, node.env.unbox_InitList(var.init.list))
                    if node.env.unbox_InitList(var.init.list) in node.global_env.consts:
                        node.global_env.consts.remove(node.env.unbox_InitList(var.init.list))
                else:
                    inst = ('global_%s' % var.decl.type.name[0], '@%s' % var.decl.name.name, var.init.value)
            else:
                inst = ('global_%s' % var.decl.type.name[0], '@%s' % var.decl.name.name)

            self.code.append(inst)
            var.gen_location = '@%s' % var.decl.name.name
            node.lookup_envs(var.decl.name.name)['location'] = '@%s' % var.decl.name.name

        for i, const in enumerate(node.global_env.consts):
            if type(const) == list:
                inst = ('global_%s' % self.get_const_type(const) + self.get_const_dim(const), '@.str.%d' % i, const)
            else:
                inst = ('global_string', '@.str.%d' % i, const)
            self.code.append(inst)

        for i, d in node.children():
            self.visit(d)

    def visit_Assignment(self, node: Assignment):
        if node.assign_expr:
            node.assign_expr.assign_left = node
            self.visit(node.assign_expr)

        if isinstance(node.name, ArrayRef):
            self.visit(node.name)
            index = node.name.expr.gen_location
            nt = self.new_temp()
            self.code.append(('load_int', index, nt))
            source = node.lookup_envs(node.name.post_expr.name)
            nt2 = self.new_temp()
            self.code.append(('elem_%s' % source['type'], source['location'], nt, nt2))
            left_target = nt2
        else:
            left_target = node.lookup_envs(node.name.name)['location']


        right_target = node.assign_expr.gen_location

        if node.op == '=':
            if not isinstance(node.assign_expr, UnaryOp) or node.assign_expr.op != '&':
                if isinstance(node.assign_expr, ArrayRef):
                    nt = self.new_temp()
                    self.code.append(
                        ('load_%s_*' % node.assign_expr.node_info['type'], node.assign_expr.gen_location, nt))
                    right_target = nt

                if isinstance(node.name, ArrayRef):
                    custom_type = '_*'
                else:
                    custom_type = ''
                self.code.append(
                    ('store_%s' % (node.name.node_info['type'].typename + custom_type), right_target, left_target))

        if node.op in ('+=', '-=', '*=', '/=', '%/'):
            nt = self.new_temp()
            op = {
                '+=': 'add',
                '-=': 'sub',
                '*=': 'mul',
                '/=': 'div',
                '%=': 'mod'
            }[node.op]
            self.code.append(('load_%s' % node.name.node_info['type'], left_target, nt))
            nt2 = self.new_temp()
            self.code.append(('%s_%s' % (op, node.name.node_info['type']), nt, node.assign_expr.gen_location, nt2))
            self.code.append(('store_%s' % node.name.node_info['type'], nt2, left_target))

    def visit_ArrayDecl(self, node: ArrayDecl):
        for i, c in node.children():
            self.visit(c)

    def visit_InnerArrayRef(self, node, list):
        if isinstance(node.post_expr, ArrayRef):
            self.visit_InnerArrayRef(node.post_expr, list[0])
        else:
            nt = self.new_temp()
            self.code.append(('literal_int', len(list), nt))
            nt2 = self.new_temp()
            self.code.append(('load_int', node.lookup_envs(node.expr.name)['location'], nt2))
            nt3 = self.new_temp()
            self.code.append(('mul_int', nt, nt2, nt3))
            node.gen_location = nt3

    def visit_ArrayRef(self, node: ArrayRef):
        if isinstance(node.post_expr, ArrayRef):
            self.visit_InnerArrayRef(node, node.node_info['params'])

        if node.expr:
            self.visit(node.expr)

        if isinstance(node.post_expr, ArrayRef):
            target = self.new_temp()
            self.code.append(('add_int', node.post_expr.gen_location, node.expr.gen_location, target))
            node.expr.gen_location = target

        target = self.new_temp()
        post_ex = node.post_expr
        while not isinstance(post_ex, ID):
            post_ex = post_ex.post_expr
        source = node.lookup_envs(post_ex.name)['location']
        self.code.append(('elem_%s' % node.node_info['type'], source, node.expr.gen_location, target))
        node.gen_location = target

    def visit_Assert(self, node: Assert):
        for i, c in node.children():
            self.visit(c)

        target_true = self.new_temp()
        target_false = self.new_temp()
        target_end = self.new_temp()

        self.code.append(('cbranch', node.expr.gen_location, target_true, target_false))
        self.code.append((target_true[1:],))
        self.code.append(('jump', target_end))
        self.code.append((target_false[1:],))
        self.code.append(('print_string', '@.str.%d' % node.error_str))
        self.code.append(('jump', '%1'))
        self.code.append((target_end[1:],))

    def visit_Break(self, node: Break):
        for i, c in node.children():
            self.visit(c)

    def visit_Cast(self, node: Cast):
        for i, c in node.children():
            self.visit(c)

        var_target = node.expr.gen_location
        target = self.new_temp()

        if node.type.name[0] == 'float':
            self.code.append(('sitofp', var_target, target))
        elif node.type.name[0] == 'int':
            self.code.append(('fptosi', var_target, target))

        node.gen_location = target

    def visit_Compound(self, node: Compound):
        for i, c in node.children():
            self.visit(c)

        pass

    def visit_Constant(self, node: Constant):
        for i, c in node.children():
            self.visit(c)

        # Create a new temporary variable name
        target = self.new_temp()

        # Make the SSA opcode and append to list of generated instructions
        inst = ('literal_' + node.type, node.value, target)
        self.code.append(inst)

        # Save the name of the temporary variable where the value was placed
        node.gen_location = target

    def visit_DeclList(self, node: DeclList):
        for i, c in node.children():
            self.visit(c)

    def array_get_dim(self, l, default=None):
        if not l:
            return [default]
        if len(l) > 0 and type(l[0]) == list:
            return [len(l)] + self.array_get_dim(l[0], None)
        return [len(l)]

    def visit_Decl(self, node: Decl):
        if isinstance(node.decl, ArrayDecl):
            target = self.new_temp()
            self.code.append(('alloc_%s_%s' % (
                node.type.name[0], '_'.join([str(x) for x in self.array_get_dim(node.node_info['params'], default=node.node_info['length'])])), target))
            node.lookup_envs(node.name.name)['location'] = target

            if node.init:
                self.code.append(('store_%s_%s' % (
                    node.type.name[0], '_'.join([str(x) for x in self.array_get_dim(node.node_info['params'])])),
                                  '@.str.%d' % node.decl.node_info['index'], target))
            return

        if isinstance(node.decl, VarDecl):
            if node.node_info['type'] == StringType:
                return

            if node.node_info['type'] == CharType and node.node_info['array']:
                return

            if not node.gen_location:
                target = self.new_temp()
                self.code.append(('alloc_%s' % node.node_info['type'], target))
                node.gen_location = target
                node.lookup_envs(node.decl.name.name)['location'] = target

        if isinstance(node.decl, PtrDecl):
            target = self.new_temp()
            self.code.append(('alloc_%s_*' % node.type.name[0], target))
            node.lookup_envs(node.name.name)['location'] = target

        for i, c in node.children():
            self.visit(c)

        if node.init:
            self.code.append(('store_%s' % node.node_info['type'], node.init.gen_location, node.gen_location))

    def visit_EmptyStatement(self, node: EmptyStatement):
        for i, c in node.children():
            self.visit(c)

    def visit_ExprList(self, node: ExprList):
        children = []
        for i, c in node.children():
            self.visit(c)
            children.append(c)

        node.node_info = children[-1].node_info
        node.gen_location = children[-1].gen_location

    def visit_For(self, node: For):
        begin_loop = self.new_temp()
        begin_statement = self.new_temp()
        end_loop = self.new_temp()

        if node.p1:
            self.visit(node.p1)

        self.code.append((begin_loop[1:],))
        self.visit(node.p2)
        self.code.append(('cbranch', node.p2.gen_location, begin_statement, end_loop))
        self.code.append((begin_statement[1:],))
        if node.statement:
            self.visit(node.statement)
        if node.p3:
            self.visit(node.p3)
        self.code.append(('jump', begin_loop))
        self.code.append((end_loop[1:],))

    def visit_FuncCall(self, node: FuncCall):
        self.visit(node.expr1)

        if isinstance(node.expr2, ExprList):
            visit = node.expr2.list
        else:
            visit = [node.expr2]

        for a, i in enumerate(visit):
            if isinstance(i, ArrayRef):
                self.visit(i)
                target = self.new_temp()
                self.code.append(('load_%s_*' % i.node_info['type'], i.gen_location, target))
                self.code.append(('param_%s' % i.node_info['type'], target))
                pass

            elif isinstance(i, ID):
                self.visit(i)
                self.code.append(('param_%s' % i.node_info['type'], i.gen_location))

            elif isinstance(i, Constant):
                if i.type != 'string':
                    self.visit(i)
                    self.code.append(('param_%s' % i.type, i.gen_location))
                else:
                    self.code.append(('param_string', '@.str.%d' % i.node_info['index']))

            else:
                self.visit(i)
                self.code.append(('param_%s' % i.node_info['type'], i.gen_location))



        # if node.expr2:
        #     # para 1 parametro
        #     if not isinstance(node.expr2, ExprList):
        #         node_info = node.expr2.lookup_envs(node.expr2.name)
        #         inst = ('param_%s' % node_info['type'].typename, node.expr2.gen_location)
        #         self.code.append(inst)
        #     # para +1 parametro
        #     else:
        #         for child in node.expr2.list:
        #             node_info = child.lookup_envs(child.name)
        #             target = self.new_temp()
        #             inst = inst = ('param_%s' % node_info['type'].typename, child.gen_location)
        #             self.code.append(inst)

        target = self.new_temp()
        inst = inst = ('call', '@%s' % node.expr1.name, target)
        self.code.append(inst)
        node.gen_location = target

    def visit_FuncDecl(self, node: FuncDecl):
        for i, c in node.children():
            self.visit(c)

    def visit_FuncDef(self, node: FuncDef):
        self.fname = node.decl.name.name

        self.code.append(('define', '@%s' % node.decl.name.name))

        params = []

        for i in node.node_info['params']:
            params.append(self.new_temp())

        if node.node_info['type'] != VoidType:
            ret = self.new_temp()
        else:
            ret = None
        node.ret_target = ret

        vars = []
        if node.decl.decl.init:
            for i in node.decl.decl.init.list:
                target = self.new_temp()
                vars.append(target)
                self.code.append(('alloc_%s' % i.decl.type.name[0], target))
                i.gen_location = target
                node.lookup_envs(i.name.name)['location'] = target

        for a, b, c in zip(params, vars, node.node_info['params']):
            self.code.append(('store_%s' % c, a, b))

        if node.decl.name.name == 'main':
            node.end_jump = self.new_temp()
            while int(node.end_jump[1:]) < 1:
                node.end_jump = self.new_temp()
        else:
            node.end_jump = self.new_temp()

        for i, c in node.children():
            self.visit(c)

        final_ret = self.new_temp()

        self.code.append((node.end_jump[1:],))
        if node.type.name[0] != 'void':
            self.code.append(('load_%s' % node.type.name[0], ret, final_ret))
            self.code.append(('return_%s' % node.type.name[0], final_ret))
        else:
            self.code.append(('return_%s' % node.type.name[0],))

    def visit_GlobalDecl(self, node: GlobalDecl):
        # for i, c in node.children():
        #     self.visit(c)
        pass

    def visit_If(self, node: If):
        # for i, c in node.children():
        #     self.visit(c)

        begin_if = self.new_temp()
        end_if = self.new_temp()
        end_elze = self.new_temp()

        if node.expr:
            self.visit(node.expr)

        self.code.append(('cbranch', node.expr.gen_location, begin_if, end_if))
        if node.then:
            self.code.append((begin_if[1:],))
            self.visit(node.then)

        if node.elze:
            self.code.append(('jump', end_elze))

        self.code.append((end_if[1:],))

        if node.elze:
            self.visit(node.elze)
            self.code.append((end_elze[1:],))

    def visit_ID(self, node: ID):
        node_info = node.lookup_envs(node.name)
        if not node.node_info['func']:
            target = self.new_temp()
            inst = ('load_%s' % node_info['type'].typename, node_info['location'], target)
            self.code.append(inst)
            node.gen_location = target

    def visit_InitList(self, node: InitList):
        for i, c in node.children():
            self.visit(c)

    def visit_ParamList(self, node: ParamList):
        for i, c in node.children():
            self.visit(c)

    def visit_Print(self, node: Print):
        if isinstance(node.expr, ExprList):
            visit = node.expr.list
        else:
            visit = [node.expr]

        for a, i in enumerate(visit):
            if isinstance(i, ArrayRef):
                self.visit(i)
                target = self.new_temp()
                self.code.append(('load_%s_*' % i.node_info['type'], i.gen_location, target))
                self.code.append(('print_%s' % i.node_info['type'], target))
                pass

            elif isinstance(i, ID):
                self.visit(i)
                self.code.append(('print_%s' % i.node_info['type'], i.gen_location))

            elif isinstance(i, Constant):
                if i.type != 'string':
                    self.visit(i)
                    self.code.append(('print_%s' % i.type, i.gen_location))
                else:
                    self.code.append(('print_string', '@.str.%d' % i.node_info['index']))

            else:
                self.visit(i)
                self.code.append(('print_%s' % i.node_info['type'], i.gen_location))


    def visit_PtrDecl(self, node: PtrDecl):
        for i, c in node.children():
            self.visit(c)

    def visit_Read(self, node: Read):
        if isinstance(node.expr, ExprList):
            visit = node.expr.list
        else:
            visit = [node.expr]

        for a, i in enumerate(visit):
            if isinstance(i, ArrayRef):
                self.visit(i)
                target = self.new_temp()
                self.code.append(('read_%s' % i.node_info['type'], target))
                self.code.append(('store_%s_*' % i.node_info['type'], target, i.gen_location))
            elif isinstance(i, ID):
                target = self.new_temp()
                self.code.append(('read_%s' % i.node_info['type'], target))
                self.code.append(('store_%s' % i.node_info['type'], target, node.lookup_envs(i.name)['location']))

    def visit_Return(self, node: Return):
        for i, c in node.children():
            self.visit(c)

        if node.value:
            self.code.append(('store_%s' % node.node_info['type'], node.value.gen_location, node.func_def.ret_target))

        self.code.append(('jump', node.func_def.end_jump))

    def visit_Type(self, node: Type):
        for i, c in node.children():
            self.visit(c)

    def visit_VarDecl(self, node: VarDecl):
        for i, c in node.children():
            self.visit(c)

    def visit_While(self, node: While):

        begin_loop = self.new_temp()
        begin_statement = self.new_temp()
        end_loop = self.new_temp()

        self.code.append((begin_loop[1:],))
        self.visit(node.expr)
        self.code.append(('cbranch', node.expr.gen_location, begin_statement, end_loop))
        self.code.append((begin_statement[1:],))
        if node.statement:
            self.visit(node.statement)
        self.code.append(('jump', begin_loop))
        self.code.append((end_loop[1:],))






