# ===== 第692课：源码分析与AST工具-NodeVisitor与符号收集 =====
# 知识点：
#   - ast.NodeVisitor：为每种节点类型定义 visit_XXX，自动分派遍历
#   - visit() 按节点类型查找 visit_ClassDef / visit_Name 等方法，未定义则 generic_visit
#   - 必须显式调用 self.generic_visit(node) 才会继续遍历子节点（最容易忘）
#   - 用「作用域栈」区分全局/函数/类作用域，收集定义与引用
#   - 读取 Name 时用 isinstance(node.ctx, ast.Load/Store) 判断读还是写
#   - 应用：未使用变量检测、未定义名检测、API 调用统计、复杂度估算
# 依赖：无（标准库）
import ast
from collections import defaultdict

SOURCE = '''\
import os
import json as js

GLOBAL = 10

def compute(a, b=2):
    tmp = a + b
    if tmp > GLOBAL:
        return tmp * FACTOR
    return helper(tmp)

class Processor:
    def run(self, data):
        return [transform(x) for x in data]
'''


class SymbolCollector(ast.NodeVisitor):
    def __init__(self):
        self.scopes = ["<module>"]
        self.defined = defaultdict(set)      # scope -> 定义的名字
        self.loaded = defaultdict(set)       # scope -> 读取的名字
        self.calls = []
        self.functions = []
        self.classes = []

    @property
    def scope(self):
        return self.scopes[-1]

    def visit_Module(self, node):
        self.generic_visit(node)             # 忘了这句就什么都不会遍历

    def visit_FunctionDef(self, node):
        self.defined[self.scope].add(node.name)
        self.functions.append((node.name, node.lineno, len(node.args.args)))
        self.scopes.append(node.name)
        for arg in node.args.args:
            self.defined[self.scope].add(arg.arg)
        self.generic_visit(node)
        self.scopes.pop()

    def visit_ClassDef(self, node):
        self.defined[self.scope].add(node.name)
        self.classes.append((node.name, node.lineno))
        self.scopes.append(node.name)
        self.generic_visit(node)
        self.scopes.pop()

    def visit_Assign(self, node):
        for t in node.targets:
            for n in ast.walk(t):
                if isinstance(n, ast.Name):
                    self.defined[self.scope].add(n.id)
        self.generic_visit(node)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self.loaded[self.scope].add(node.id)
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            self.calls.append((node.func.id, node.lineno))
        elif isinstance(node.func, ast.Attribute):
            self.calls.append((node.func.attr, node.lineno))
        self.generic_visit(node)


print("== 收集结果 ==")
c = SymbolCollector()
c.visit(ast.parse(SOURCE))
print("  函数:", c.functions)
print("  类  :", c.classes)
print("  调用:", c.calls)

print("\n== 各作用域的定义 ==")
for scope, names in c.defined.items():
    print(f"  {scope:<14}: {sorted(names)}")

print("\n== 各作用域读取但未在本作用域定义的名字 ==")
for scope, names in c.loaded.items():
    local = c.defined[scope]
    external = sorted(n for n in names if n not in local)
    print(f"  {scope:<14}: {external}")

print("\n== 全局视角：所有已定义名 ==")
all_defined = set().union(*c.defined.values()) if c.defined else set()
print("  ", sorted(all_defined))
print("  引用但从未定义（疑似 NameError）:")
import builtins
builtin_names = set(dir(builtins))
for scope, names in c.loaded.items():
    for n in sorted(names):
        if n not in all_defined and n not in builtin_names:
            print(f"    {scope}: {n}")

print("\n== 对比：忘掉 generic_visit 会怎样 ==")
class SkipAssignVisitor(ast.NodeVisitor):
    def __init__(self): self.calls = []
    def visit_Call(self, node):
        self.calls.append(ast.unparse(node.func))
        # 不调用 generic_visit -> 嵌套在 Call 里的子节点不会被访问

    def visit_Assign(self, node):
        pass                                 # 完全跳过赋值语句的子树

b = SkipAssignVisitor()
b.visit(ast.parse(SOURCE))
print("  跳过 Assign 子树后收集到的调用:", b.calls, "（明显不全）")
print("  正确做法：在 visit_XXX 末尾加 self.generic_visit(node)")

print("\n== Load / Store / Del 上下文 ==")
for snippet in ("x = 1", "print(x)", "del x", "x += 1"):
    t = ast.parse(snippet)
    ctxs = [(type(n.ctx).__name__, n.id) for n in ast.walk(t) if isinstance(n, ast.Name)]
    print(f"  {snippet:<12} -> {ctxs}")

print("\n== 常见应用 ==")
for line in (
    "  未使用变量: defined - loaded（注意 __all__ 与动态 getattr）",
    "  圈复杂度  : 数 If/For/While/Try/BoolOp 节点（第693课）",
    "  API 统计  : 数 Call 节点的 func 名，做升级影响面分析",
    "  死代码    : return 之后的语句、恒真/恒假条件",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 给 SymbolCollector 增加 async def / lambda / comprehension 的作用域处理。
# 2. 实现「未使用 import」检测：收集 Import 名与 Load 名做差集。
# 3. 用作用域链（而非扁平集合）正确解析嵌套函数里的自由变量。
# 4. 思考：为什么静态分析无法 100% 判断 getattr(obj, name) 这类动态引用？
