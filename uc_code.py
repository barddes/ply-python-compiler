import operator
import re

from graphviz import Digraph

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
        self._next_block = None  # Link to the next block
        self.nodes = []
        self.prev_block = None
        self.visited = False

        self.code_obj = []

        # Reaching Definitions
        self.rd_in = set()
        self.rd_out = set()
        self.rd_gen = set()
        self.rd_kill = set()

        # Liveness analisys
        self.la_use = set()
        self.la_def = set()
        self.la_in = set()
        self.la_out = set()


    def append(self, instr):
        self.instructions.append(instr)

    def __iter__(self):
        return iter(self.instructions)

    @property
    def next_block(self):
        return self._next_block

    @next_block.setter
    def next_block(self, block):
        self._next_block = block
        if block:
            block.prev_block = self


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

def format_instruction(t):
    # Auxiliary method to pretty print the instructions
    op = t[0]
    if len(t) > 1:
        if op == "define":
            return f"\n{op} {t[1]}"
        else:
            _str = "" if op.startswith('global') else "  "
            if op == 'jump':
                _str += f"{op} label {t[1]}"
            elif op == 'cbranch':
                _str += f"{op} {t[1]} label {t[2]} label {t[3]}"
            elif op == 'global_string':
                _str += f"{op} {t[1]} \'{t[2]}\'"
            elif op.startswith('return'):
                _str += f"{op} {t[1]}"
            else:
                for _el in t:
                    _str += f"{_el} "
            return _str
    elif op == 'print_void' or op == 'return_void':
        return f"  {op}"
    else:
        return f"{op}"

class CFG(object):

    def __init__(self, fname):
        self.fname = fname
        self.g = Digraph('g', filename=fname + '.gv', node_attr={'shape': 'record'})

    def visit_BasicBlock(self, block):
        # Get the label as node name
        _name = block.label
        if _name:
            # get the formatted instructions as node label
            _label = "{" + _name + ":\l\t"
            for _inst in block.instructions[1:]:
                _label += format_instruction(_inst) + "\l\t"
            #
            # for _inst in block.code_obj[1:]:
            #     _label += ('%d: ' % _inst['label']) + format_instruction(_inst['inst']) + '\l\t'

            # _label += 'RD:\l\t'
            # _label += 'GEN ' + str(block.rd_gen).replace('{', '').replace('}', '') + '\l\t'
            # _label += 'KILL ' + str(block.rd_kill).replace('{', '').replace('}', '') + '\l\t'
            # _label += 'IN   ' + str(block.rd_in).replace('{', '').replace('}', '') + '\l\t'
            # _label += 'OUT  ' + str(block.rd_out).replace('{', '').replace('}', '') + '\l\t'
            #
            # _label += 'LA:\l\t'
            # _label += 'USE  ' + str(block.la_use).replace('{', '').replace('}', '') + '\l\t'
            # _label += 'DEF  ' + str(block.la_def).replace('{', '').replace('}', '') + '\l\t'
            # _label += 'IN   ' + str(block.la_in).replace('{', '').replace('}', '') + '\l\t'
            # _label += 'OUT  ' + str(block.la_out).replace('{', '').replace('}', '') + '\l\t'

            # _label += "\l\t"
            # for _pred in block.predecessors:
            #     _label += "pred %s \l\t" % _pred.label
            _label += "}"
            self.g.node(_name, label=_label)
            if block.branch:
                self.g.edge(_name, block.branch.label)
        else:
            # Function definition. An empty block that connect to the Entry Block
            self.g.node(self.fname, label=None, _attributes={'shape': 'ellipse'})
            self.g.edge(self.fname, block.next_block.label)

    def visit_ConditionBlock(self, block):
        # Get the label as node name
        _name = block.label
        # get the formatted instructions as node label
        _label = "{" + _name + ":\l\t"
        for _inst in block.instructions[1:]:
            _label += format_instruction(_inst) + "\l\t"

        # for _inst in block.code_obj[1:]:
        #     _label += ('%d: ' % _inst['label']) + format_instruction(_inst['inst']) + '\l\t'

        # _label += 'RD:\l\t'
        # _label += 'GEN ' + str(block.rd_gen).replace('{', '').replace('}', '') + '\l\t'
        # _label += 'KILL ' + str(block.rd_kill).replace('{', '').replace('}', '') + '\l\t'
        # _label += 'IN   ' + str(block.rd_in).replace('{', '').replace('}', '') + '\l\t'
        # _label += 'OUT  ' + str(block.rd_out).replace('{', '').replace('}', '') + '\l\t'
        #
        # _label += 'LA:\l\t'
        # _label += 'USE  ' + str(block.la_use).replace('{', '').replace('}', '') + '\l\t'
        # _label += 'DEF  ' + str(block.la_def).replace('{', '').replace('}', '') + '\l\t'
        # _label += 'IN   ' + str(block.la_in).replace('{', '').replace('}', '') + '\l\t'
        # _label += 'OUT  ' + str(block.la_out).replace('{', '').replace('}', '') + '\l\t'
        # _label += "\l\t"
        # for _pred in block.predecessors:
        #     _label += "pred %s \l\t" % _pred.label
        _label +="|{<f0>T|<f1>F}}"
        self.g.node(_name, label=_label)
        self.g.edge(_name + ":f0", block.taken.label)
        self.g.edge(_name + ":f1", block.fall_through.label)

    def view(self, block):
        while isinstance(block, Block):
            name = "visit_%s" % type(block).__name__
            if hasattr(self, name):
                getattr(self, name)(block)
            block = block.next_block
        # You can use the next stmt to see the dot file
        # print(self.g.source)
        try:
            self.g.view()
        except:
            pass


class CodeGenerator(NodeVisitor):
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

    labels = {}

    def show(self, buf=None):
        for d in self.dot:
            d.view()

    def make_label(self, name):
        value = self.labels.get(name, 0)
        self.labels[name] = value + 1

        if value == 0:
            return '%%%s' % name
        else:
            return '%%%s.%d' % (name, value)

    '''
    Node visitor class that creates 3-address encoded instruction sequences.
    '''

    def __init__(self, cfg=None):
        self.current_block = None
        self.ret_block = None
        self.loop_stack = []
        self.global_vars = set()
        self.code_obj = []
        self.global_code_obj = []
        self.dot = []

        super(GenerateCode, self).__init__()

        # version dictionary for temporaries
        self.fname = 'main'  # We use the function name as a key
        self.versions = {self.fname: 0}

        # The generated code (list of tuples)
        self.code = []
        self.label = 0

    def new_temp(self):
        '''
        Create a new temporary variable of a given scope (function name).
        '''
        if self.fname not in self.versions:
            self.versions[self.fname] = 0
        name = "%" + "%d" % (self.versions[self.fname])
        self.versions[self.fname] += 1

        return name

    def changeBlockToBasic(self, block, result):
        new_block = BasicBlock(block.label)
        new_block.instructions = block.instructions
        new_block.predecessors = block.predecessors
        new_block.next_block = block.next_block

        if result:
            new_block.branch = block.taken
        else:
            new_block.branch = block.fall_through

        if block.prev_block:
            block.prev_block.next_block = new_block

        for pred in block.predecessors:
            if isinstance(pred, BasicBlock):
                pred.branch = new_block
            else:
                if pred.taken == block:
                    pred.taken = new_block
                else:
                    pred.fall_through = new_block

            if pred.next_block == block:
                pred.next_block = new_block

        for node in block.nodes:
            node.cfg = new_block

        return new_block

    def changeCurrentBlock(self):
        current_block = self.current_block
        new_block = ConditionBlock(current_block.label)
        new_block.instructions = current_block.instructions
        new_block.predecessors = current_block.predecessors
        new_block.next_block = current_block.next_block

        if current_block.prev_block:
            current_block.prev_block.next_block = new_block

        for b in current_block.predecessors:
            if isinstance(b, BasicBlock):
                b.branch = new_block
            else:
                if b.taken == current_block:
                    b.taken = new_block
                else:
                    b.fall_through = new_block

            if b.next_block == current_block:
                b.next_block = new_block

        for n in current_block.nodes:
            n.cfg = new_block
        self.current_block = new_block

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
        self.current_block.append(inst)

        # Save the name of the temporary variable where the value was placed
        node.gen_location = target

    def visit_BinaryOp(self, node: BinaryOp):
        # Visit the left and right expressions
        self.visit(node.expr1)
        self.visit(node.expr2)

        if isinstance(node.expr1, ArrayRef):
            nt = self.new_temp()
            self.current_block.append(('load_%s_*' % node.expr1.node_info['type'], node.expr1.gen_location, nt))
            node.expr1.gen_location = nt

        if isinstance(node.expr2, ArrayRef):
            nt = self.new_temp()
            self.current_block.append(('load_%s_*' % node.expr2.node_info['type'], node.expr2.gen_location, nt))
            node.expr2.gen_location = nt

        target = self.new_temp()

        # Create the opcode and append to list
        opcode = self.binary_ops[node.op] + "_" + node.expr1.node_info['type'].typename
        inst = (opcode, node.expr1.gen_location, node.expr2.gen_location, target)
        self.current_block.append(inst)

        # Store location of the result on the node
        node.gen_location = target

    def visit_VarDeclaration(self, node):
        # allocate on stack memory
        inst = ('alloc_' + node.type.name, node.id)
        self.current_block.append(inst)
        # store optional init val
        if node.value:
            self.visit(node.value)
            inst = ('store_' + node.type.name, node.value.gen_location, node.id)
            self.current_block.append(inst)

    def visit_LoadLocation(self, node):
        target = self.new_temp()
        inst = ('load_' + node.type.name, node.name, target)
        self.current_block.append(inst)
        node.gen_location = target

    def visit_AssignmentStatement(self, node):
        self.visit(node.value)
        inst = ('store_' + node.value.type.name, node.value.gen_location, node.location)
        self.current_block.append(inst)

    def visit_UnaryOp(self, node: UnaryOp):
        self.visit(node.expr1)

        node_t = node.expr1.node_info['type'].typename

        if node.op == '&':
            if node.assign_left:
                nt = node.lookup_envs(node.assign_left.name.name)['location']
            else:
                nt = self.new_temp()
            self.current_block.append(('get_%s_*' % node_t, node.expr1.gen_location, nt))
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
            self.current_block.append(('literal_%s' % node_t, 0, nt))
            nt2 = self.new_temp()
            self.current_block.append(('sub_%s' % node_t, nt, node.expr1.gen_location, nt2))
            node.gen_location = nt2
            return

        if node.op in ('--', '++'):
            op = 'add' if node.op == '++' else 'sub'
            nt = self.new_temp()
            self.current_block.append(('literal_%s' % node_t, 1, nt))
            nt2 = self.new_temp()
            self.current_block.append(('%s_%s' % (op, node_t), node.expr1.gen_location, nt, nt2))
            var_loc = node.lookup_envs(node.expr1.name)['location']
            self.current_block.append(('store_%s' % node_t, nt2, var_loc))
            node.gen_location = nt2

        if node.op in ('p--', 'p++'):
            op = 'add' if node.op[1:] == '++' else 'sub'
            nt = self.new_temp()
            self.current_block.append(('literal_%s' % node_t, 1, nt))
            nt2 = self.new_temp()
            self.current_block.append(('%s_%s' % (op, node_t), node.expr1.gen_location, nt, nt2))
            var_loc = node.lookup_envs(node.expr1.name)['location']
            self.current_block.append(('store_%s' % node_t, nt2, var_loc))
            node.gen_location = node.expr1.gen_location

        if node.op == '!':
            nt = self.new_temp()
            self.current_block.append(('not_%s' % node_t, node.expr1.gen_location, nt))
            node.gen_location = nt
            return

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
                    inst = ('global_%s_%s' % (var.decl.type.name[0], '_'.join([str(x) for x in self.array_get_dim(node.env.unbox_InitList(var.init.list))])), '@%s' % var.decl.name.name, node.env.unbox_InitList(var.init.list))
                    if node.env.unbox_InitList(var.init.list) in node.global_env.consts:
                        idx = node.global_env.consts.index(node.env.unbox_InitList(var.init.list))
                        node.global_env.consts[idx] = None
                else:
                    inst = ('global_%s' % var.decl.type.name[0], '@%s' % var.decl.name.name, var.init.value)
            else:
                inst = ('global_%s' % var.decl.type.name[0], '@%s' % var.decl.name.name)

            self.global_code_obj.append({
                    'label': self.make_label_instructions(),
                    'inst': inst,
                    'def': set(),
                    'use': set(),
                    'alive': True
                })
            var.gen_location = '@%s' % var.decl.name.name
            node.lookup_envs(var.decl.name.name)['location'] = '@%s' % var.decl.name.name

        for i, const in enumerate(node.global_env.consts):
            if not const:
                continue
            if type(const) == list:
                inst = ('global_%s' % self.get_const_type(const) + self.get_const_dim(const), '@.str.%d' % i, const)
            else:
                inst = ('global_string', '@.str.%d' % i, const)
            self.global_code_obj.append({
                'label': self.make_label_instructions(),
                'inst': inst,
                'def': set(),
                'use': set(),
                'alive': True
            })

        for i, d in node.children():
            self.visit(d)

        for e in node.global_env.symtable:
            if node.global_env.symtable[e].get('global', None):
                self.global_vars |= {'@%s' % e}

        self.code = [inst['inst'] for inst in self.global_code_obj]

        for _decl in node.decl_list:
            if isinstance(_decl, FuncDef):
                cfg = _decl.cfg
                # self.instruction_analisys(cfg)
                # self.reaching_definitions(cfg)
                # self.copy_propagation(cfg)
                #
                # self.instruction_analisys(cfg)
                # self.reaching_definitions(cfg)
                # self.constant_folding(cfg)
                #
                # self.instruction_analisys(cfg)
                # self.reaching_definitions(cfg)
                # self.branch_folding(cfg)
                #
                # self.instruction_analisys(cfg)
                # self.liveness_analisys(cfg)
                # self.deadcode_elimination(cfg)
                # self.block_removal(cfg)
                # self.merge_basic_blocks(cfg)

                self.instruction_analisys(cfg)

                self.code += [inst['inst'] for inst in self.code_obj]

        for _decl in node.decl_list:
            if isinstance(_decl, FuncDef):
                dot = CFG(_decl.decl.name.name)
                # dot.view(_decl.cfg)  # _decl.cfg contains the CFG for the function

    def visit_Assignment(self, node: Assignment):
        if node.assign_expr:
            node.assign_expr.assign_left = node
            self.visit(node.assign_expr)

            if isinstance(node.assign_expr, ArrayRef):
                nt = self.new_temp()
                self.current_block.append(('load_%s_*' % node.assign_expr.node_info['type'], node.assign_expr.gen_location, nt))
                node.assign_expr.gen_location= nt

        if isinstance(node.name, ArrayRef):
            self.visit(node.name)
            left_target = node.name.gen_location
            # index = node.name.expr.gen_location
            # nt = self.new_temp()
            # self.current_block.append(('load_int', index, nt))
            # source = node.lookup_envs(node.name.post_expr.name)
            # nt2 = self.new_temp()
            # self.current_block.append(('elem_%s' % source['type'], source['location'], nt, nt2))
            # left_target = nt2
        else:
            left_target = node.lookup_envs(node.name.name)['location']


        right_target = node.assign_expr.gen_location

        if node.op == '=':
            if not isinstance(node.assign_expr, UnaryOp) or node.assign_expr.op != '&':
                if isinstance(node.name, ArrayRef):
                    self.current_block.append(('store_%s_*' % node.assign_expr.node_info['type'], node.assign_expr.gen_location, left_target))
                else:
                    self.current_block.append(('store_%s' % node.name.node_info['type'].typename, right_target, left_target))

        if node.op in ('+=', '-=', '*=', '/=', '%/'):
            nt = self.new_temp()
            op = {
                '+=': 'add',
                '-=': 'sub',
                '*=': 'mul',
                '/=': 'div',
                '%=': 'mod'
            }[node.op]
            self.current_block.append(('load_%s' % node.name.node_info['type'], left_target, nt))
            nt2 = self.new_temp()
            self.current_block.append(('%s_%s' % (op, node.name.node_info['type']), nt, node.assign_expr.gen_location, nt2))
            self.current_block.append(('store_%s' % node.name.node_info['type'], nt2, left_target))

    def visit_ArrayDecl(self, node: ArrayDecl):
        for i, c in node.children():
            self.visit(c)

    def visit_InnerArrayRef(self, node, list):
        if isinstance(node.post_expr, ArrayRef):
            self.visit_InnerArrayRef(node.post_expr, list[0])
        else:
            nt = self.new_temp()
            self.current_block.append(('literal_int', len(list), nt))
            nt2 = self.new_temp()
            self.current_block.append(('load_int', node.lookup_envs(node.expr.name)['location'], nt2))
            nt3 = self.new_temp()
            self.current_block.append(('mul_int', nt, nt2, nt3))
            node.gen_location = nt3

    def visit_ArrayRef(self, node: ArrayRef):
        if isinstance(node.post_expr, ArrayRef):
            self.visit_InnerArrayRef(node, node.node_info['params'])

        if node.expr:
            self.visit(node.expr)

        if isinstance(node.post_expr, ArrayRef):
            target = self.new_temp()
            self.current_block.append(('add_int', node.post_expr.gen_location, node.expr.gen_location, target))
            node.expr.gen_location = target

        target = self.new_temp()
        post_ex = node.post_expr
        while not isinstance(post_ex, ID):
            post_ex = post_ex.post_expr
        source = node.lookup_envs(post_ex.name)['location']
        self.current_block.append(('elem_%s' % node.node_info['type'], source, node.expr.gen_location, target))
        node.gen_location = target

    def visit_Assert(self, node: Assert):
        self.changeCurrentBlock()

        target_false = self.make_label('assert.false')
        target_end = self.make_label('assert.true')

        current_block = self.current_block
        false_block = BasicBlock(target_false)
        true_block = BasicBlock(target_end)

        current_block.next_block = false_block
        false_block.next_block = true_block

        self.visit(node.expr)
        self.current_block.append(('cbranch', node.expr.gen_location, target_end, target_false))
        self.current_block.taken = true_block
        self.current_block.fall_through = false_block
        true_block.predecessors.append(self.current_block)
        false_block.predecessors.append(self.current_block)

        self.current_block = false_block
        self.current_block.append((str(target_false[1:]) + ':',))
        self.current_block.append(('print_string', '@.str.%d' % node.error_str))
        self.current_block.append(('jump', self.ret_block.label))
        self.current_block.branch = self.ret_block
        self.ret_block.predecessors.append(self.current_block)

        self.current_block = true_block
        self.current_block.append((str(target_end[1:]) + ':',))

    def visit_Break(self, node: Break):
        self.current_block.append(('jump', self.loop_stack[-1].label))
        self.current_block.branch = self.loop_stack[-1]
        self.loop_stack[-1].predecessors.append(self.current_block)

    def visit_Cast(self, node: Cast):
        for i, c in node.children():
            self.visit(c)

        var_target = node.expr.gen_location
        target = self.new_temp()

        if node.type.name[0] == 'float':
            self.current_block.append(('sitofp', var_target, target))
        elif node.type.name[0] == 'int':
            self.current_block.append(('fptosi', var_target, target))

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
        self.current_block.append(inst)

        # Save the name of the temporary variable where the value was placed
        node.gen_location = target

    def visit_DeclList(self, node: DeclList):
        for ix, c in node.children():
            self.visit(c)

    def array_get_dim(self, l, default=None):
        if not l:
            return [default]
        if len(l) > 0 and type(l[0]) == list:
            return [len(l)] + self.array_get_dim(l[0], None)
        return [len(l)]

    def visit_Decl(self, node: Decl):
        if isinstance(node.decl, ArrayDecl):
            target = self.make_label(node.name.name)
            self.current_block.append(('alloc_%s_%s' % (
                node.type.name[0], '_'.join([str(x) for x in self.array_get_dim(node.node_info['params'], default=node.node_info['length'])])), target))
            node.lookup_envs(node.name.name)['location'] = target

            if node.init:
                self.current_block.append(('store_%s_%s' % (
                    node.type.name[0], '_'.join([str(x) for x in self.array_get_dim(node.node_info['params'])])),
                                  '@.str.%d' % node.decl.node_info['index'], target))
            return

        if isinstance(node.decl, VarDecl):
            if node.node_info['type'] == StringType:
                return

            if node.node_info['type'] == CharType and node.node_info['array']:
                return

            if not node.gen_location:
                target = self.make_label(node.name.name)
                self.current_block.append(('alloc_%s' % node.node_info['type'], target))
                node.gen_location = target
                node.lookup_envs(node.decl.name.name)['location'] = target

        if isinstance(node.decl, PtrDecl):
            target = self.make_label(node.name.name)
            self.current_block.append(('alloc_%s_*' % node.type.name[0], target))
            node.lookup_envs(node.name.name)['location'] = target

        for i, c in node.children():
            self.visit(c)

        if node.init:
            self.current_block.append(('store_%s' % node.node_info['type'], node.init.gen_location, node.gen_location))

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
        cond_label = self.make_label('for.cond')
        inc_label = self.make_label('for.inc')
        body_label = self.make_label('for.body')
        end_label = self.make_label('for.end')

        condition_block = ConditionBlock(cond_label)
        inc_block = BasicBlock(inc_label)
        body_block = BasicBlock(body_label)
        end_block = BasicBlock(end_label)

        self.loop_stack.append(end_block)

        if node.p1:
            self.visit(node.p1)

        self.current_block.next_block = condition_block
        self.current_block.branch = condition_block
        condition_block.predecessors.append(self.current_block)
        self.current_block = condition_block
        self.current_block.append((str(cond_label[1:]) + ':',))
        self.visit(node.p2)
        self.current_block.append(('cbranch', node.p2.gen_location, body_label, end_label))
        self.current_block.taken = body_block
        self.current_block.fall_through = end_block

        self.current_block.next_block = body_block
        body_block.predecessors.append(self.current_block)
        self.current_block = body_block
        self.current_block.append((str(body_label[1:]) + ':',))
        if node.statement:
            self.visit(node.statement)
        self.current_block.append(('jump', inc_label))

        self.current_block.next_block = inc_block
        self.current_block.branch = inc_block
        inc_block.predecessors.append(self.current_block)
        self.current_block = inc_block
        self.current_block.append((str(inc_label[1:]) + ':',))
        if node.p3:
            self.visit(node.p3)
        self.current_block.append(('jump', cond_label))
        self.current_block.branch = condition_block
        condition_block.predecessors.append(self.current_block)

        self.current_block.next_block = end_block
        end_block.predecessors.append(condition_block)
        self.current_block = end_block
        self.current_block.append((str(end_label[1:]) + ':',))

        self.loop_stack.pop(-1)

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
                self.current_block.append(('load_%s_*' % i.node_info['type'], i.gen_location, target))
                self.current_block.append(('param_%s' % i.node_info['type'], target))
                pass

            elif isinstance(i, ID):
                self.visit(i)
                self.current_block.append(('param_%s' % i.node_info['type'], i.gen_location))

            elif isinstance(i, Constant):
                if i.type != 'string':
                    self.visit(i)
                    self.current_block.append(('param_%s' % i.type, i.gen_location))
                else:
                    self.current_block.append(('param_string', '@.str.%d' % i.node_info['index']))

            else:
                self.visit(i)
                self.current_block.append(('param_%s' % i.node_info['type'], i.gen_location))

        target = self.new_temp()
        inst = ('call', '@%s' % node.expr1.name, target)
        self.current_block.append(inst)
        node.gen_location = target

    def visit_FuncDecl(self, node: FuncDecl):
        for i, c in node.children():
            self.visit(c)

    def visit_FuncDef(self, node: FuncDef):
        self.fname = node.decl.name.name
        self.current_block = BasicBlock(None)

        node.cfg = self.current_block
        self.current_block.nodes.append(node)

        current_block = self.current_block
        entry_block = BasicBlock(self.make_label('entry'))
        current_block.branch = entry_block
        self.current_block = entry_block

        current_block.next_block = entry_block
        entry_block.predecessors.append(current_block)

        self.current_block.append(('define', '@%s' % node.decl.name.name))
        params = []
        for _ in node.node_info['params']:
            params.append(self.new_temp())

        if node.node_info['type'] != VoidType:
            ret = self.new_temp()
        else:
            ret = None
        node.ret_target = ret

        self.ret_block = BasicBlock(self.make_label('exit'))

        vars = []
        if node.decl.decl.init:
            for i in node.decl.decl.init.list:
                target = self.make_label(i.name.name)
                vars.append(target)
                self.current_block.append(('alloc_%s' % i.decl.type.name[0], target))
                i.gen_location = target
                node.lookup_envs(i.name.name)['location'] = target

        for a, b, c in zip(params, vars, node.node_info['params']):
            self.current_block.append(('store_%s' % c, a, b))

        if node.decl.name.name == 'main':
            node.end_jump = self.new_temp()
            while int(node.end_jump[1:]) < 1:
                node.end_jump = self.new_temp()
        else:
            node.end_jump = self.new_temp()

        for i, c in node.children():
            self.visit(c)

        if self.current_block.instructions[-1] != ('jump', self.ret_block.label):
            self.current_block.append(('jump', self.ret_block.label))
            self.ret_block.predecessors.append(self.current_block)

        self.current_block.next_block = self.ret_block
        self.current_block.branch = self.ret_block
        self.current_block = self.ret_block

        final_ret = self.new_temp()
        self.current_block.append((self.ret_block.label[1:] + ':',))
        if node.type.name[0] != 'void':
            self.current_block.append(('load_%s' % node.type.name[0], ret, final_ret))
            self.current_block.append(('return_%s' % node.type.name[0], final_ret))
        else:
            self.current_block.append(('return_%s' % node.type.name[0],))

    def visit_GlobalDecl(self, node: GlobalDecl):
        pass

    def visit_If(self, node: If):
        self.changeCurrentBlock()

        then_label = self.make_label('if.then')
        then_block = BasicBlock(then_label)

        else_label = self.make_label('if.else')
        if node.elze:
            else_block = BasicBlock(else_label)

        end_label = self.make_label('if.end')
        end_block = BasicBlock(end_label)

        if node.expr:
            self.visit(node.expr)

        if node.elze:
            self.current_block.append(('cbranch', node.expr.gen_location, then_label, else_label))
            self.current_block.taken = then_block
            self.current_block.fall_through = else_block

            then_block.predecessors.append(self.current_block)
            else_block.predecessors.append(self.current_block)
        else:
            self.current_block.append(('cbranch', node.expr.gen_location, then_label, end_label))
            self.current_block.taken = then_block
            self.current_block.fall_through = end_block

            then_block.predecessors.append(self.current_block)
            end_block.predecessors.append(self.current_block)


        if node.then:
            self.current_block.next_block = then_block
            self.current_block = then_block
            self.current_block.append((str(then_label[1:]) + ':',))
            self.current_block.branch = end_block
            self.visit(node.then)

            if self.current_block.instructions[-1][0] != 'jump':
                self.current_block.append(('jump', end_label))
                self.current_block.branch = end_block
                end_block.predecessors.append(self.current_block)

        if node.elze:
            self.current_block.next_block = else_block
            self.current_block = else_block
            self.current_block.append((str(else_label[1:]) + ':',))
            self.current_block.branch = end_block
            self.visit(node.elze)

            if self.current_block.instructions[-1][0] != 'jump':
                self.current_block.append(('jump', end_label))
                self.current_block.branch = end_block
                end_block.predecessors.append(self.current_block)

        self.current_block.next_block = end_block
        self.current_block = end_block
        self.current_block.append((str(end_label[1:]) + ':',))


    def visit_ID(self, node: ID):
        node_info = node.lookup_envs(node.name)
        if not node.node_info['func']:
            target = self.new_temp()
            inst = ('load_%s' % node_info['type'].typename, node_info['location'], target)
            self.current_block.append(inst)
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
                self.current_block.append(('load_%s_*' % i.node_info['type'], i.gen_location, target))
                self.current_block.append(('print_%s' % i.node_info['type'], target))
                pass

            elif isinstance(i, ID):
                self.visit(i)
                self.current_block.append(('print_%s' % i.node_info['type'], i.gen_location))

            elif isinstance(i, Constant):
                if i.type != 'string':
                    self.visit(i)
                    self.current_block.append(('print_%s' % i.type, i.gen_location))
                else:
                    self.current_block.append(('print_string', '@.str.%d' % i.node_info['index']))

            else:
                self.visit(i)
                self.current_block.append(('print_%s' % i.node_info['type'], i.gen_location))

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
                self.current_block.append(('read_%s' % i.node_info['type'], target))
                self.current_block.append(('store_%s_*' % i.node_info['type'], target, i.gen_location))
            elif isinstance(i, ID):
                target = self.new_temp()
                self.current_block.append(('read_%s' % i.node_info['type'], target))
                self.current_block.append(('store_%s' % i.node_info['type'], target, node.lookup_envs(i.name)['location']))

    def visit_Return(self, node: Return):
        if node.value:
            self.visit(node.value)
            self.current_block.append(('store_%s' % node.node_info['type'], node.value.gen_location, node.func_def.ret_target))

        self.current_block.append(('jump', self.ret_block.label))
        self.current_block.branch = self.ret_block
        self.ret_block.predecessors.append(self.current_block)

    def visit_Type(self, node: Type):
        for i, c in node.children():
            self.visit(c)

    def visit_VarDecl(self, node: VarDecl):
        for i, c in node.children():
            self.visit(c)

    def visit_While(self, node: While):
        cond_label = self.make_label('while.cond')
        body_label = self.make_label('while.body')
        end_label = self.make_label('while.end')

        condition_block = ConditionBlock(cond_label)
        body_block = BasicBlock(body_label)
        end_block = BasicBlock(end_label)

        self.loop_stack.append(end_block)

        self.current_block.next_block = condition_block
        self.current_block.branch = condition_block
        condition_block.predecessors.append(self.current_block)
        self.current_block = condition_block

        self.current_block.append((str(cond_label[1:]) + ':',))
        self.visit(node.expr)

        self.current_block.append(('cbranch', node.expr.gen_location, body_label, end_label))
        body_block.predecessors.append(self.current_block)
        end_block.predecessors.append(self.current_block)
        self.current_block.taken = body_block
        self.current_block.fall_through = end_block

        if node.statement:
            self.current_block.next_block = body_block
            self.current_block = body_block
            self.current_block.append((str(body_label[1:]) + ':',))
            self.visit(node.statement)

            self.current_block.branch = condition_block
            self.current_block.append(('jump', cond_label))
            condition_block.predecessors.append(self.current_block)

        self.current_block.next_block = end_block
        self.current_block = end_block
        self.current_block.append((str(end_label[1:]) + ':',))

        self.loop_stack.pop(-1)


    def make_label_instructions(self):
        label = self.label
        self.label = label + 1
        return label

    def instruction_analisys(self, cfg):
        self.reset_analisys(cfg)

        definition_re = re.compile(r'(load|store|literal|elem|get|add|sub|mul|div|mod|lt|le|ge|gt|eq|ne|and|or|not|read|alloc)_.*|fptosi|sitofp|call')
        label_re = re.compile(r'.*:')

        # uses_1_re = re.compile(r'(load|store|get|return|param|print)_(?!void).*|fptosi|sitofp|jump|call')
        uses_1_re = re.compile(r'(load|store|get|return|param|print|not)_(?!void).*|fptosi|sitofp|call')
        uses_2_re = re.compile(r'(elem|add|sub|mul|div|mod|lt|le|ge|gt|eq|ne|and|or)_.*')
        uses_3_re = re.compile(r'cbranch')

        block = cfg
        while isinstance(block, Block):
            for inst in block.instructions:
                obj = {
                    'label': self.make_label_instructions(),
                    'inst': inst,
                    'def': set(),
                    'use': set(),
                    'alive': True
                }

                if definition_re.match(inst[0]):
                    obj['def'] |= {inst[-1]}
                # elif label_re.match(inst[0]):
                #     obj['def'] |= {'%%%s' % inst[0][0:-1]}

                if uses_1_re.match(inst[0]):
                    obj['use'] |= {inst[1]}
                elif uses_2_re.match(inst[0]):
                    obj['use'] |= {inst[1], inst[2]}
                elif uses_3_re.match(inst[0]):
                    # obj['use'] |= {inst[1], inst[2], inst[3]}
                    obj['use'] |= {inst[1]}

                if re.match(r'store_.+_*', inst[0]):
                    obj['use'] |= obj['def']

                block.code_obj.append(obj)
                self.code_obj.append(obj)
            block = block.next_block

        self.print_analisys_table()

    def print_analisys_table(self):
        return
        table_format = '{:60} {:20} {:20} {:20} {:20}'
        print(table_format.format('Instruction', 'RD Gen', 'RD Kill', 'Def', 'Use'))
        print(table_format.format('-----------', '------', '-------', '---', '---'))

        for inst in self.code_obj:
            gen = set()
            kill = set()
            _def = set()
            use = set()

            if inst['def']:
                gen = {inst['label']}
                _def = inst['def']
                kill = {x['label'] for x in self.code_obj if x['def'] == inst['def']} - gen

            if inst['use']:
                use = inst['use']

            if not gen:
                gen = ''
            if not kill:
                kill = ''
            if not _def:
                _def = ''
            if not use:
                use = ''

            print(table_format.format('%d: %s' % (inst['label'], inst['inst']), str(gen), str(kill), str(_def), str(use)))

    def reaching_definitions(self, cfg):
        block = cfg
        nodes = []

        # Gen/Kill do bloco
        while isinstance(block, Block):
            nodes.append(block)
            for inst in block.code_obj:
                if not inst['def']:
                    continue

                gen_n = {inst['label']}
                kill_n = {x['label'] for x in self.code_obj if x['def'] == inst['def']} - gen_n

                new_gen = gen_n | (block.rd_gen - kill_n)
                new_kill = block.rd_kill | kill_n

                block.rd_gen = new_gen
                block.rd_kill = new_kill
            block = block.next_block

        # Reaching Definitions
        while len(nodes) > 0:
            node = nodes.pop(0)

            old = node.rd_out

            rd_in = set()
            for pred in node.predecessors:
                rd_in |= pred.rd_out

            node.rd_in = rd_in
            node.rd_out = node.rd_gen | (rd_in - node.rd_kill)

            if old != node.rd_out:
                if isinstance(node, ConditionBlock):
                    succ = [node.taken, node.fall_through]
                else:
                    succ = [node.branch]
                for s in succ:
                    if s and s not in nodes:
                        nodes.append(s)

    def liveness_analisys(self, cfg):
        block = cfg
        nodes = []

        # Use/Def do bloco
        while isinstance(block, Block):
            nodes.append(block)
            for inst in reversed(block.code_obj):
                old_use = block.la_use
                block.la_use = inst['use'] | (old_use - inst['def'])

                old_def = block.la_def
                block.la_def = inst['def'] | old_def
            block = block.next_block

        nodes[-1].la_out = self.global_vars

        # Liveness analisys
        while len(nodes) > 0:
            node = nodes.pop(-1)

            if isinstance(node, ConditionBlock):
                successors = [node.taken, node.fall_through]
            else:
                successors = [node.branch]

            # node.la_out = set()
            for successor in successors:
                if successor:
                    node.la_out |= successor.la_in

            old_in = node.la_in
            node.la_in = node.la_use | (node.la_out - node.la_def)

            if old_in != node.la_in:
                for pred in node.predecessors:
                    if pred and pred not in nodes:
                        nodes.insert(0, pred)

    def reset_analisys(self, cfg):
        self.code_obj = []
        self.label = 0

        block = cfg
        while isinstance(block, Block):
            block.code_obj = []
            block.rd_gen = set()
            block.rd_kill = set()
            block.rd_in = set()
            block.rd_out = set()
            block.la_def = set()
            block.la_use = set()
            block.la_in = set()
            block.la_out = set()
            block = block.next_block

    def copy_propagation(self, cfg):
        block = cfg
        while isinstance(block, Block):
            current_in = block.rd_in.copy()

            for inst in block.code_obj:
                if re.match(r'(load|store)_[^_]+$', inst['inst'][0]):
                    param = inst['inst'][1]
                    defs = {x['inst'] for x in self.code_obj if x['label'] in current_in and x['def'] == {param}}

                    if len(defs) == 1:
                        old_inst = inst['inst']

                        new_inst = list(defs.copy().pop())
                        new_inst[0] = re.sub(r'store_', 'load_', new_inst[0])
                        new_inst[-1] = list(old_inst)[-1]
                        new_inst = tuple(new_inst)

                        if not new_inst[0].startswith('load_') or new_inst[1][1:].isdigit():



                            if re.match(r'read_.*', new_inst[0]):

                                old_read = list(defs.copy().pop())

                                print('[Copy Propagation] Changing from %d: %s to %s' % (inst['label']-1, tuple(old_read), new_inst))

                                for i in block.code_obj:
                                    if i['label'] == inst['label']-1:
                                        idx = block.instructions.index(i['inst'])
                                        block.instructions[idx] = new_inst
                                        i['inst'] = new_inst
                                        break

                                new_inst = list(old_inst)
                                temp = new_inst[-1]
                                new_inst[-1] = new_inst[1]
                                new_inst[1] = temp
                                new_inst = tuple(new_inst)

                                print('[Copy Propagation] Changing from %d: %s to %s' % (inst['label'], old_inst, new_inst))

                                for i in block.code_obj:
                                    if i['label'] == inst['label']:
                                        idx = block.instructions.index(i['inst'])
                                        block.instructions[idx] = new_inst
                                        i['inst'] = new_inst
                                        break

                            # if re.match(r'call', new_inst[0]):
                            #     old_call = list(defs.copy().pop())
                            #
                            #     print('[Copy Propagation] Changing from %d: %s to %s' % ((inst['label']-1, tuple(old_call), new_inst)))
                            #
                            #     for i in block.code_obj:
                            #         if i['label'] == inst['label']-1:
                            #             idx = block.instructions.index(i['inst'])
                            #             block.instructions[idx] = new_inst
                            #             i['inst'] = new_inst
                            #             break
                            #
                            #     new_inst = list(old_inst)
                            #     temp = new_inst[-1]
                            #     new_inst[-1] = new_inst[1]
                            #     new_inst[1] = temp
                            #     new_inst = tuple(new_inst)
                            #
                            #     print('[Copy Propagation] Changing from %d: %s to %s' % (inst['label'], old_inst, new_inst))
                            #
                            #     for i in block.code_obj:
                            #         if i['label'] == inst['label']:
                            #             idx = block.instructions.index(i['inst'])
                            #             block.instructions[idx] = new_inst
                            #             i['inst'] = new_inst
                            #             return

                            if not re.match(r'(alloc|read|elem)_.*|call', new_inst[0]):
                                print('[Copy Propagation] Changing from %d: %s to %s' % (inst['label'], old_inst, new_inst))

                                for i in block.code_obj:
                                    if i['label'] == inst['label']:
                                        idx = block.instructions.index(i['inst'])
                                        block.instructions[idx] = new_inst
                                        i['inst'] = new_inst
                                        break

                if re.match(r'(add|sub|mul|div|mod|lt|le|ge|gt|eq|ne|and|or)_*', inst['inst'][0]):
                    param1 = inst['inst'][1]
                    param2 = inst['inst'][2]

                    defs1 = {x['inst'] for x in self.code_obj if x['label'] in current_in and x['def'] == {param1}}
                    defs2 = {x['inst'] for x in self.code_obj if x['label'] in current_in and x['def'] == {param2}}

                    new_inst = list(inst['inst'])

                    if len(defs1) == 1:
                        def_inst = list(defs1.copy().pop())

                        if re.match(r'(load|store)_[^_]+$', def_inst[0]):
                            new_inst[1] = def_inst[1]

                    if len(defs2) == 1:
                        def_inst = list(defs2.copy().pop())

                        if re.match(r'(load|store)_[^_]+$', def_inst[0]):
                            new_inst[2] = def_inst[1]
                    # add %1 %2 %3
                    # store %3 %x
                    # load %g %16

                    # add %1 %2 %x
                    # load %x %16

                    new_inst = tuple(new_inst)

                    if new_inst != inst['inst']:
                        print('[Copy Propagation] Changing from %d: %s to %s' % (inst['label'], inst['inst'], new_inst))

                        for i in block.code_obj:
                            if i['label'] == inst['label']:
                                idx = block.instructions.index(i['inst'])
                                block.instructions[idx] = new_inst
                                i['inst'] = new_inst
                                break

                if re.match(r'(not|return)_(?!void).*$|fptosi|sitofp|param', inst['inst'][0]):
                    param = inst['inst'][1]
                    defs = {x['inst'] for x in self.code_obj if x['label'] in current_in and x['def'] == {param}}

                    new_inst = list(inst['inst'])

                    if len(defs) == 1:
                        def_inst = list(defs.copy().pop())

                        if re.match(r'(load|store)_[^_]*$', def_inst[0]):
                            new_inst[1] = def_inst[1]

                    new_inst = tuple(new_inst)

                    if new_inst != inst['inst']:
                        print('[Copy Propagation] Changing from %d: %s to %s' % (inst['label'], inst['inst'], new_inst))

                        for i in block.code_obj:
                            if i['label'] == inst['label']:
                                idx = block.instructions.index(i['inst'])
                                block.instructions[idx] = new_inst
                                i['inst'] = new_inst
                                break

                if re.match(r'elem_.*', inst['inst'][0]):
                    param = inst['inst'][2]
                    defs = {x['inst'] for x in self.code_obj if x['label'] in current_in and x['def'] == {param}}

                    new_inst = list(inst['inst'])

                    if len(defs) == 1:
                        def_inst = list(defs.copy().pop())

                        if re.match(r'(load|store)_[^_]*$', def_inst[0]):
                            new_inst[2] = def_inst[1]

                    new_inst = tuple(new_inst)

                    if new_inst != inst['inst']:
                        print('[Copy Propagation] Changing from %d: %s to %s' % (inst['label'], inst['inst'], new_inst))

                        for i in block.code_obj:
                            if i['label'] == inst['label']:
                                idx = block.instructions.index(i['inst'])
                                block.instructions[idx] = new_inst
                                i['inst'] = new_inst
                                break


                if inst['def']:
                    inst_kill = {x['label'] for x in self.code_obj if x['def'] == inst['def']} - {inst['label']}
                    current_in -= inst_kill
                    current_in |= {inst['label']}

            block = block.next_block

    def constant_folding(self, cfg):
        block = cfg

        while isinstance(block, Block):
            current_in = block.rd_in.copy()

            for inst in block.code_obj:
                matches = re.match(r'(add|sub|mul|div|mod|lt|le|ge|gt|eq|ne|and|or)_(?!void)(.*)', inst['inst'][0])
                if matches:
                    op = matches.group(1)
                    type = matches.group(2)

                    if (op, type) == ('div', 'float'):
                        op = 'truediv'
                    elif (op, type) == ('div', 'int'):
                        op = 'floordiv'
                    elif op == 'and':
                        op = 'and_'

                    param1 = inst['inst'][1]
                    param2 = inst['inst'][2]

                    defs1 = {x['inst'] for x in self.code_obj if x['label'] in current_in and x['def'] == {param1}}
                    defs2 = {x['inst'] for x in self.code_obj if x['label'] in current_in and x['def'] == {param2}}

                    if len(defs1) == len(defs2) == 1:
                        def_inst1 = list(defs1.copy().pop())
                        def_inst2 = list(defs2.copy().pop())

                        literal_re = re.compile(r'literal_.*')
                        bool_re = re.compile(r'(eq|ne)_.*')

                        if literal_re.match(def_inst1[0]) and literal_re.match(def_inst2[0]):
                            res = getattr(operator, op)(def_inst1[1], def_inst2[1])

                            if not isinstance(res, bool):
                                if type == 'int':
                                    res = res // 1

                                new_inst = ('literal_%s' % type, res, inst['inst'][-1])
                            else:
                                if res:
                                    new_inst = ('eq_%s' % type, inst['inst'][1], inst['inst'][1], inst['inst'][-1])
                                else:
                                    new_inst = ('ne_%s' % type, inst['inst'][1], inst['inst'][1], inst['inst'][-1])

                            old_inst = inst['inst']

                            print('[Constant Folding] Changing %d: %s to %s' % (inst['label'], old_inst, new_inst))

                            idx = block.instructions.index(old_inst)
                            block.instructions[idx] = new_inst
                            inst['inst'] = new_inst
                        elif bool_re.match(def_inst1[0]) and bool_re.match(def_inst2[0]):
                            if def_inst1[1] == def_inst1[2] and def_inst2[1] == def_inst2[2]:
                                b1 = def_inst1[0].startswith('eq')
                                b2 = def_inst2[0].startswith('eq')

                                if getattr(operator, op)(b1, b2):
                                    new_inst = ('eq_%s' % type, inst['inst'][1], inst['inst'][1], inst['inst'][-1])
                                else:
                                    new_inst = ('ne_%s' % type, inst['inst'][1], inst['inst'][1], inst['inst'][-1])

                                old_inst = inst['inst']

                                print('[Constant Folding] Changing %d: %s to %s' % (inst['label'], old_inst, new_inst))

                                idx = block.instructions.index(old_inst)
                                block.instructions[idx] = new_inst
                                inst['inst'] = new_inst
                elif inst['inst'][0] == 'not_bool':
                    param1 = inst['inst'][1]

                    defs1 = {x['inst'] for x in self.code_obj if x['label'] in current_in and x['def'] == {param1}}

                    if len(defs1) == 1:
                        def_inst1 = list(defs1.copy().pop())

                        if re.match(r'(eq|ne)_.*', def_inst1[0]) and def_inst1[1] == def_inst1[2]:
                            if not def_inst1[0].startswith('eq'):
                                new_inst = ('eq_bool', inst['inst'][1], inst['inst'][1], inst['inst'][-1])
                            else:
                                new_inst = ('ne_bool', inst['inst'][1], inst['inst'][1], inst['inst'][-1])

                            old_inst = inst['inst']

                            print('[Constant Folding] Changing %d: %s to %s' % (inst['label'], old_inst, new_inst))

                            idx = block.instructions.index(old_inst)
                            block.instructions[idx] = new_inst
                            inst['inst'] = new_inst

                if inst['def']:
                    inst_kill = {x['label'] for x in self.code_obj if x['def'] == inst['def']} - {inst['label']}
                    current_in -= inst_kill
                    current_in |= {inst['label']}

            block = block.next_block

    def branch_folding(self, cfg):
        block = cfg

        while isinstance(block, Block):
            current_in = block.rd_in.copy()
            for inst in block.code_obj:
                if inst['inst'][0] == 'cbranch':
                    param = inst['inst'][1]

                    defs = {x['inst'] for x in self.code_obj if x['label'] in current_in and x['def'] == {param}}

                    if len(defs) == 1:
                        def_inst = list(defs.copy().pop())

                        if def_inst[1] == def_inst[2]:
                            new_block = self.changeBlockToBasic(block, def_inst[0].startswith('eq'))
                            if new_block == cfg:
                                cfg = new_block
                            block = new_block

                            new_inst = ('jump', block.branch.label)
                            old_inst = inst['inst']

                            print('[Branch Folding] Changing %d: %s to %s' % (inst['label'], old_inst, new_inst))

                            idx = block.instructions.index(old_inst)
                            block.instructions[idx] = new_inst
                            inst['inst'] = new_inst

                if inst['def']:
                    inst_kill = {x['label'] for x in self.code_obj if x['def'] == inst['def']} - {inst['label']}
                    current_in = {inst['label']} | (current_in - inst_kill)

            block = block.next_block

    def deadcode_elimination(self, cfg):
        nodes = []
        block = cfg
        while isinstance(block, Block):
            nodes.append(block)
            block = block.next_block

        may_kill_re = re.compile(r'(alloc|load|store|literal|elem|get|add|sub|mul|div|mod|lt|le|ge|gt|eq|ne|and|or|not)_[^_]+$|fptosi|sitofp')

        while len(nodes) > 0:
            block = nodes.pop(-1)
            current_out = block.la_out.copy()
            used_vars = set()

            for inst in reversed(block.code_obj):
                if may_kill_re.match(inst['inst'][0]):
                    _def = inst['def']
                    if not _def & current_out:
                        inst['alive'] = False

                        if re.match(r'alloc_.*', inst['inst'][0]) and inst['def'] & used_vars:
                            inst['alive'] = True

                if inst['alive']:
                    current_out = inst['use'] | (current_out - inst['def'])
                    if inst['def'] and not re.match(r'%[0-9]+', list(inst['def'])[0]):
                        used_vars |= inst['def']

            for inst in self.code_obj.copy():
                if not inst['alive']:
                    print('[Dead code elimination] Removing %d: %s' % (inst['label'], inst['inst']))
                    block.code_obj.remove(inst)
                    self.code_obj.remove(inst)

            new_instructions = [inst['inst'] for inst in block.code_obj if inst['alive']]
            old_instructions = block.instructions
            block.instructions = new_instructions

            if len(new_instructions) != len(old_instructions):
                for pred in block.predecessors:
                    if pred and pred not in nodes:
                        nodes = [pred] + nodes

    def block_removal(self, cfg):
        nodes = [cfg]
        while len(nodes) > 0:
            node = nodes.pop(0)

            node.visited = True

            if isinstance(node, BasicBlock):
                if node.branch and node.branch not in nodes and not node.branch.visited:
                    nodes.append(node.branch)
            else:
                if node.taken and node.taken not in nodes and not node.taken.visited:
                    nodes.append(node.taken)
                if node.fall_through and node.fall_through not in nodes and not node.fall_through.visited:
                    nodes.append(node.fall_through)

        block = cfg
        old_block = None
        while isinstance(block, Block):
            if block and not block.visited:
                for inst in block.code_obj:
                    self.code_obj.remove(inst)

                if old_block:
                    old_block._next_block = block.next_block

                if isinstance(block, BasicBlock) and block.branch:
                    block.branch.predecessors.remove(block)
                else:
                    if block.taken:
                        block.taken.predecessors.remove(block)
                    else:
                        block.fall_through.predecessors.remove(block)
            else:
                old_block = block
            block = block.next_block

    def merge_basic_blocks(self, cfg):
        new_blocks = []
        block = cfg
        while isinstance(block, Block):
            new_blocks.append(block)
            block = block.next_block

        for i, b in enumerate(new_blocks):
            b.visited = False

            if i > 0:
                new_blocks[i-1]._next_block = new_blocks[i]
            if i < len(new_blocks)-1:
                new_blocks[i+1].prev_block = new_blocks[i]

        new_blocks[0].prev_block = None
        new_blocks[-1].next_block = None

        new_blocks = [cfg.branch]
        while len(new_blocks) > 0:
            block = new_blocks.pop(0)
            block.visited = True

            if isinstance(block, BasicBlock) and block.branch and len(block.branch.predecessors) == 1:
                prev_block = block.prev_block
                next_block = block.next_block

                prev_block._next_block = next_block
                next_block.prev_block = prev_block

                block.branch.instructions = block.instructions + block.branch.instructions
                block.branch.label = block.label

                for pred in block.predecessors:
                    if isinstance(pred, BasicBlock):
                        pred.branch = block.branch
                    else:
                        if pred.taken == block:
                            pred.taken = block.branch
                        else:
                            pred.fall_through = block.branch
                block.branch.predecessors = block.predecessors

            if isinstance(block, BasicBlock):
                if block.branch and block.branch not in new_blocks and not block.branch.visited:
                    new_blocks.append(block.branch)
            else:
                if block.taken and block.taken not in new_blocks and not block.taken.visited:
                    new_blocks.append(block.taken)
                if block.fall_through and block.fall_through not in new_blocks and not block.fall_through.visited:
                    new_blocks.append(block.fall_through)

        self.instruction_analisys(cfg)

        nodes = []
        block = cfg
        while isinstance(block, Block):
            nodes.append(block)
            block = block.next_block

        for block in nodes:
            for i, inst in enumerate(block.code_obj):
                if i == 0 or i == len(block.code_obj)-1:
                    continue

                if len(inst['inst']) == 1:
                    block.code_obj[i]['alive'] = False
                    block.code_obj[i-1]['alive'] = False

            to_remove = [inst for inst in block.code_obj if not inst['alive']]

            for inst in to_remove:
                self.code_obj.remove(inst)
                block.code_obj.remove(inst)
                block.instructions.remove(inst['inst'])












