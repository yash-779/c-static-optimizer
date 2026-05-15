import networkx as nx
from cfg.basic_block import BasicBlock, Instruction, _is_variable

class Loop:

    def __init__(self, header, body, back_edge):
        self.header = header
        self.body = body
        self.back_edge = back_edge
        self.licm_candidates = []

    def __repr__(self):
        return f'Loop(header={self.header}, body={sorted(self.body)}, back_edge={self.back_edge}, licm={len(self.licm_candidates)} candidates)'

def _compute_dominators(graph, entry_id):
    dom_tree = nx.immediate_dominators(graph, entry_id)
    all_nodes = set(graph.nodes)
    doms = {}
    for n in all_nodes:
        dominated_by = set()
        cur = n
        while True:
            dominated_by.add(cur)
            parent = dom_tree.get(cur)
            if parent is None or parent == cur:
                break
            cur = parent
        doms[n] = dominated_by
    return doms

def _find_loop_body(graph, header, tail):
    body = {header}
    stack = []
    if tail != header:
        body.add(tail)
        stack.append(tail)
    rev_graph = graph.reverse()
    while stack:
        node = stack.pop()
        for pred in rev_graph.successors(node):
            if pred not in body:
                body.add(pred)
                stack.append(pred)
    return body

def detect_loops(graph, blocks, entry_id):
    try:
        doms = _compute_dominators(graph, entry_id)
    except Exception:
        return []
    loops = []
    for src, dst in graph.edges():
        if dst in doms.get(src, set()):
            body = _find_loop_body(graph, header=dst, tail=src)
            loop = Loop(header=dst, body=body, back_edge=(src, dst))
            _find_licm_candidates(loop, blocks)
            loops.append(loop)
    return loops

def _find_licm_candidates(loop, blocks):
    loop_defined = set()
    for bid in loop.body:
        blk = blocks.get(bid)
        if blk:
            for instr in blk.instructions:
                d = instr.defines()
                if d:
                    loop_defined.add(d)
    for bid in loop.body:
        blk = blocks.get(bid)
        if blk is None:
            continue
        for idx, instr in enumerate(blk.instructions):
            if instr.op not in ('assign', 'binop', 'unop'):
                continue
            is_safe = True
            if instr.op == 'binop' and instr.arg2 in ('/', '%'):
                is_safe = False
            # Block memory accesses (arrays, structs, pointers)
            if any((c in str(instr) for c in ('[', ']', '.', '->'))):
                is_safe = False
            # Only block '*' if it's a unary pointer dereference, not binary multiplication
            if instr.op == 'unop' and instr.arg1 == '*':
                is_safe = False
            if instr.op == 'assign' and isinstance(instr.arg1, str) and instr.arg1.startswith('*'):
                is_safe = False
            if not is_safe:
                continue
            operands = [x for x in [instr.arg1, instr.arg2, instr.arg3] if x and _is_variable(x)]
            if all((op not in loop_defined for op in operands)):
                loop.licm_candidates.append((bid, idx, instr, str(instr)))

def perform_licm(graph, blocks, loops):
    moved_count = 0
    for loop in loops:
        if not loop.licm_candidates:
            continue
        pre_header_id = max(blocks.keys()) + 1
        pre_header = BasicBlock(id=pre_header_id, label=f'preheader_for_{loop.header}')
        blocks[pre_header_id] = pre_header
        graph.add_node(pre_header_id, block=pre_header)
        preds = [p for p in graph.predecessors(loop.header) if p not in loop.body]
        for p in preds:
            edge_data = graph.get_edge_data(p, loop.header)
            graph.remove_edge(p, loop.header)
            graph.add_edge(p, pre_header_id, **edge_data)
        graph.add_edge(pre_header_id, loop.header, label='fall')
        for bid, idx, instr, text_snapshot in sorted(loop.licm_candidates, key=lambda x: x[1], reverse=True):
            original_instr = blocks[bid].instructions[idx]
            new_instr = Instruction(op=original_instr.op, result=original_instr.result, arg1=original_instr.arg1, arg2=original_instr.arg2, arg3=original_instr.arg3, original_text=f'hoisted from Block {bid}: {text_snapshot}', opt_type='Moved')
            pre_header.add_instruction(new_instr)
            blocks[bid].instructions[idx] = Instruction(op='nop', opt_type='Moved', original_text=text_snapshot)
            moved_count += 1
    return moved_count