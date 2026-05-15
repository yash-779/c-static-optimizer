import networkx as nx
from cfg.basic_block import BasicBlock, Instruction

def simplify_control_flow(graph, blocks):
    changed = True
    while changed:
        changed = False
        for bid, blk in blocks.items():
            if not blk.instructions:
                continue
            is_pass_through = True
            target_label = None
            for instr in blk.instructions:
                if instr.op in ('nop', 'label'):
                    continue
                elif instr.op == 'goto':
                    target_label = instr.arg1
                else:
                    is_pass_through = False
                    break
            if is_pass_through and target_label:
                target_bid = None
                for b in blocks.values():
                    if b.label == target_label:
                        target_bid = b.id
                        break
                if target_bid is not None and target_bid != bid:
                    in_edges = list(graph.in_edges(bid, data=True))
                    if in_edges:
                        for src, _, data in in_edges:
                            graph.remove_edge(src, bid)
                            if data.get('label') in ('true', 'false'):
                                pass
                            graph.add_edge(src, target_bid, **data)
                        for src, _, _ in in_edges:
                            src_blk = blocks[src]
                            for instr in src_blk.instructions:
                                if instr.op == 'goto' and instr.arg1 == blk.label:
                                    instr.arg1 = target_label
                                    changed = True
                                elif instr.op == 'ifgoto':
                                    if instr.arg2 == blk.label:
                                        instr.arg2 = target_label
                                        changed = True
                                    if instr.arg3 == blk.label:
                                        instr.arg3 = target_label
                                        changed = True
        for bid, blk in blocks.items():
            for idx, instr in enumerate(blk.instructions):
                if instr.op == 'ifgoto' and instr.arg2 == instr.arg3:
                    blk.instructions[idx] = Instruction(op='goto', arg1=instr.arg2, opt_type='Removed', original_text=str(instr))
                    changed = True

def remove_unreachable_code(graph, blocks, entry_id):
    simplify_control_flow(graph, blocks)
    reachable = set(nx.descendants(graph, entry_id))
    reachable.add(entry_id)
    all_nodes = set(graph.nodes)
    unreachable = all_nodes - reachable
    if not unreachable:
        return (graph, blocks, [])
    new_graph = graph.copy()
    new_graph.remove_nodes_from(unreachable)
    new_blocks = {bid: blk for bid, blk in blocks.items() if bid in reachable}
    return (new_graph, new_blocks, list(unreachable))

def find_dead_blocks(graph, blocks, entry_id):
    dead = []
    reachable = set(nx.descendants(graph, entry_id))
    reachable.add(entry_id)
    for bid in reachable:
        blk = blocks.get(bid)
        if blk and blk.label == 'dead' and blk.is_empty():
            dead.append(bid)
    return dead