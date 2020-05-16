from objects import Program, BinaryOp, Assignment, ArrayDecl, ArrayRef, Assert, Break, Cast, Compound, Constant, \
    DeclList, Decl, EmptyStatement, ExprList, For, FuncCall, FuncDecl, FuncDef, GlobalDecl, If, ID, InitList, ParamList, \
    Print, PtrDecl, Read, Return, Type, UnaryOp, VarDecl, While
from uc_sema import NodeVisitor, StringType, CharType, VoidType


class GenerateCode(NodeVisitor):
    # rel_opcodes = {
    #     '==': 'eq',
    #     '!=': 'ne',
    #     '>': 'gt',
    #     '<': 'lt',
    #     '>=': 'ge',
    #     '<=': 'le',
    # }

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

    # assing_opcodes = {
    #     '+=': 'add',
    #     '-=': 'sub',
    #     '*=': 'mul',
    #     '/=': 'div',
    #     '%=': 'mod',
    # }

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

        # {'--', '++', 'p--', 'p++', *, &}

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
            self.visit(node.assign_expr)

        if isinstance(node.name, ArrayRef):
            index = node.lookup_envs(node.name.expr.name)['location']
            nt = self.new_temp()
            self.code.append(('load_int', index, nt))
            source = node.lookup_envs(node.name.post_expr.name)
            nt2 = self.new_temp()
            self.code.append(('elem_%s' % source['type'], nt, nt2))
            left_target = nt2
        else:
            left_target = node.lookup_envs(node.name.name)['location']

        right_target = node.assign_expr.gen_location

        if node.op == '+=':
            pass

        if node.op == '-=':
            pass

        if node.op == '*=':
            pass

        if node.op == '/=':
            pass

        if node.op == '*=':
            pass

        self.code.append(('store_%s' % node.name.node_info['type'], right_target, left_target))

    def visit_ArrayDecl(self, node: ArrayDecl):
        for i, c in node.children():
            self.visit(c)

    def visit_ArrayRef(self, node: ArrayRef):
        for i, c in node.children():
            self.visit(c)

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

    def visit_Decl(self, node: Decl):
        if isinstance(node.decl, ArrayDecl):
            if not node.init:
                target = self.new_temp()
                self.code.append(('alloc_%s_%d' % (node.type.name[0], node.node_info['length']), target))
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
            self.code.append(('alloc_%s%s' % (node.type.name[0], ''.join(['_*' for _ in range(node.decl.node_info['depth'])])), target))

        for i, c in node.children():
            self.visit(c)

        if node.init:
            self.code.append(('store_%s' % node.node_info['type'], node.init.gen_location, node.gen_location))

    def visit_EmptyStatement(self, node: EmptyStatement):
        for i, c in node.children():
            self.visit(c)

    def visit_ExprList(self, node: ExprList):
        for i, c in node.children():
            self.visit(c)

    def visit_For(self, node: For):
        for i, c in node.children():
            self.visit(c)

    def visit_FuncCall(self, node: FuncCall):

        for i, c in node.children():
            self.visit(c)

        # para 1 parametro
        if isinstance(node.expr2, ID):
            node_info = node.expr2.lookup_envs(node.expr2.name)
            inst = ('param_%s' % node_info['type'].typename, node.expr2.gen_location)
            self.code.append(inst)
        # para +1 parametro
        if isinstance(node.expr2, ExprList):
            for child in node.expr2.list:
                node_info = child.lookup_envs(child.name)
                target = self.new_temp()
                inst = inst = ('param_%s' % node_info['type'].typename, child.gen_location)
                self.code.append(inst)

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
            node.end_jump = '%1'
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
        for i, c in node.children():
            self.visit(c)

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
        for i, c in node.children():
            self.visit(c)

        if isinstance(node.expr, ID):
            node_info = node.expr.lookup_envs(node.expr.name)
            inst = ('print_%s' % node_info['type'].typename, node.expr.gen_location)
            self.code.append(inst)
        elif not isinstance(node.expr, ExprList):
            inst = ('print_%s' % node.expr.node_info['type'], node.expr.gen_location)
            self.code.append(inst)

        else :
            for child in node.expr.list:
                if isinstance(node.expr, ID):
                    node_info = child.lookup_envs(child.name)
                    inst = ('print_%s' % node_info['type'].typename, child.gen_location)
                    self.code.append(inst)
                else:
                    inst = ('print_%s' % child.node_info['type'], child.gen_location)
                    self.code.append(inst)



    def visit_PtrDecl(self, node: PtrDecl):
        for i, c in node.children():
            self.visit(c)

    def visit_Read(self, node: Read):
        for i, c in node.children():
            self.visit(c)

        if isinstance(node.expr, ID):
            node_info = node.expr.lookup_envs(node.expr.name)
            inst = ('read_%s' % node_info['type'].typename, node.expr.gen_location)
            self.code.append(inst)

        if isinstance(node.expr, ExprList):
            for child in node.expr.list:
                node_info = child.lookup_envs(child.name)
                inst = ('read_%s' % node_info['type'].typename, child.gen_location)
                self.code.append(inst)

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
        for i, c in node.children():
            self.visit(c)
