from __future__ import annotations
import os
from typing import Dict, Optional
import networkx as nx
from cfg.basic_block import BasicBlock
_HEADER_BG = {'entry': ('#0d3d2b', '#2ecc71'), 'exit': ('#3d0d0d', '#e74c3c'), 'func': ('#0d1f3d', '#5dade2'), 'dead': ('#1a1a1a', '#7f8c8d'), 'preheader': ('#1f0d3d', '#a855f7'), 'default': ('#0d1a2e', '#94a3b8')}
_OPT_ROW = {'Folded': ('#2d1f00', '#f59e0b'), 'Propagated': ('#0d2d1f', '#10b981'), 'Removed': ('#2d0d0d', '#ef4444'), 'Moved': ('#1f0d2d', '#a855f7')}
_DEFAULT_ROW_BG = '#0a1628'
_DEFAULT_ROW_FG = '#93c5fd'
_EDGE_COLOUR = {'true': '#27ae60', 'false': '#e74c3c', 'back': '#9b59b6', 'return': '#e67e22', 'call': '#3498db', 'break': '#e74c3c', 'continue': '#16a085', 'fall': '#4a5568', 'default': '#4a5568'}
_OPT_BADGE = {'Folded': '⚡FOLD', 'Propagated': '→PROP', 'Removed': '✂ DCE', 'Moved': '⬆LICM'}

def _header_colours(blk: BasicBlock):
    label = blk.label.lower()
    for key, colours in _HEADER_BG.items():
        if key in label:
            return colours
    return _HEADER_BG['default']

def _html_escape(text: str) -> str:
    """Escape text for embedding inside a Graphviz HTML label."""
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')

def _dot_escape(text: str) -> str:
    """Escape text for embedding inside a plain DOT string attribute."""
    return text.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')

def _make_html_label(blk: BasicBlock) -> str:
    """
    Build a Graphviz HTML table label for a basic block.
    Each instruction gets its own row. Optimized instructions are
    colour-coded with a badge, making the transformation immediately visible.
    """
    hdr_bg, hdr_fg = _header_colours(blk)
    title = f'Block {blk.id}'
    if blk.label:
        title += f'  [{_html_escape(blk.label)}]'
    rows = []
    rows.append(f'<TR><TD COLSPAN="2" BGCOLOR="{hdr_bg}" ALIGN="LEFT" CELLPADDING="5"><FONT FACE="Courier New" COLOR="{hdr_fg}"><B>{_html_escape(title)}</B></FONT></TD></TR>')
    rows.append(f'<TR><TD COLSPAN="2" BGCOLOR="#1a2540" HEIGHT="1" CELLPADDING="0"></TD></TR>')
    if not blk.instructions:
        rows.append(f'<TR><TD COLSPAN="2" BGCOLOR="{_DEFAULT_ROW_BG}" ALIGN="LEFT" CELLPADDING="4"><FONT FACE="Courier New" COLOR="#4a5568"><I>(empty)</I></FONT></TD></TR>')
    else:
        for instr in blk.instructions:
            s = str(instr).strip()
            if s == 'nop':
                c_text = '/* nop */'
            elif s.startswith('return'):
                c_text = s.replace('return ', 'return ') + ';' if ' ' in s else 'return;'
            elif s.startswith('goto '):
                c_text = s + ';'
            elif s.startswith('if '):
                import re
                m = re.match('^if\\s+(.+?)\\s+goto\\s+(\\S+)\\s+else\\s+goto\\s+(\\S+)$', s)
                c_text = f'if ({m.group(1)}) goto {m.group(2)}; else goto {m.group(3)};' if m else s + ';'
            elif s.startswith('[label:'):
                c_text = s[8:-1].strip() + ':'
            elif ' = call ' in s:
                import re
                m = re.match('^(\\S+)\\s*=\\s*call\\s+(\\S+)\\(([^)]*)\\)$', s)
                c_text = f'{m.group(1)} = {m.group(2)}({m.group(3)});' if m else s + ';'
            elif s.startswith('param '):
                c_text = f'/* param {s[6:]} */'
            elif '=' in s:
                import re
                m = re.match('^(\\S+)\\s*=\\s*(.+)$', s)
                if m:
                    lhs = m.group(1)
                    rhs = m.group(2).strip()
                    if lhs.startswith('_t') and ' ' not in rhs and (not instr.opt_type):
                        continue
                    c_text = f'{lhs} = {rhs};'
                else:
                    c_text = s + ';'
            else:
                c_text = s + ';'
            text = _html_escape(c_text)
            opt = instr.opt_type
            if opt and opt in _OPT_ROW:
                row_bg, row_fg = _OPT_ROW[opt]
                badge = _html_escape(_OPT_BADGE.get(opt, opt))
                badge_cell = f'<TD BGCOLOR="{row_bg}" ALIGN="CENTER" CELLPADDING="3" WIDTH="42"><FONT FACE="Courier New" POINT-SIZE="8" COLOR="{row_fg}"><B>{badge}</B></FONT></TD>'
                instr_cell = f'<TD BGCOLOR="{row_bg}" ALIGN="LEFT" CELLPADDING="3"><FONT FACE="Courier New" COLOR="{row_fg}">{text}</FONT></TD>'
            else:
                badge_cell = f'<TD BGCOLOR="{_DEFAULT_ROW_BG}" CELLPADDING="3" WIDTH="42"></TD>'
                instr_cell = f'<TD BGCOLOR="{_DEFAULT_ROW_BG}" ALIGN="LEFT" CELLPADDING="3"><FONT FACE="Courier New" COLOR="{_DEFAULT_ROW_FG}">{text}</FONT></TD>'
            rows.append(f'<TR>{badge_cell}{instr_cell}</TR>')
    table = '<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="0" BGCOLOR="#0a1628">' + ''.join(rows) + '</TABLE>>'
    return table

def cfg_to_dot(graph: nx.DiGraph, blocks: Dict[int, BasicBlock], title: str='Control Flow Graph', show_dataflow: bool=False) -> str:
    lines = ['digraph CFG {', f'    label="{_dot_escape(title)}";', '    labelloc="t";', '    fontname="Helvetica";', '    fontsize=13;', '    bgcolor="#080b12";', '    node [shape=plaintext, fontname="Courier New", fontsize=10];', '    edge [fontname="Helvetica", fontsize=9, penwidth=1.5];', '    rankdir=TB;', '    splines=ortho;', '    nodesep=0.6;', '    ranksep=0.8;', '']
    for node_id in graph.nodes:
        blk = blocks.get(node_id)
        if blk is None:
            continue
        html_label = _make_html_label(blk)
        lines.append(f'    node_{node_id} [label={html_label}, tooltip="Block {node_id}"];')
    lines.append('')
    for src, dst, data in graph.edges(data=True):
        kind = data.get('label', '')
        colour = _EDGE_COLOUR.get(kind, _EDGE_COLOUR['default'])
        attrs = f'color="{colour}", fontcolor="{colour}"'
        if kind:
            attrs += f', label="  {kind}  "'
        if kind == 'back':
            attrs += ', style=dashed, constraint=false'
        if kind in ('true', 'false'):
            attrs += ', penwidth=2.0'
        lines.append(f'    node_{src} -> node_{dst} [{attrs}];')
    lines.append('}')
    return '\n'.join(lines)

def render_cfg(dot_source: str, output_path: str, fmt: str='png') -> Optional[str]:
    try:
        import graphviz as gv
        base, _ = os.path.splitext(output_path)
        src = gv.Source(dot_source)
        rendered = src.render(filename=base, format=fmt, cleanup=True, quiet=True)
        return rendered
    except Exception:
        dot_path = output_path.replace('.' + fmt, '.dot')
        if not dot_path.endswith('.dot'):
            dot_path = output_path + '.dot'
        with open(dot_path, 'w', encoding='utf-8') as f:
            f.write(dot_source)
        return dot_path

def save_dot(dot_source: str, path: str) -> str:
    with open(path, 'w', encoding='utf-8') as f:
        f.write(dot_source)
    return path