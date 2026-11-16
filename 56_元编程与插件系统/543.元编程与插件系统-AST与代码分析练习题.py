# ===== 第543课：元编程与插件系统-AST与代码分析 =====
# 知识点：
#   - AST（抽象语法树）：Python 源码解析后的树结构，工具链的基础
#   - ast.parse 把源码变成树；ast.walk 遍历所有节点
#   - 可做静态检查：危险函数（eval/exec）、裸 except、未使用导入、命名规范
#   - ast.unparse 把节点转回源码（3.9+），方便展示与改写
#   - 与第218课代码规范、第472课 Git Hooks 的配合：提交前跑 AST 检查
#   - 真实工具：ruff、mypy、black 内部都大量使用 AST
# 依赖：无（标准库 ast）

import ast

CODE = '''
import os
import sys

def add(a, b):
    return a + b

def unsafe(user_input):
    result = eval(user_input)
    exec("print('hi')")
    return result

def risky():
    try:
        return 1 / 0
    except:
        pass
'''

tree = ast.parse(CODE)

print("== 顶层结构 ==")
for node in tree.body:
    print(f"  {type(node).__name__}: {getattr(node, 'name', '')}")

print("\n== 函数列表 ==")
functions = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
for fn in functions:
    args = [a.arg for a in fn.args.args]
    print(f"  {fn.name}({', '.join(args)}) | 行号 {fn.lineno}")

print("\n== 导入 ==")
for node in ast.walk(tree):
    if isinstance(node, ast.Import):
        for alias in node.names:
            print(f"  import {alias.name}")
    elif isinstance(node, ast.ImportFrom):
        print(f"  from {node.module} import ...")


# ---------------- 简易静态检查器 ----------------
def lint(code: str) -> list[dict]:
    tree = ast.parse(code)
    issues = []
    imported = set()
    used = set()

    for node in ast.walk(tree):
        # 危险函数
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in ("eval", "exec", "compile", "__import__"):
                issues.append({"line": node.lineno, "rule": "dangerous-call",
                               "msg": f"避免使用 {node.func.id}()"})
        # 裸 except
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            issues.append({"line": node.lineno, "rule": "bare-except",
                           "msg": "不要用裸 except，至少捕获 Exception"})
        # 导入与使用
        if isinstance(node, ast.Name):
            used.add(node.id)
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.asname or alias.name.split(".")[0])

    for name in sorted(imported - used):
        issues.append({"line": 1, "rule": "unused-import",
                       "msg": f"导入 {name} 但未使用"})

    return issues


print("\n== AST 检查结果 ==")
for issue in lint(CODE):
    print(f"  行{issue['line']:2d} [{issue['rule']}] {issue['msg']}")

# ---- 正常代码不应有告警 ----
CLEAN_CODE = '''
def greet(name: str) -> str:
    return f"你好，{name}"

print(greet("小明"))
'''
print("\n== 检查正常代码 ==")
issues = lint(CLEAN_CODE)
print("  问题数：", len(issues))

# ---- 用 AST 做代码改写（示例） ----
print("\n== AST 改写：把 print 替换成 logging ==")
class RewritePrint(ast.NodeTransformer):
    def visit_Call(self, node):
        self.generic_visit(node)
        if isinstance(node.func, ast.Name) and node.func.id == "print":
            node.func.id = "logger.info"
        return node


small = "print('hello')\n"
new_tree = RewritePrint().visit(ast.parse(small))
ast.fix_missing_locations(new_tree)
print("  改写前：", small.strip())
print("  改写后：", ast.unparse(new_tree))

# ---- AST 的边界 ----
print("\n== 注意事项 ==")
for item in [
    "AST 只做静态分析，不执行代码（比 import 安全）",
    "动态特性（getattr/exec）会让静态分析漏报",
    "改写代码要保留行号（fix_missing_locations），否则报错难定位",
    "生产级检查用 ruff/mypy，不要自己造全套轮子",
    "Git Hooks 里跑 AST 检查，可以阻止危险代码入库（第472课）",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 增加规则：函数超过 30 行告警。
# 2. 增加规则：函数名不是 snake_case 告警。
# 3. 用 AST 统计每个函数的复杂度（分支数）。
# 4. 思考：为什么 AST 检查无法发现“运行时才出现”的 bug？
