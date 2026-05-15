import re
import sys
import os
import tempfile
import networkx as nx
import pycparser
from pycparser import c_ast, c_generator, c_parser
from cfg.basic_block import BasicBlock, Instruction

def _get_fake_libc_path():
    base = os.path.dirname(pycparser.__file__)
    fake = os.path.join(base, 'utils', 'fake_libc_include')
    if os.path.isdir(fake):
        return fake
    tmp = tempfile.mkdtemp()
    with open(os.path.join(tmp, 'stdio.h'), 'w') as f:
        f.write('int printf(const char*, ...);\nint scanf(const char*, ...);\n')
    with open(os.path.join(tmp, 'stdlib.h'), 'w') as f:
        f.write('void* malloc(int);\nvoid free(void*);\nint atoi(const char*);\n')
    with open(os.path.join(tmp, 'string.h'), 'w') as f:
        f.write('int strlen(const char*);\n')
    return tmp

class CFGBuilder(c_ast.NodeVisitor):

    def __init__(self):
        self._blocks = {}
        self._graph = nx.DiGraph()
        self._counter = 0
        self._tmp_counter = 0
        self._label_counter = 0
        self._current_block = None
        self._entry_id = None
        self._exit_id = None
        self._break_targets = []
        self._continue_targets = []
        self._generator = c_generator.CGenerator()

    def build(self, c_code):
        preamble = 'typedef unsigned int size_t;\ntypedef int bool;\n'

        def strip_comments(text):
            text = re.sub('//.*', '', text)
            text = re.sub('/\\*.*?\\*/', '', text, flags=re.DOTALL)
            return text
        source = preamble + strip_comments(c_code)
        try:
            ast = pycparser.CParser().parse(source, filename='<input>')
        except c_parser.ParseError as e:
            raise SyntaxError(f'C parse error: {e}') from e
        entry = self._new_block(label='ENTRY')
        self._entry_id = entry.id
        self._current_block = entry
        exit_block = self._new_block(label='EXIT')
        self._exit_id = exit_block.id
        self._add_instr(Instruction(op='nop'), exit_block)
        for node in ast.ext:
            if isinstance(node, c_ast.FuncDef):
                self._visit_func(node)
        if self._current_block and self._current_block.id != self._exit_id:
            self._add_edge(self._current_block.id, self._exit_id, 'fall')
        for blk in self._blocks.values():
            blk.compute_local_sets()
        return (self._graph, self._blocks, self._entry_id)

    def _new_block(self, label=''):
        blk = BasicBlock(id=self._counter, label=label)
        self._blocks[self._counter] = blk
        self._graph.add_node(self._counter, block=blk)
        self._counter += 1
        return blk

    def _add_edge(self, src, dst, kind=''):
        self._graph.add_edge(src, dst, label=kind)

    def _add_instr(self, instr, block=None):
        target = block if block is not None else self._current_block
        if target:
            target.add_instruction(instr)

    def _new_temp(self):
        name = f'_t{self._tmp_counter}'
        self._tmp_counter += 1
        return name

    def _new_label(self):
        name = f'L{self._label_counter}'
        self._label_counter += 1
        return name

    def _visit_func(self, node):
        func_name = node.decl.name
        func_block = self._new_block(label=f'func:{func_name}')
        self._add_edge(self._entry_id, func_block.id, 'call')
        self._current_block = func_block
        if node.body:
            self._visit_stmt(node.body)
        if self._current_block and self._current_block.id != self._exit_id:
            self._add_edge(self._current_block.id, self._exit_id, 'fall')

    def _visit_stmt(self, node):
        if node is None:
            return
        t = type(node).__name__
        dispatch = {'Compound': self._visit_compound, 'Decl': self._visit_decl, 'Assignment': self._visit_assignment_stmt, 'If': self._visit_if, 'While': self._visit_while, 'For': self._visit_for, 'DoWhile': self._visit_dowhile, 'Return': self._visit_return, 'FuncCall': self._visit_funccall_stmt, 'Break': self._visit_break, 'Continue': self._visit_continue, 'Label': self._visit_label_stmt, 'Goto': self._visit_goto}
        handler = dispatch.get(t)
        if handler:
            handler(node)
        elif t in ('UnaryOp', 'BinaryOp', 'Constant', 'ID', 'Cast', 'TernaryOp', 'ArrayRef', 'StructRef'):
            self._visit_expr(node)
        else:
            self._add_instr(Instruction(op='nop'))

    def _visit_compound(self, node):
        if node.block_items:
            for item in node.block_items:
                self._visit_stmt(item)

    def _visit_decl(self, node):
        if node.init is not None:
            val = self._visit_expr(node.init)
            self._add_instr(Instruction(op='assign', result=node.name, arg1=val))

    def _visit_assignment_stmt(self, node):
        self._visit_assignment(node)

    def _visit_assignment(self, node):
        rhs = self._visit_expr(node.rvalue)
        lhs = self._lvalue_name(node.lvalue)
        if node.op == '=':
            self._add_instr(Instruction(op='assign', result=lhs, arg1=rhs))
        else:
            base_op = node.op[:-1]
            tmp = self._new_temp()
            self._add_instr(Instruction(op='binop', result=tmp, arg1=lhs, arg2=base_op, arg3=rhs))
            self._add_instr(Instruction(op='assign', result=lhs, arg1=tmp))
        return lhs

    def _lvalue_name(self, node):
        if isinstance(node, c_ast.ID):
            return node.name
        if isinstance(node, c_ast.ArrayRef):
            idx = self._visit_expr(node.subscript)
            base = self._lvalue_name(node.name)
            return f'{base}[{idx}]'
        if isinstance(node, c_ast.StructRef):
            return self._generator.visit(node)
        return '_unknown_lval'

    def _visit_expr(self, node):
        if node is None:
            return '_none'
        t = type(node).__name__
        if t == 'Constant':
            return node.value
        if t == 'ID':
            return node.name
        if t == 'BinaryOp':
            return self._visit_binop(node)
        if t == 'UnaryOp':
            return self._visit_unaryop(node)
        if t == 'Assignment':
            return self._visit_assignment(node)
        if t == 'FuncCall':
            return self._visit_funccall_expr(node)
        if t == 'Cast':
            return self._visit_expr(node.expr)
        if t == 'TernaryOp':
            return self._visit_ternary(node)
        if t == 'ArrayRef':
            idx = self._visit_expr(node.subscript)
            base = self._visit_expr(node.name)
            tmp = self._new_temp()
            self._add_instr(Instruction(op='assign', result=tmp, arg1=f'{base}[{idx}]'))
            return tmp
        if t == 'StructRef':
            tmp = self._new_temp()
            self._add_instr(Instruction(op='assign', result=tmp, arg1=self._generator.visit(node)))
            return tmp
        tmp = self._new_temp()
        self._add_instr(Instruction(op='assign', result=tmp, arg1=self._generator.visit(node)))
        return tmp

    def _visit_binop(self, node):
        left = self._visit_expr(node.left)
        right = self._visit_expr(node.right)
        tmp = self._new_temp()
        self._add_instr(Instruction(op='binop', result=tmp, arg1=left, arg2=node.op, arg3=right))
        return tmp

    def _visit_unaryop(self, node):
        if node.op in ('p++', 'p--'):
            base = self._visit_expr(node.expr)
            old = self._new_temp()
            self._add_instr(Instruction(op='assign', result=old, arg1=base))
            op = '+' if node.op == 'p++' else '-'
            tmp = self._new_temp()
            self._add_instr(Instruction(op='binop', result=tmp, arg1=base, arg2=op, arg3='1'))
            lhs = self._lvalue_name(node.expr)
            self._add_instr(Instruction(op='assign', result=lhs, arg1=tmp))
            return old
        if node.op in ('++', '--'):
            base = self._visit_expr(node.expr)
            op = '+' if node.op == '++' else '-'
            tmp = self._new_temp()
            self._add_instr(Instruction(op='binop', result=tmp, arg1=base, arg2=op, arg3='1'))
            lhs = self._lvalue_name(node.expr)
            self._add_instr(Instruction(op='assign', result=lhs, arg1=tmp))
            return tmp
        operand = self._visit_expr(node.expr)
        tmp = self._new_temp()
        self._add_instr(Instruction(op='unop', result=tmp, arg1=node.op, arg2=operand))
        return tmp

    def _visit_funccall_expr(self, node):
        func_name = self._visit_expr(node.name)
        args = []
        if node.args:
            for arg in node.args.exprs:
                args.append(self._visit_expr(arg))
        for a in args:
            self._add_instr(Instruction(op='param', arg1=a))
        tmp = self._new_temp()
        self._add_instr(Instruction(op='call', result=tmp, arg1=func_name, arg2=','.join(args)))
        return tmp

    def _visit_funccall_stmt(self, node):
        self._visit_funccall_expr(node)

    def _visit_ternary(self, node):
        cond = self._visit_expr(node.cond)
        cond_blk = self._current_block
        true_label = self._new_label()
        false_label = self._new_label()
        merge_label = self._new_label()
        tmp = self._new_temp()
        self._add_instr(Instruction(op='ifgoto', arg1=cond, arg2=true_label, arg3=false_label))
        
        true_blk = self._new_block(label=true_label)
        self._add_edge(cond_blk.id, true_blk.id, 'true')
        self._current_block = true_blk
        tv = self._visit_expr(node.iftrue)
        self._add_instr(Instruction(op='assign', result=tmp, arg1=tv))
        self._add_instr(Instruction(op='goto', arg1=merge_label))
        true_exit = self._current_block
        
        false_blk = self._new_block(label=false_label)
        self._add_edge(cond_blk.id, false_blk.id, 'false')
        self._current_block = false_blk
        fv = self._visit_expr(node.iffalse)
        self._add_instr(Instruction(op='assign', result=tmp, arg1=fv))
        false_exit = self._current_block
        
        merge_blk = self._new_block(label=merge_label)
        self._add_edge(true_exit.id, merge_blk.id, 'fall')
        self._add_edge(false_exit.id, merge_blk.id, 'fall')
        self._current_block = merge_blk
        return tmp

    def _visit_if(self, node):
        if self._current_block and self._current_block.instructions:
            cond_lbl = self._new_label()
            cond_blk = self._new_block(label=cond_lbl)
            self._add_instr(Instruction(op='goto', arg1=cond_lbl))
            self._add_edge(self._current_block.id, cond_blk.id, 'fall')
            self._current_block = cond_blk
        cond = self._visit_expr(node.cond)
        true_label = self._new_label()
        merge_label = self._new_label()
        if node.iffalse:
            false_label = self._new_label()
            self._add_instr(Instruction(op='ifgoto', arg1=cond, arg2=true_label, arg3=false_label))
        else:
            self._add_instr(Instruction(op='ifgoto', arg1=cond, arg2=true_label, arg3=merge_label))
        cond_block = self._current_block
        true_blk = self._new_block(label=true_label)
        self._add_edge(cond_block.id, true_blk.id, 'true')
        self._current_block = true_blk
        self._visit_stmt(node.iftrue)
        true_end = self._current_block
        self._add_instr(Instruction(op='goto', arg1=merge_label))
        if node.iffalse:
            false_blk = self._new_block(label=false_label)
            self._add_edge(cond_block.id, false_blk.id, 'false')
            self._current_block = false_blk
            self._visit_stmt(node.iffalse)
            false_end = self._current_block
            self._add_instr(Instruction(op='goto', arg1=merge_label))
        merge_blk = self._new_block(label=merge_label)
        self._add_edge(true_end.id, merge_blk.id, 'fall')
        if node.iffalse:
            self._add_edge(false_end.id, merge_blk.id, 'fall')
        else:
            self._add_edge(cond_block.id, merge_blk.id, 'false')
        self._current_block = merge_blk

    def _visit_while(self, node):
        header_label = self._new_label()
        body_label = self._new_label()
        exit_label = self._new_label()
        header_blk = self._new_block(label=header_label)
        self._add_edge(self._current_block.id, header_blk.id, 'fall')
        self._current_block = header_blk
        cond = self._visit_expr(node.cond)
        self._add_instr(Instruction(op='ifgoto', arg1=cond, arg2=body_label, arg3=exit_label))
        body_blk = self._new_block(label=body_label)
        self._add_edge(header_blk.id, body_blk.id, 'true')
        self._current_block = body_blk
        self._break_targets.append([])
        self._continue_targets.append([])
        self._visit_stmt(node.stmt)
        body_end = self._current_block
        self._add_edge(body_end.id, header_blk.id, 'back')
        exit_blk = self._new_block(label=exit_label)
        self._add_edge(header_blk.id, exit_blk.id, 'false')
        self._current_block = exit_blk
        for brk in self._break_targets.pop():
            self._add_edge(brk, exit_blk.id, 'break')
        conts = self._continue_targets.pop()
        for c in conts:
            self._add_edge(c, header_blk.id, 'continue')

    def _visit_for(self, node):
        if node.init:
            self._visit_stmt(node.init)
        header_label = self._new_label()
        body_label = self._new_label()
        incr_label = self._new_label()
        exit_label = self._new_label()
        header_blk = self._new_block(label=header_label)
        self._add_edge(self._current_block.id, header_blk.id, 'fall')
        self._current_block = header_blk
        if node.cond:
            cond = self._visit_expr(node.cond)
            self._add_instr(Instruction(op='ifgoto', arg1=cond, arg2=body_label, arg3=exit_label))
        else:
            self._add_instr(Instruction(op='goto', arg1=body_label))
        body_blk = self._new_block(label=body_label)
        self._add_edge(header_blk.id, body_blk.id, 'true')
        self._current_block = body_blk
        self._break_targets.append([])
        self._continue_targets.append([])
        self._visit_stmt(node.stmt)
        body_end = self._current_block
        incr_blk = self._new_block(label=incr_label)
        self._add_edge(body_end.id, incr_blk.id, 'fall')
        self._current_block = incr_blk
        if node.next:
            self._visit_stmt(node.next)
        self._add_edge(incr_blk.id, header_blk.id, 'back')
        exit_blk = self._new_block(label=exit_label)
        self._add_edge(header_blk.id, exit_blk.id, 'false')
        self._current_block = exit_blk
        for brk in self._break_targets.pop():
            self._add_edge(brk, exit_blk.id, 'break')
        for cont in self._continue_targets.pop():
            self._add_edge(cont, incr_blk.id, 'continue')

    def _visit_dowhile(self, node):
        body_label = self._new_label()
        cond_label = self._new_label()
        exit_label = self._new_label()
        body_blk = self._new_block(label=body_label)
        self._add_edge(self._current_block.id, body_blk.id, 'fall')
        self._current_block = body_blk
        self._break_targets.append([])
        self._continue_targets.append([])
        self._visit_stmt(node.stmt)
        body_end = self._current_block
        cond_blk = self._new_block(label=cond_label)
        self._add_edge(body_end.id, cond_blk.id, 'fall')
        self._current_block = cond_blk
        cond = self._visit_expr(node.cond)
        self._add_instr(Instruction(op='ifgoto', arg1=cond, arg2=body_label, arg3=exit_label))
        exit_blk = self._new_block(label=exit_label)
        self._add_edge(cond_blk.id, body_blk.id, 'back')
        self._add_edge(cond_blk.id, exit_blk.id, 'false')
        self._current_block = exit_blk
        for brk in self._break_targets.pop():
            self._add_edge(brk, exit_blk.id, 'break')
        for cont in self._continue_targets.pop():
            self._add_edge(cont, cond_blk.id, 'continue')

    def _visit_return(self, node):
        val = self._visit_expr(node.expr) if node.expr else None
        self._add_instr(Instruction(op='return', arg1=val))
        self._add_edge(self._current_block.id, self._exit_id, 'return')
        dead = self._new_block(label='dead')
        self._current_block = dead

    def _visit_break(self, node):
        if self._break_targets:
            src = self._current_block.id
            self._break_targets[-1].append(src)
            dead = self._new_block(label='dead')
            self._current_block = dead

    def _visit_continue(self, node):
        if self._continue_targets:
            src = self._current_block.id
            self._continue_targets[-1].append(src)
            dead = self._new_block(label='dead')
            self._current_block = dead

    def _visit_label_stmt(self, node):
        lbl_blk = self._new_block(label=node.name)
        self._add_edge(self._current_block.id, lbl_blk.id, 'fall')
        self._current_block = lbl_blk
        self._add_instr(Instruction(op='label', arg1=node.name))
        self._visit_stmt(node.stmt)

    def _visit_goto(self, node):
        self._add_instr(Instruction(op='goto', arg1=node.name))

def build_cfg(c_code):
    builder = CFGBuilder()
    return builder.build(c_code)