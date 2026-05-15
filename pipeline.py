import time
import copy
from dataclasses import dataclass, field
import networkx as nx
from cfg.basic_block import BasicBlock
from cfg.builder import build_cfg
from cfg.visualizer import cfg_to_dot
from analysis.reaching_definitions import reaching_definitions, find_uninitialized_uses
from analysis.live_variables import live_variable_analysis, find_dead_assignments
from optimizations.constant_folding import constant_folding
from optimizations.constant_propagation import constant_propagation
from optimizations.dead_code_elimination import dead_code_elimination, remove_nops
from optimizations.unreachable_code import remove_unreachable_code
from optimizations.loop_detection import detect_loops, Loop, perform_licm

class PipelineResult:

    def __init__(self):
        self.graph = nx.DiGraph()
        self.blocks = {}
        self.blocks_before = {}
        self.blocks_pre_cleanup = {}
        self.blocks_after_prop = {}
        self.graph_before = nx.DiGraph()
        self.entry_id = 0
        self.cfg_dot_before = ''
        self.cfg_dot_after = ''
        self.uninitialized_uses = []
        self.dead_assignments = []
        self.loops = []
        self.folded = 0
        self.propagated = 0
        self.dead_removed = 0
        self.nops_removed = 0
        self.unreachable_ids = []
        self.errors = []
        self.parse_error = None
        self.elapsed_ms = 0.0

    def summary(self):
        lines = ['══════════════════════════════════════════', '         PIPELINE SUMMARY', '══════════════════════════════════════════', f'  Blocks (after opt):    {len(self.blocks)}', f'  CFG edges:             {self.graph.number_of_edges()}', '', '  ── Static Analysis ──', f'  Uninitialized uses:    {len(self.uninitialized_uses)}', f'  Dead assignments:      {len(self.dead_assignments)}', f'  Loops detected:        {len(self.loops)}', '', '  ── Optimizations ──', f'  Constant folds:        {self.folded}', f'  Const propagations:    {self.propagated}', f'  Dead instrs removed:   {self.dead_removed}', f'  NOPs removed:          {self.nops_removed}', f'  Unreachable blocks:    {len(self.unreachable_ids)}', '', f'  Elapsed: {self.elapsed_ms:.1f} ms', '══════════════════════════════════════════']
        return '\n'.join(lines)

def run_pipeline(c_code, pass_sequence=None):
    if pass_sequence is None:
        pass_sequence = ['fold', 'prop', 'fold', 'dce', 'unreachable', 'dce', 'licm']
    result = PipelineResult()
    t_start = time.perf_counter()
    try:
        graph, blocks, entry_id = build_cfg(c_code)
        result.blocks = blocks
        result.blocks_before = copy.deepcopy(blocks)
        result.graph = graph
        result.graph_before = copy.deepcopy(graph)
        result.entry_id = entry_id
    except SyntaxError as e:
        result.parse_error = str(e)
        result.errors.append(f'Parse error: {e}')
        result.elapsed_ms = (time.perf_counter() - t_start) * 1000
        return result
    except Exception as e:
        result.parse_error = str(e)
        result.errors.append(f'CFG build error: {e}')
        result.elapsed_ms = (time.perf_counter() - t_start) * 1000
        return result
    result.cfg_dot_before = cfg_to_dot(graph, blocks, title='CFG – Before Optimizations')
    try:
        reaching_definitions(graph, blocks, entry_id)
        result.uninitialized_uses = find_uninitialized_uses(blocks)
    except Exception as e:
        result.errors.append(f'Reaching definitions error: {e}')
    try:
        live_variable_analysis(graph, blocks, entry_id)
        result.dead_assignments = find_dead_assignments(blocks)
    except Exception as e:
        result.errors.append(f'Live variable analysis error: {e}')
    for pass_name in pass_sequence:
        pass_name = pass_name.lower().strip()
        if pass_name == 'fold':
            try:
                result.folded += constant_folding(blocks)
            except Exception as e:
                result.errors.append(f'Constant folding error: {e}')
        elif pass_name == 'prop':
            try:
                result.propagated += constant_propagation(graph, blocks, entry_id)
            except Exception as e:
                result.errors.append(f'Constant propagation error: {e}')
        elif pass_name == 'dce':
            try:
                result.dead_removed += dead_code_elimination(graph, blocks, entry_id)
            except Exception as e:
                result.errors.append(f'DCE error: {e}')
        elif pass_name == 'unreachable':
            try:
                graph, blocks, removed = remove_unreachable_code(graph, blocks, entry_id)
                result.graph = graph
                result.blocks = blocks
                if not isinstance(result.unreachable_ids, list):
                    result.unreachable_ids = []
                result.unreachable_ids.extend(removed)
            except Exception as e:
                result.errors.append(f'Unreachable code removal error: {e}')
        elif pass_name == 'licm':
            try:
                result.loops = detect_loops(graph, blocks, entry_id)
                perform_licm(graph, blocks, result.loops)
                result.graph = graph
                result.blocks = blocks
            except Exception as e:
                result.errors.append(f'LICM error: {e}')
    result.blocks_after_prop = copy.deepcopy(blocks)
    try:
        reaching_definitions(graph, blocks, entry_id)
        live_variable_analysis(graph, blocks, entry_id)
        result.cfg_dot_after = cfg_to_dot(graph, blocks, title='CFG – After Optimizations', show_dataflow=False)
    except Exception as e:
        result.errors.append(f'Post-opt visualization error: {e}')
        result.cfg_dot_after = result.cfg_dot_before
    result.blocks_pre_cleanup = copy.deepcopy(blocks)
    try:
        result.nops_removed = remove_nops(blocks)
    except Exception as e:
        result.errors.append(f'NOP removal error: {e}')
    result.elapsed_ms = (time.perf_counter() - t_start) * 1000
    return result