#!/usr/bin/env python3
"""Extract pure motors from Commands/Gates/*.py into a standalone gates/ package.
Drops Telegram-bot handlers (gateCmd, callbacks) and any _template import."""
import ast
import pathlib
import re
import sys

SRC = pathlib.Path('Commands/Gates')
DST = pathlib.Path('gates')

# Top-level function names to DROP (bot handlers / builders). Keep everything else.
DROP_PREFIX = ('gateCmd', 'clb', 'tcl_monto_cb', 'ps_monto_cb', 'zb_monto_cb')
DROP_PREFIX = ('gateCmd', 'clb', 'mcgenerator')


def is_bot_func(name: str) -> bool:
    n = name.strip()
    if n == 'cmdCookieGen' or n == 'clbCookieGen' or n == 'clbSaveCookie' or n == '_execute':
        return True
    if n.startswith('gateCmd') or n.startswith('clb') or n.startswith('cmd'):
        return True
    if n in ('_checker_p', 'run_co_log'):
        return True
    return False


def has_bot_param(node: ast.FunctionDef) -> bool:
    for a in node.args.args + node.args.posonlyargs:
        if a.arg in ('bot', 'update', 'gestion'):
            return True
    return False


def transform(src: pathlib.Path) -> str:
    text = src.read_text(encoding='utf-8')
    tree = ast.parse(text)
    kept = []
    for node in tree.body:
        # imports/constants/classes/assignments pass through
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            # drop _template import (brings no bot dep, but pure pkg should not need it)
            if isinstance(node, ast.ImportFrom) and (node.module or '').endswith('_template'):
                continue
            kept.append(node)
            continue
        if isinstance(node, ast.FunctionDef):
            if is_bot_func(node.name) or has_bot_param(node):
                continue
            kept.append(node)
            continue
        kept.append(node)
    out = '\n\n'.join(ast.unparse(n) for n in kept)
    # rebuild header
    header = "# Pure gate motor for '%s' — no Telegram-bot dependency.\n" % src.stem
    return header + '\n' + out


def main():
    DST.mkdir(exist_ok=True)
    for py in sorted(SRC.glob('*.py')):
        if py.name in ('_template.py', 'main.py', '__init__.py', 'telcel.py', 'telcel_core.py'):
            continue
        try:
            code = transform(py)
            (DST / py.name).write_text(code, encoding='utf-8')
            print(f'{py.name}: OK     ({len(code)} bytes)')
        except Exception as e:
            print(f'{py.name}: SKIP   {type(e).__name__}: {e}')


if __name__ == '__main__':
    main()