# -*- coding: cp936 -*-
"""列出源码的顶层函数/类及各段行数，用于判断结构"""
import ast
import io
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

path = sys.argv[1]
src = io.open(path, encoding='utf-8').read()
tree = ast.parse(src)
lines = src.split('\n')

items = []
for node in tree.body:
    if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
        end = getattr(node, 'end_lineno', node.lineno)
        items.append((node.lineno, node.name, 'class' if isinstance(node, ast.ClassDef) else 'def', end - node.lineno + 1))

print('total lines = %d' % len(lines))
print('top-level defs = %d' % len(items))
print('%-6s %-42s %-6s %s' % ('line', 'name', 'kind', 'len'))
for ln, name, kind, size in items:
    print('%-6d %-42s %-6s %d' % (ln, name, kind, size))

# 类内部方法
for node in tree.body:
    if isinstance(node, ast.ClassDef):
        print('\n--- class %s (line %d) ---' % (node.name, node.lineno))
        for sub in node.body:
            if isinstance(sub, ast.FunctionDef):
                print('  %-40s line %d' % (sub.name, sub.lineno))
