import networkx as nx
from cfg.basic_block import BasicBlock, Instruction, _is_variable
from analysis.live_variables import live_variable_analysis, find_dead_assignments

def dead_code_elimination(graph, blocks, entry_id):
    live_variable_analysis(graph, blocks, entry_id)
    removed = 0
    for blk in blocks.values():
        live_after = set(blk.lv_out)
        new_instrs = []
        removed_local = 0
        for instr in reversed(blk.instructions):
            d = instr.defines()
            keep = True
            if d and _is_variable(d):
                is_mem_write = any(c in d for c in ('[', ']', '*', '.', '->'))
                if d not in live_after and not is_mem_write:
                    if instr.op not in ('call',):
                        keep = False
                        removed_local += 1
            if keep:
                new_instrs.append(instr)
                if d:
                    live_after.discard(d)
                live_after |= {v for v in instr.uses() if _is_variable(v)}
            else:
                new_instrs.append(Instruction(op='nop', original_text=str(instr), opt_type='Removed'))
        blk.instructions = list(reversed(new_instrs))
        removed += removed_local
    return removed

def remove_nops(blocks):
   
    for blk in blocks.values():
        old_len = len(blk.instructions)
        blk.instructions = [i for i in blk.instructions if i.op != 'nop']
        removed += old_len - len(blk.instructions)
    return removed