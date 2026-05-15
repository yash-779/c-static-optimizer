from __future__ import annotations
import os
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from pipeline import run_pipeline
app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/analyze', methods=['POST'])
def analyze():
    data = request.get_json(force=True)
    code = data.get('code', '')
    opts = data.get('options', {})
    if not code.strip():
        return (jsonify({'error': 'No code provided'}), 400)
    default_seq = ['fold', 'prop', 'fold', 'dce', 'unreachable', 'dce', 'licm']
    pass_sequence = opts.get('sequence')
    if not pass_sequence:
        pass_sequence = []
        if opts.get('folding', True):
            pass_sequence.append('fold')
        if opts.get('propagation', True):
            pass_sequence.append('prop')
        if opts.get('folding', True):
            pass_sequence.append('fold')
        if opts.get('dce', True):
            pass_sequence.append('dce')
        if opts.get('unreachable', True):
            pass_sequence.append('unreachable')
        if opts.get('dce', True):
            pass_sequence.append('dce')
        pass_sequence.append('licm')
    result = run_pipeline(code, pass_sequence=pass_sequence)
    if result.parse_error:
        return (jsonify({'error': result.parse_error}), 422)
    blocks_before_data = []
    for bid, blk in sorted(result.blocks_before.items()):
        blocks_before_data.append({'id': bid, 'label': blk.label, 'instructions': [str(i) for i in blk.instructions]})
    before_map = {b['id']: b for b in blocks_before_data}
    graph_edges_before = {}
    if hasattr(result, 'graph_before') and result.graph_before:
        for src, dst, edata in result.graph_before.edges(data=True):
            kind = edata.get('label', 'fall')
            graph_edges_before.setdefault(src, []).append({'to': dst, 'kind': kind})
            graph_edges_before.setdefault(dst, []).append({'from': src, 'kind': kind})
    graph_edges = {}
    for src, dst, edata in result.graph.edges(data=True):
        kind = edata.get('label', 'fall')
        graph_edges.setdefault(src, []).append({'to': dst, 'kind': kind})
        graph_edges.setdefault(dst, []).append({'from': src, 'kind': kind})
    blocks_data = []
    for bid, blk in sorted(result.blocks.items()):
        blk_pre = result.blocks_pre_cleanup.get(bid, blk)
        instr_dicts = [{'text': str(i), 'original': i.original_text, 'type': i.opt_type} for i in blk.instructions if i.op != 'nop']
        opts_list = [{'text': str(i), 'original': i.original_text, 'type': i.opt_type} for i in blk_pre.instructions if i.opt_type]
        blocks_data.append({'id': bid, 'label': blk.label, 'instructions': instr_dicts, 'before_instructions': before_map.get(bid, {}).get('instructions', []), 'edges_before': graph_edges_before.get(bid, []), 'edges': graph_edges.get(bid, []), 'optimizations': opts_list, 'lv_in': sorted(blk.lv_in), 'lv_out': sorted(blk.lv_out)})
    loops_data = []
    for lp in result.loops:
        licm_texts = []
        for item in lp.licm_candidates:
            licm_texts.append(item[3] if len(item) == 4 else str(item[2]))
        loops_data.append({'header': lp.header, 'body': sorted(lp.body), 'back_edge': list(lp.back_edge), 'licm_count': len(lp.licm_candidates), 'licm': licm_texts})
    return jsonify({'dot_before': result.cfg_dot_before, 'dot_after': result.cfg_dot_after, 'blocks_before': blocks_before_data, 'blocks': blocks_data, 'stats': {'block_count': len(result.blocks), 'edge_count': result.graph.number_of_edges(), 'folded': result.folded, 'propagated': result.propagated, 'dead_removed': result.dead_removed, 'nops_removed': result.nops_removed, 'unreachable': len(result.unreachable_ids), 'elapsed_ms': round(result.elapsed_ms, 1)}, 'analysis': {'uninitialized': [{'block': b, 'var': v} for b, v in result.uninitialized_uses], 'dead_assignments': [{'block': b, 'instr': i, 'var': v} for b, i, v in result.dead_assignments]}, 'loops': loops_data, 'errors': result.errors})

@app.route('/api/render_dot', methods=['POST'])
def render_dot():
    import subprocess
    data = request.get_json(force=True)
    dot_src = data.get('dot', '')
    if not dot_src:
        return jsonify({'error': 'No dot source'}), 400
    try:
        result_proc = subprocess.run(['dot', '-Tsvg'], input=dot_src.encode(), capture_output=True, timeout=10)
        svg = result_proc.stdout.decode('utf-8', errors='replace')
        return jsonify({'svg': svg})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
