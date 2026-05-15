import networkx as nx
from cfg.basic_block import BasicBlock, Instruction, _is_variable

def compute_use_def(blocks):
    for blk in blocks.values():
        use = set()
        defs = set()
        for instr in blk.instructions:
            for v in instr.uses():
                if v not in defs and _is_variable(v):
                    use.add(v)
            d = instr.defines()
            if d and _is_variable(d):
                defs.add(d)
        blk.use = use
        blk.defs = defs

def live_variable_analysis(graph, blocks, entry_id):
    compute_use_def(blocks)
    for blk in blocks.values():
        blk.lv_in = set()
        blk.lv_out = set()
    try:
        topo = list(nx.topological_sort(graph))
    except nx.NetworkXUnfeasible:
        topo = list(graph.nodes)
    rev_topo = list(reversed(topo))
    changed = True
    iterations = 0
    max_iter = len(blocks) * 10
    while changed and iterations < max_iter:
        changed = False
        iterations += 1
        for node_id in rev_topo:
            blk = blocks.get(node_id)
            if blk is None:
                continue
            new_out = set()
            for succ_id in graph.successors(node_id):
                succ = blocks.get(succ_id)
                if succ:
                    new_out |= succ.lv_in
            new_in = blk.use | new_out - blk.defs
            if new_out != blk.lv_out or new_in != blk.lv_in:
                blk.lv_out = new_out
                blk.lv_in = new_in
                changed = True

def find_dead_assignments(blocks):
    dead = []
    for blk in blocks.values():
        live_after = set(blk.lv_out)
        for idx in range(len(blk.instructions) - 1, -1, -1):
            instr = blk.instructions[idx]
            d = instr.defines()
            is_dead = False
            if d and _is_variable(d):
                if d not in live_after:
                    dead.append((blk.id, idx, d))
                    is_dead = True
            if not is_dead:
                if d:
                    if d in live_after:
                        live_after.remove(d)
                for v in instr.uses():
                    if _is_variable(v):
                        live_after.add(v)
    return dead