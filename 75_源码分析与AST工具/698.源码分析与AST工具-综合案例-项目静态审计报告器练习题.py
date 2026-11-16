# ===== 第698课：源码分析与AST工具-综合案例-项目静态审计报告器 =====
# 知识点：
#   - 综合串起本章：parse / NodeVisitor / 度量 / Transformer / 调用图 / unparse / linter
#   - 扫描一个目录下的 .py，逐文件产出结构化指标，汇总成审计报告
#   - 分析维度：规模（文件/函数/行数）、复杂度、规则问题、调用图、依赖
#   - 全部用内存字符串 + TemporaryDirectory 构造样本项目，不依赖外部代码
#   - 报告输出为文本 + JSON 两种格式（第665课多格式渲染思路）
#   - 纯函数 analyze_project(files) 可单测、可缓存、可接入 CI
# 依赖：无（标准库）
import ast
import json
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

FILES = {
    "models.py": '''\
from dataclasses import dataclass

@dataclass
class User:
    name: str
    age: int

    def is_adult(self):
        return self.age >= 18
''',
    "service.py": '''\
import logging
from models import User

def create(name, age):
    if age < 0:
        raise ValueError(age)
    return User(name, age)

def batch(names, ages):
    result = []
    for n, a in zip(names, ages):
        try:
            result.append(create(n, a))
        except ValueError:
            logging.warning("skip %s", n)
    return result

def unused():
    x = 1
    return 42
''',
    "app.py": '''\
from service import batch

def main():
    users = batch(["a", "b"], [20, 30])
    print(len(users))
    return users

if __name__ == "__main__":
    main()
''',
}


# ---- 各分析器 ----
class Collector(ast.NodeVisitor):
    def __init__(self):
        self.functions, self.classes, self.imports = [], [], []
        self.decisions = 0
        self.issues = []
        self._func = None
        self._defined = []

    def visit_Import(self, node):
        self.imports.extend(a.name for a in node.names)
    def visit_ImportFrom(self, node):
        if node.module:
            self.imports.append(node.module)

    def visit_ClassDef(self, node):
        self.classes.append(node.name)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self.functions.append(node.name)
        self._func = node.name
        self._defined = [a.arg for a in node.args.args]
        for d in node.args.defaults:
            if isinstance(d, (ast.List, ast.Dict, ast.Set)):
                self.issues.append((node.lineno, "MUTABLE_DEFAULT", node.name))
        self.generic_visit(node)
        self._func = None

    def visit_Assign(self, node):
        if self._func:
            for t in node.targets:
                for n in ast.walk(t):
                    if isinstance(n, ast.Name):
                        self._defined.append(n.id)
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id == "print":
            self.issues.append((node.lineno, "PRINT_CALL", ""))
        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        if node.type is None:
            self.issues.append((node.lineno, "BARE_EXCEPT", ""))
        self.generic_visit(node)

    def visit_Global(self, node):
        self.issues.append((node.lineno, "GLOBAL_STMT", ""))
        self.generic_visit(node)


def analyze_file(name, source):
    tree = ast.parse(source)
    c = Collector()
    c.visit(tree)
    lines = source.splitlines()
    code_lines = [l for l in lines if l.strip() and not l.strip().startswith("#")]
    # 圈复杂度：全文件判定节点数 + 1
    decisions = sum(1 for n in ast.walk(tree)
                    if isinstance(n, (ast.If, ast.For, ast.While, ast.IfExp,
                                      ast.Try, ast.With)))
    decisions += sum(len(n.values) - 1 for n in ast.walk(tree) if isinstance(n, ast.BoolOp))
    decisions += sum(len(n.handlers) for n in ast.walk(tree) if isinstance(n, ast.Try))
    return {
        "file": name,
        "total_lines": len(lines),
        "code_lines": len(code_lines),
        "functions": c.functions,
        "classes": c.classes,
        "imports": sorted(set(c.imports)),
        "complexity": decisions + 1,
        "issues": [{"line": l, "rule": r, "target": t} for l, r, t in c.issues],
    }


def build_call_graph(files):
    graph, all_funcs = defaultdict(set), set()
    for src in files.values():
        all_funcs.update(n.name for n in ast.walk(ast.parse(src))
                         if isinstance(n, ast.FunctionDef))
    for src in files.values():
        for fn in (n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.FunctionDef)):
            for sub in ast.walk(fn):
                if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name):
                    if sub.func.id in all_funcs:
                        graph[fn.name].add(sub.func.id)
    return {k: sorted(v) for k, v in graph.items()}


def analyze_project(files):
    reports = [analyze_file(n, s) for n, s in sorted(files.items())]
    graph = build_call_graph(files)
    summary = {
        "files": len(reports),
        "total_lines": sum(r["total_lines"] for r in reports),
        "code_lines": sum(r["code_lines"] for r in reports),
        "functions": sum(len(r["functions"]) for r in reports),
        "classes": sum(len(r["classes"]) for r in reports),
        "total_complexity": sum(r["complexity"] for r in reports),
        "issues": sum(len(r["issues"]) for r in reports),
        "imports": sorted({m for r in reports for m in r["imports"]}),
    }
    return {"summary": summary, "files": reports, "call_graph": graph}


def render(result):
    s = result["summary"]
    out = [
        "=" * 60,
        "项目静态审计报告",
        "=" * 60,
        f"文件 {s['files']} | 总行 {s['total_lines']} | 代码行 {s['code_lines']} | "
        f"函数 {s['functions']} | 类 {s['classes']}",
        f"总圈复杂度 {s['total_complexity']} | 规则问题 {s['issues']}",
        f"外部/内部依赖: {', '.join(s['imports'])}",
        "-" * 60,
    ]
    for r in result["files"]:
        out.append(f"  {r['file']:<16} 行={r['total_lines']:<4} 复杂度={r['complexity']:<3} "
                   f"函数={r['functions']} 类={r['classes']}")
        for i in r["issues"]:
            out.append(f"      L{i['line']} [{i['rule']}] {i['target']}")
    out += ["-" * 60, "调用图:"]
    for f, targets in sorted(result["call_graph"].items()):
        out.append(f"  {f:<12} -> {targets}")
    out += ["=" * 60]
    return "\n".join(out)


result = analyze_project(FILES)
print(render(result))

print("\n== JSON 输出（便于 CI 消费）==")
doc = json.dumps(result, ensure_ascii=False, indent=2)
print(f"  {len(doc)} 字符，前 200:", doc[:200].replace("\n", " "), "...")

print("\n== 热点文件（按复杂度）==")
for r in sorted(result["files"], key=lambda x: -x["complexity"]):
    print(f"  {r['file']:<16} 复杂度={r['complexity']}")

print("\n== 规则问题按类型 ==")
cnt = Counter(i["rule"] for r in result["files"] for i in r["issues"])
print("  ", dict(cnt) or "无")

print("\n== 用 Transformer 自动修复 print ==")
class RemovePrint(ast.NodeTransformer):
    def visit_Expr(self, node):
        self.generic_visit(node)
        if (isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name)
                and node.value.func.id == "print"):
            return None
        return node

fixed = ast.unparse(RemovePrint().visit(
    ast.fix_missing_locations(ast.parse(FILES["app.py"]))))
print(fixed)
print("  修复后 app.py 的 PRINT_CALL 数:",
      len(analyze_file("app.py", fixed)["issues"]))

print("\n== 落盘与重载 ==")
with tempfile.TemporaryDirectory() as tmp:
    p = Path(tmp) / "report.json"
    p.write_text(json.dumps(result, ensure_ascii=False, indent=2), "utf-8")
    loaded = json.loads(p.read_text("utf-8"))
    print(f"  {p.name}: {p.stat().st_size} 字节，文件数={loaded['summary']['files']}")
    print("  重载后摘要一致:", loaded["summary"] == result["summary"])

print("\n== 流水线回顾 ==")
for line in [
    "  parse       : 每个文件解析成 AST（第691课）",
    "  Visitor     : 收集符号/调用/问题（第692/697课）",
    "  Metrics     : 行数与圈复杂度（第693课）",
    "  CallGraph   : 跨文件调用边与影响面（第695课）",
    "  Transformer : 自动修复并 unparse 验证（第694/696课）",
    "  Render      : 文本 + JSON 双格式报告（第665课）",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 增加「每函数」而非「每文件」的复杂度列，精确到行号范围。
# 2. 实现基线对比：与上次报告 diff，只报新增问题。
# 3. 用多进程扫描真实大项目，注意 AST 对象不可直接跨进程序列化。
# 4. 思考：为什么静态审计报告要同时给「机器可读 JSON」与「人可读文本」？
