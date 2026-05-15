import networkx as nx
from cfg.basic_block import BasicBlock, Instruction

def _def_id(var, block_id, instr_idx):
    return f'{var}@{block_id}@{instr_idx}'

def compute_rd_gen_kill(blocks):
    all_defs = {}
    for blk in blocks.values():
        for idx, instr in enumerate(blk.instructions):
            d = instr.defines()
            if d:
                all_defs.setdefault(d, set()).add((blk.id, idx))
    for blk in blocks.values():
        gen_map = {}
        kill_set = set()
        local_defs = {}
        for idx, instr in enumerate(blk.instructions):
            d = instr.defines()
            if d:
                def_id = _def_id(d, blk.id, idx)
                gen_map[d] = def_id
                for other_bid, other_idx in all_defs.get(d, set()):
                    if other_bid != blk.id or other_idx != idx:
                        kill_set.add(_def_id(d, other_bid, other_idx))
        blk.gen = set(gen_map.values())
        blk.kill = kill_set

def reaching_definitions(graph, blocks, entry_id):
   
    compute_rd_gen_kill(blocks)
    for blk in blocks.values():
        blk.rd_in = set()
        blk.rd_out = set(blk.gen)
    all_vars = set()
    for blk in blocks.values():
        for instr in blk.instructions:
            for use in instr.uses():
                if not use.startswith('_t'):
                    all_vars.add(use)
            d = instr.defines()
            if d and (not d.startswith('_t')):
                all_vars.add(d)
    if entry_id in blocks:
        for v in all_vars:
            blocks[entry_id].rd_out.add(f'{v}@UNINIT')
    worklist = list(nx.bfs_tree(graph, entry_id).nodes())
    worklist_set = set(worklist)
    iteration = 0
    max_iterations = len(blocks) * 10
    while worklist and iteration < max_iterations:
        iteration += 1
        node_id = worklist.pop(0)
        worklist_set.discard(node_id)
        blk = blocks.get(node_id)
        if blk is None:
            continue
        new_in = set()
        for pred_id in graph.predecessors(node_id):
            pred = blocks.get(pred_id)
            if pred:
                new_in |= pred.rd_out
        blk.rd_in = new_in
        new_out = blk.gen | new_in - blk.kill
        if new_out != blk.rd_out:
            blk.rd_out = new_out
            for succ_id in graph.successors(node_id):
                if succ_id not in worklist_set:
                    worklist.append(succ_id)
                    worklist_set.add(succ_id)

def find_uninitialized_uses(blocks):
  
    issues = []
    for blk in blocks.values():
        defined_before = set()
        uninit_in = {d.split('@')[0] for d in blk.rd_in if d.endswith('@UNINIT')}
        defined_by_rd = {d.split('@')[0] for d in blk.rd_in if not d.endswith('@UNINIT')}
        for instr in blk.instructions:
            for used_var in instr.uses():
                if (used_var in uninit_in or used_var not in defined_by_rd) and used_var not in defined_before and (not used_var.startswith('_t')):
                    issues.append((blk.id, used_var))
            d = instr.defines()
            if d:
                defined_before.add(d)
    return issues

def get_reaching_defs_at(block_id, blocks):
    blk = blocks[block_id]
    result = {}
    for d in blk.rd_in:
        parts = d.rsplit('@', 2)
        if len(parts) < 2: continue
        var = parts[0]
        src = parts[1]
        if src == 'UNINIT':
            continue
        result.setdefault(var, set()).add(int(src))
    return result