class Instruction:

    def __init__(self, op, result=None, arg1=None, arg2=None, arg3=None, original_text=None, opt_type=None):
        self.op = op
        self.result = result
        self.arg1 = arg1
        self.arg2 = arg2
        self.arg3 = arg3
        self.original_text = original_text
        self.opt_type = opt_type

    def defines(self):
        if self.op in ('assign', 'binop', 'unop', 'call'):
            return self.result
        return None

    def uses(self):
        used = set()
        if self.op in ('goto', 'label'):
            return used
        vals_to_check = [self.arg1] if self.op == 'ifgoto' else [self.arg1, self.arg2, self.arg3]
        for val in vals_to_check:
            if val and _is_variable(val):
                used.add(val)
        return used

    def __str__(self):
        if self.op == 'assign':
            return f'{self.result} = {self.arg1}'
        if self.op == 'binop':
            return f'{self.result} = {self.arg1} {self.arg2} {self.arg3}'
        if self.op == 'unop':
            return f'{self.result} = {self.arg1}{self.arg2}'
        if self.op == 'call':
            if self.arg2:
                return f'{self.result} = call {self.arg1}({self.arg2})'
            else:
                return f'{self.result} = call {self.arg1}()'
        if self.op == 'return':
            if self.arg1:
                return f'return {self.arg1}'
            else:
                return 'return '
        if self.op == 'goto':
            return f'goto {self.arg1}'
        if self.op == 'ifgoto':
            return f'if {self.arg1} goto {self.arg2} else goto {self.arg3}'
        if self.op == 'label':
            return f'[label: {self.arg1}]'
        if self.op == 'param':
            return f'param {self.arg1}'
        if self.op == 'nop':
            return 'nop'
        return f'{self.op} {self.arg1} {self.arg2} {self.arg3}'

def _is_variable(token):
    try:
        float(token)
        return False
    except:
        pass
    if type(token) == str and token.startswith('"'):
        return False
    if token and (token[0].isalpha() or (len(token) > 1 and token[0] == '_')):
        return True
    return False

class BasicBlock:

    def __init__(self, id, label=''):
        self.id = id
        self.label = label
        self.instructions = []
        self.gen = set()
        self.kill = set()
        self.use = set()
        self.defs = set()
        self.rd_in = set()
        self.rd_out = set()
        self.lv_in = set()
        self.lv_out = set()

    def add_instruction(self, instr):
        self.instructions.append(instr)

    def is_empty(self):
        return len(self.instructions) == 0

    def last_instruction(self):
        if self.instructions:
            return self.instructions[-1]
        return None

    def compute_local_sets(self):
        gen_map = {}
        defined_here = set()
        for instr in self.instructions:
            d = instr.defines()
            if d:
                gen_map[d] = d
                defined_here.add(d)
        self.gen = set(gen_map.keys())
        self.kill = defined_here.copy()
        defined_so_far = set()
        for instr in self.instructions:
            for v in instr.uses():
                if v not in defined_so_far:
                    self.use.add(v)
            d = instr.defines()
            if d:
                defined_so_far.add(d)
                self.defs.add(d)

    def to_dot_label(self):
        lines = [f'<<B>Block {self.id}</B>>']
        if self.label:
            lines.append(f'[{self.label}]')
        for instr in self.instructions:
            text = str(instr)
            text = text.replace('&', '&amp;')
            text = text.replace('<', '&lt;')
            text = text.replace('>', '&gt;')
            lines.append(text)
        return '\\n'.join(lines)

    def __repr__(self):
        return f"<BasicBlock id={self.id} label='{self.label}' instrs={len(self.instructions)}>"