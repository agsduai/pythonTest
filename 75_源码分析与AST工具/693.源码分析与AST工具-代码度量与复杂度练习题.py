# ===== 第693课：源码分析与AST工具-代码度量与复杂度 =====
# 知识点：
#   - 圈复杂度 Cyclomatic Complexity：判定节点数 + 1，衡量分支路径数量
#   - 判定节点：If / For / While / Try(每 except) / BoolOp / IfExp / comprehension 的 if
#   - 可维护性指数、Halstead 体积、嵌套深度、函数长度是常用补充指标
#   - 阈值只是参考：>10 建议拆分，>20 高风险；别把指标当 KPI
#   - 用 NodeVisitor 逐函数统计，输出「函数 -> 指标」表，可定位热点
#   - 与第58章 ruff/mypy 配合：指标找候选，人工判断是否需要重构
# 依赖：无（标准库）
import ast
from dataclasses import dataclass, field

SOURCE = '''\
def trivial(x):
    return x + 1

def classify(score, vip=False):
    if score >= 90:
        grade = "A"
    elif score >= 75:
        grade = "B"
    elif score >= 60:
        grade = "C"
    else:
        grade = "D"
    if vip and score > 80:
        grade = grade + "+"
    return grade

def process(items, strict=True):
    total = 0
    for it in items:
        try:
            if it > 0 and it < 100:
                total += it
            elif strict:
                raise ValueError(it)
        except ValueError:
            continue
    result = [x * 2 for x in items if x % 2 == 0]
    return total, result

def nested(data):
    for a in data:
        for b in a:
            if b:
                for c in b:
                    if c > 0:
                        return c
    return 0
'''


@dataclass
class Metrics:
    name: str
    lineno: int
    lines: int = 0
    decisions: int = 0
    max_depth: int = 0
    statements: int = 0
    calls: int = 0

    @property
    def complexity(self):
        return self.decisions + 1

    @property
    def risk(self):
        if self.complexity <= 5 and self.max_depth <= 2:
            return "低"
        if self.complexity <= 10 and self.max_depth <= 4:
            return "中"
        return "高"


class MetricVisitor(ast.NodeVisitor):
    DECISION = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.IfExp,
                ast.Assert, ast.With, ast.AsyncWith)

    def __init__(self):
        self.results = []
        self._stack = []

    @property
    def m(self):
        return self._stack[-1]

    def visit_FunctionDef(self, node):
        self._stack.append(Metrics(node.name, node.lineno))
        self.m.lines = (node.end_lineno or node.lineno) - node.lineno + 1
        self.generic_visit(node)
        self.results.append(self._stack.pop())

    def generic_visit(self, node):
        if self._stack:
            if isinstance(node, ast.stmt):
                self.m.statements += 1
            if isinstance(node, ast.Call):
                self.m.calls += 1
            if isinstance(node, self.DECISION):
                self.m.decisions += 1
            if isinstance(node, ast.BoolOp):
                self.m.decisions += len(node.values) - 1
            if isinstance(node, ast.Try):
                self.m.decisions += len(node.handlers)
            if isinstance(node, ast.comprehension):
                self.m.decisions += len(node.ifs)
        super().generic_visit(node)


def nesting_depth(fn):
    """计算函数体的最大控制流嵌套深度。"""
    def walk(node, depth=0):
        best = depth
        for child in ast.iter_child_nodes(node):
            d = depth + 1 if isinstance(child, (ast.If, ast.For, ast.While,
                                                  ast.With, ast.Try)) else depth
            best = max(best, walk(child, d))
        return best
    return max((walk(stmt) for stmt in fn.body), default=0)


print("== 各函数度量 ==")
tree = ast.parse(SOURCE)
v = MetricVisitor()
v.visit(tree)
# 补上嵌套深度（Visitor 里不便维护，单独算）
depths = {f.name: nesting_depth(f) for f in tree.body if isinstance(f, ast.FunctionDef)}
for m in v.results:
    m.max_depth = depths[m.name]

print(f"  {'函数':<14}{'行':>4}{'语句':>6}{'调用':>6}{'判定':>6}{'圈复杂度':>9}{'嵌套':>6}  风险")
for m in v.results:
    print(f"  {m.name:<14}{m.lines:>4}{m.statements:>6}{m.calls:>6}"
          f"{m.decisions:>6}{m.complexity:>9}{m.max_depth:>6}  {m.risk}")

print("\n== 判定节点明细（classify）==")
fn = next(f for f in tree.body if isinstance(f, ast.FunctionDef) and f.name == "classify")
for n in ast.walk(fn):
    if isinstance(n, (ast.If, ast.IfExp, ast.BoolOp)):
        label = type(n).__name__
        extra = f" values={len(n.values)}" if isinstance(n, ast.BoolOp) else ""
        print(f"  L{n.lineno}: {label}{extra}")

print("\n== 阈值解读 ==")
for line in (
    "  1~5   : 简单清晰，测试容易覆盖",
    "  6~10  : 尚可，留意分支组合",
    "  11~20 : 建议拆分，单测用例会快速膨胀",
    "  >20   : 高风险，通常伴随深嵌套与重复逻辑",
):
    print(" ", line)

print("\n== 圈复杂度与最少测试用例 ==")
for m in v.results:
    print(f"  {m.name:<14} 圈复杂度={m.complexity} -> 分支覆盖至少约 {m.complexity} 条路径")

print("\n== 其他常用指标 ==")
print("  函数行数       : 过长通常职责不单一")
print("  参数个数       : >5 个考虑 dataclass / 配置对象")
print("  最大嵌套深度   : >4 层可用早返回（guard clause）压平")
print("  Halstead 体积  : 由运算符/操作数计数估算，偏学术")
print("  可维护性指数   : 综合行数、复杂度、注释率")

print("\n== 指标的正确用法 ==")
for line in [
    "  指标用于「找候选」，重构与否由人结合业务判断",
    "  不要设硬性 KPI，否则会被拆函数、加空行等手法刷低",
    "  关注趋势（本季度是否变差）比关注绝对值更有意义",
    "  与覆盖率、评审意见、线上缺陷一起看，别单指标决策",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 给度量器增加「参数个数」与「返回语句数量」两个指标。
# 2. 实现认知复杂度（嵌套越深权重越高），与圈复杂度对比排序差异。
# 3. 扫描整个目录，输出按圈复杂度降序的 Top 10 函数。
# 4. 思考：为什么「圈复杂度高」不等于「代码一定难维护」？
