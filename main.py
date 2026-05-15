from __future__ import annotations
import sys, io
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import argparse, os, textwrap

def run_cli(c_code: str, out_dir: str='.') -> None:
    from pipeline import run_pipeline
    from cfg.visualizer import save_dot
    print('\n[*] Running CS202 C Optimizer Pipeline...\n')
    result = run_pipeline(c_code)
    if result.parse_error:
        print(f'[ERROR] Parse Error: {result.parse_error}')
        sys.exit(1)
    print(result.summary())
    if result.uninitialized_uses:
        print('\n[WARN] Uninitialized Variable Uses:')
        for blk_id, var in result.uninitialized_uses:
            print(f"    Block {blk_id}: variable '{var}' may be uninitialized")
    else:
        print('\n[OK] No uninitialized variable uses detected.')
    if result.dead_assignments:
        print('\n💀  Dead Assignments:')
        for blk_id, idx, var in result.dead_assignments:
            print(f"    Block {blk_id}[instr {idx}]: assignment to '{var}' is dead")
    else:
        print('✅  No dead assignments.')
    if result.loops:
        print(f'\n[LOOPS] Loops detected: {len(result.loops)}')
        for i, lp in enumerate(result.loops, 1):
            print(f'    Loop {i}: header=Block {lp.header}, body={sorted(lp.body)}, back-edge={lp.back_edge}')
            if lp.licm_candidates:
                print(f'      [LICM] candidates ({len(lp.licm_candidates)}):')
                for bid, idx, instr in lp.licm_candidates:
                    print(f'         Block {bid}[{idx}]: {instr}')
    os.makedirs(out_dir, exist_ok=True)
    before_path = os.path.join(out_dir, 'cfg_before.dot')
    after_path = os.path.join(out_dir, 'cfg_after.dot')
    save_dot(result.cfg_dot_before, before_path)
    save_dot(result.cfg_dot_after, after_path)
    print(f'\n[DOT] DOT files saved:')
    print(f'    Before: {before_path}')
    print(f'    After:  {after_path}')
    from cfg.visualizer import render_cfg
    png_path = render_cfg(result.cfg_dot_after, os.path.join(out_dir, 'cfg_after.png'))
    if png_path and png_path.endswith('.png'):
        print(f'    PNG:    {png_path}')
    else:
        print('    (Install Graphviz binary to render PNGs)')
    if result.errors:
        print(f'\n[WARN] Pipeline warnings:')
        for e in result.errors:
            print(f'    {e}')

def main():
    parser = argparse.ArgumentParser(description='CS202 C Compiler Optimizer', formatter_class=argparse.RawDescriptionHelpFormatter, epilog='')
    parser.add_argument('file', nargs='?', help='C source file to analyze')
    parser.add_argument('--web', action='store_true', help='Launch web dashboard')
    parser.add_argument('--out', default='output', help='Output directory (default: output)')
    args = parser.parse_args()
    if args.web:
        print('[WEB] Starting web dashboard at http://localhost:5000')
        from app import app
        app.run(debug=False, port=5000)
        return
    if args.file:
        if not os.path.isfile(args.file):
            print(f'[ERROR] File not found: {args.file}')
            sys.exit(1)
        with open(args.file, 'r', encoding='utf-8') as f:
            code = f.read()
        run_cli(code, out_dir=args.out)
        return
    parser.print_help()
if __name__ == '__main__':
    main()