import networkx as nx
from cfg.basic_block import BasicBlock, Instruction
from analysis.reaching_definitions import reaching_definitions, get_reaching_defs_at

def _to_number(token):
    try:
        return float(token)
    except (ValueError, TypeError):
        return None

def _is_constant(token):
    return _to_number(token) is not None

def _find_constant_value(var, block_id, blocks):
    blk = blocks[block_id]
    reaching = {d for d in blk.rd_in if d.startswith(var + '@')}
    if not reaching:
        return None
    constant_vals = set()
    for d in reaching:
        parts = d.rsplit('@', 2)
        if len(parts) < 2:
            return None
        vname, src_id_str = parts[0], parts[1]
        if src_id_str == 'UNINIT':
            return None
        try:
            src_id = int(src_id_str)
        except ValueError:
            return None
        src_blk = blocks[src_id]
        found_def = False
        last_val = None
        
        target_idx = int(parts[2]) if len(parts) == 3 else -1
        if target_idx != -1:
            instr = src_blk.instructions[target_idx]
            if instr.defines() == var:
                found_def = True
                if instr.op == 'assign' and _is_constant(instr.arg1 or ''):
                    last_val = instr.arg1
        else:
            for instr in src_blk.instructions:
                if instr.defines() == var:
                    found_def = True
                    if instr.op == 'assign' and _is_constant(instr.arg1 or ''):
                        last_val = instr.arg1
                    else:
                        last_val = None
        if not found_def:
            return None
        if last_val is not None:
            constant_vals.add(last_val)
        else:
            return None
    if len(constant_vals) == 1:
        return constant_vals.pop()
    return None

def constant_propagation(graph, blocks, entry_id):
    reaching_definitions(graph, blocks, entry_id)
    count = 0
    for node_id, blk in blocks.items():
        local_consts = {}
        rd_vars = {d.split('@')[0] for d in blk.rd_in if not d.endswith('@UNINIT')}
        for var in rd_vars:
            val = _find_constant_value(var, node_id, blocks)
            if val is not None:
                local_consts[var] = val
        for idx, instr in enumerate(blk.instructions):
            modified = False
            new_arg1 = instr.arg1
            new_arg3 = instr.arg3
            if instr.arg1 and instr.arg1 in local_consts:
                new_arg1 = local_consts[instr.arg1]
                modified = True
            if instr.arg3 and instr.arg3 in local_consts:
                new_arg3 = local_consts[instr.arg3]
                modified = True
            if modified:
                blk.instructions[idx] = Instruction(op=instr.op, result=instr.result, arg1=new_arg1, arg2=instr.arg2, arg3=new_arg3, original_text=str(instr), opt_type='Propagated')
                count += 1
            d = instr.defines()
            if d:
                effective_instr = blk.instructions[idx]
                if effective_instr.op == 'assign' and _is_constant(effective_instr.arg1 or ''):
                    local_consts[d] = effective_instr.arg1
                else:
                    local_consts.pop(d, None)
    return count