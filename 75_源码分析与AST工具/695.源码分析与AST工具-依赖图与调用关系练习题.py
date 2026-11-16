# ===== 第695课：源码分析与AST工具-依赖图与调用关系 =====
# 知识点：
#   - 从 AST 提取「模块 -> import 的模块」「函数 -> 调用的函数」两类边
#   - 调用图 Call Graph：节点是函数，边是调用关系；可查未定义调用、递归、孤立函数
#   - 环检测用 DFS 三色标记（白/灰/黑），能找出相互递归的强连通分量
#   - 传递闭包：从入口函数出发能到达哪些函数（影响面分析）
#   - 与第641课 DAG 对比：调用图允许环（递归），DAG 不允许
#   - 局限：getattr / 动态分发 / 高阶函数无法静态确定，需保守处理
# 依赖：无（标准库）
import ast
from collections import defaultdict, deque

SOURCE = '''\
import os
import json
from pathlib import Path

def load(path):
    return json.loads(Path(path).read_text())

def clean(data):
    return [normalize(x) for x in data if x]

def normalize(x):
    return x.strip().lower()

def pipeline(path):
    raw = load(path)
    cleaned = clean(raw)
    return summarize(cleaned)

def summarize(items):
    return report(len(items))

def report(n):
    return f"count={n}"

def recursive(n):
    if n <= 1:
        return 1
    return n * recursive(n - 1)

def mutually_a(n):
    return mutually_b(n - 1)

def mutually_b(n):
    return mutually_a(n + 1)

def unused_helper():
    return 42
'''


def build_call_graph(source):
    tree = ast.parse(source)
    funcs, calls, imports = set(), defaultdict(set), set()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            funcs.add(node.name)
        elif isinstance(node, ast.Import):
            imports.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    for fn in (n for n in tree.body if isinstance(n, ast.FunctionDef)):
        for sub in ast.walk(fn):
            if isinstance(sub, ast.Call):
                if isinstance(sub.func, ast.Name) and sub.func.id in funcs:
                    calls[fn.name].add(sub.func.id)
    return funcs, dict(calls), imports


funcs, call_graph, imports = build_call_graph(SOURCE)
print("== 函数集合 ==")
print("  ", sorted(funcs))
print("  import 的顶层模块:", sorted(imports))

print("\n== 调用图 ==")
for f in sorted(funcs):
    print(f"  {f:<16} -> {sorted(call_graph.get(f, ()))}")

print("\n== 入口 / 出口 / 孤立函数 ==")
called = set().union(*call_graph.values()) if call_graph else set()
entries = sorted(funcs - called)
leaves = sorted(f for f in funcs if not call_graph.get(f))
print("  未被任何函数调用（可能是入口）:", entries)
print("  不调用其他函数（叶子）:", leaves)
print("  真正的孤立函数需结合可达性分析判断（见下）")

print("\n== 可达性：从 pipeline 出发 ==")
def reachable(start, graph):
    seen, q = set(), deque([start])
    while q:
        cur = q.popleft()
        if cur in seen: continue
        seen.add(cur)
        q.extend(graph.get(cur, ()))
    return seen
reach = reachable("pipeline", call_graph)
print("  可达:", sorted(reach))
print("  不可达（死代码候选）:", sorted(funcs - reach))

print("\n== 自递归检测 ==")
self_recursive = sorted(f for f in funcs if f in call_graph.get(f, ()))
print("  ", self_recursive)

print("\n== 环检测（DFS 三色标记）==")
def find_cycles(graph, nodes):
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {n: WHITE for n in nodes}
    cycles, stack = [], []
    def dfs(n):
        color[n] = GRAY; stack.append(n)
        for m in sorted(graph.get(n, ())):
            if color.get(m, WHITE) == GRAY:
                idx = stack.index(m)
                cycles.append(stack[idx:] + [m])
            elif color.get(m, WHITE) == WHITE:
                dfs(m)
        stack.pop(); color[n] = BLACK
    for n in sorted(nodes):
        if color[n] == WHITE:
            dfs(n)
    return cycles

for c in find_cycles(call_graph, funcs):
    print("  环:", " -> ".join(c))

print("\n== 反向图：谁会受影响 ==")
reverse = defaultdict(set)
for a, targets in call_graph.items():
    for b in targets:
        reverse[b].add(a)
for f in ("load", "normalize", "report"):
    print(f"  改 {f:<12} 会直接影响: {sorted(reverse.get(f, ()))}")
# 传递影响（反向可达）
def affected(target):
    return reachable(target, dict(reverse))
print("  改 report 的传递影响面:", sorted(affected("report")))

print("\n== 调用图 vs DAG（第641课）==")
for line in (
    "  调用图允许环：递归、互相递归都很常见",
    "  任务 DAG 必须无环，否则无法拓扑排序",
    "  两者都要做可达性/影响面分析，算法相通",
    "  静态调用图是「近似」：dynamic dispatch 会漏边",
):
    print(" ", line)

print("\n== 动态性带来的盲区 ==")
for line in [
    "  getattr(obj, name)(...) 无法静态知道 name",
    "  函数作为参数传入（map/filter/回调）会丢失边",
    "  跨模块调用需把多个文件的图合并",
    "  结论：当作「下界」用，别当成完整事实",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 合并多个 .py 文件的调用图，支持 module.func 形式的跨模块调用。
# 2. 用 Tarjan 算法求强连通分量，替代本例的简单环检测。
# 3. 计算每个函数的「扇入/扇出」，找出最需要重点关注的核心节点。
# 4. 思考：为什么静态调用图只能作为下界，动态语言里哪些写法会漏边？
