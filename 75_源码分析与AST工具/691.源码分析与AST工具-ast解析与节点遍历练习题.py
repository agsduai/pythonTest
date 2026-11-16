# ===== 第691课：源码分析与AST工具-ast解析与节点遍历 =====
# 知识点：
#   - ast.parse(source) 把源码解析成抽象语法树；ast.dump() 查看结构
#   - 节点类型：Module / FunctionDef / Assign / Call / Name / Constant / BinOp 等
#   - 每个节点带 lineno / col_offset / end_lineno / end_col_offset（位置信息）
#   - ast.walk 深度优先遍历全部节点；ast.iter_child_nodes 只看直接子节点
#   - ast.literal_eval 安全求值字面量，绝不用 eval 处理不可信输入
#   - 语法错误抛 SyntaxError，可用 try/except 给出友好提示
# 依赖：无（标准库）
import ast

SOURCE = '''\
import math

PI = 3.14159

def area(r):
    """计算圆面积"""
    return PI * r ** 2

class Circle:
    def __init__(self, radius):
        self.radius = radius

    def size(self):
        return area(self.radius)

result = area(2)
print(result)
'''

print("== ast.parse 与 dump ==")
tree = ast.parse(SOURCE)
print("  根节点:", type(tree).__name__, "| 顶层语句数:", len(tree.body))
print("  dump 前 240 字符:")
print("   ", ast.dump(tree, indent=2)[:240].replace("\n", "\n    "))

print("\n== 顶层语句清单 ==")
for node in tree.body:
    extra = ""
    if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
        extra = f" name={node.name!r}"
    elif isinstance(node, ast.Assign):
        extra = f" targets={[ast.unparse(t) for t in node.targets]}"
    elif isinstance(node, (ast.Import, ast.ImportFrom)):
        extra = f" names={[a.name for a in node.names]}"
    print(f"  L{node.lineno:<3} {type(node).__name__:<16}{extra}")

print("\n== 位置信息 ==")
for node in tree.body:
    print(f"  {type(node).__name__:<16} L{node.lineno}:{node.col_offset} "
          f"-> L{node.end_lineno}:{node.end_col_offset}")

print("\n== ast.walk 全量遍历（计数）==")
from collections import Counter
counts = Counter(type(n).__name__ for n in ast.walk(tree))
for name, n in counts.most_common(12):
    print(f"  {name:<20} {n}")

print("\n== iter_child_nodes 只看直接子节点 ==")
fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef))
print("  FunctionDef(area) 的直接子节点:", [type(c).__name__ for c in ast.iter_child_nodes(fn)])
print("  ast.walk 的子孙数:", len(list(ast.walk(fn))))

print("\n== literal_eval 安全求值 ==")
for expr in ("[1, 2, 3]", "{'a': 1, 'b': (2, 3)}", "1 + 2", "__import__('os')"):
    try:
        print(f"  {expr:<28} -> {ast.literal_eval(expr)!r}")
    except (ValueError, SyntaxError) as e:
        print(f"  {expr:<28} -> 拒绝: {type(e).__name__}")
print("  literal_eval 只接受字面量，不执行表达式/函数调用")

print("\n== 语法错误处理 ==")
for bad in ("def f(:", "x = (1", "return 1", "if True\n  pass"):
    try:
        ast.parse(bad)
        print(f"  {bad!r:<20} 通过")
    except SyntaxError as e:
        print(f"  {bad!r:<20} -> SyntaxError: {e.msg} (line {e.lineno}, offset {e.offset})")

print("\n== type_comments 与 feature_version ==")
print("  ast.parse(src, type_comments=True) 会解析 # type: 注释")
print("  ast.parse(src, feature_version=(3, 10)) 按旧版语法解析（如 match 之前）")
modern = ast.parse("x = 1  # type: int", type_comments=True)
print("  带类型注释的 Assign.type_comment:", modern.body[0].type_comment)
print("  注意：变量注解 `x: int` 与 `# type:` 注释不能同时写，二选一")

print("\n== AST 分析 vs 文本正则 ==")
for line in (
    "  正则容易被注释、字符串、多行写法骗过；AST 只看真实语法结构",
    "  AST 保留位置信息，可以精确报「第几行第几列」",
    "  Python 3.9+ 的 ast.unparse 可把 AST 还原成源码（第696课）",
    "  静态分析/linter/自动重构/代码生成都建立在 AST 之上",
):
    print(line)

# ===== 练习题 =====
# 1. 统计一段源码里所有字符串常量及其所在行号。
# 2. 用 ast.walk 找出所有 import 的模块名，区分 import 与 from...import。
# 3. 比较正则 `\bdef\s+(\w+)` 与 AST 在「注释里写 def」场景下的差异。
# 4. 思考：为什么 ast.literal_eval 比 eval 安全，但仍不该处理超大输入？
