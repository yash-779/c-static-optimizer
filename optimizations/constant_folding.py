import operator
from cfg.basic_block import BasicBlock, Instruction
_BINOP_MAP = {'+': operator.add, '-': operator.sub, '*': operator.mul, '/': lambda a, b: int(a / b) if b != 0 else None, '%': lambda a, b: a % b if b != 0 else None, '&': operator.and_, '|': operator.or_, '^': operator.xor, '<<': operator.lshift, '>>': operator.rshift, '<': lambda a, b: int(a < b), '>': lambda a, b: int(a > b), '<=': lambda a, b: int(a <= b), '>=': lambda a, b: int(a >= b), '==': lambda a, b: int(a == b), '!=': lambda a, b: int(a != b), '&&': lambda a, b: int(bool(a) and bool(b)), '||': lambda a, b: int(bool(a) or bool(b))}
_UNOP_MAP = {'-': lambda a: -a, '!': lambda a: int(not bool(a)), '~': lambda a: ~a}

def _to_number(token):
    try:
        return float(token)
    except (ValueError, TypeError):
        return None

def _fmt_number(n):
    if n == int(n):
        return str(int(n))
    return str(n)

def constant_folding(blocks):
    count = 0
    for blk in blocks.values():
        for idx, instr in enumerate(blk.instructions):
            if instr.op == 'binop':
                a = _to_number(instr.arg1)
                b = _to_number(instr.arg3)
                op = instr.arg2
                if a is not None and b is not None and (op in _BINOP_MAP):
                    if op in ('<<', '>>', '&', '|', '^'):
                        if not float(a).is_integer() or not float(b).is_integer():
                            continue
                        a = int(a)
                        b = int(b)
                    result = _BINOP_MAP[op](a, b)
                    if result is not None:
                        blk.instructions[idx] = Instruction(op='assign', result=instr.result, arg1=_fmt_number(result), original_text=str(instr), opt_type='Folded')
                        count += 1
            elif instr.op == 'unop':
                a = _to_number(instr.arg2)
                op = instr.arg1
                if a is not None and op in _UNOP_MAP:
                    result = _UNOP_MAP[op](a)
                    blk.instructions[idx] = Instruction(op='assign', result=instr.result, arg1=_fmt_number(result), original_text=str(instr), opt_type='Folded')
                    count += 1
    return count