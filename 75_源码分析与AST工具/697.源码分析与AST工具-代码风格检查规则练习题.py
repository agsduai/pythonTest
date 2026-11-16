# ===== 第697课：源码分析与AST工具-代码风格检查规则 =====
# 知识点：
#   - linter 规则 = 一组 AST 访问器：每条规则产出 (行, 列, 级别, 消息)
#   - 常见规则：可变默认参数、裸 except、未使用变量、print 残留、重复字面量
#   - 规则要能配置开关与严重级别，输出统一结构便于 IDE / CI 消费
#   - 误报控制：白名单（测试文件允许 print）、# noqa 注释抑制
#   - 与第58章 ruff/mypy、第693课复杂度配合：AST 做结构检查
#   - 本课手写一个 mini-linter，覆盖 5 条规则，可扫描内存中的源码
# 依赖：无（标准库）
import ast
from dataclasses import dataclass
from collections import Counter


@dataclass
class Issue:
    line: int
    col: int
    level: str       # ERROR / WARNING / INFO
    rule: str
    message: str

    def __str__(self):
        return f"L{self.line}:{self.col} {self.level:<7} [{self.rule}] {self.message}"


class Linter(ast.NodeVisitor):
    MUTABLE = (ast.List, ast.Dict, ast.Set)
    RULES = {
        "MUTABLE_DEFAULT": "WARNING",
        "BARE_EXCEPT": "ERROR",
        "PRINT_CALL": "WARNING",
        "UNUSED_VAR": "INFO",
        "GLOBAL_STMT": "WARNING",
    }

    def __init__(self, source, config=None):
        self.source = source
        self.config = config or self.RULES.copy()
        self.issues = []
        self.noqa = {i for i, line in enumerate(source.splitlines(), 1)
                     if "# noqa" in line}
        self._scope = ["<module>"]
        self._defined = {}
        self._loaded = Counter()

    def report(self, node, rule, message):
        level = self.config.get(rule)
        if not level or node.lineno in self.noqa:
            return
        self.issues.append(Issue(node.lineno, node.col_offset, level, rule, message))

    def visit_FunctionDef(self, node):
        # 规则 1：可变默认参数
        for default in list(node.args.defaults) + [d for d in node.args.kw_defaults if d]:
            if isinstance(default, self.MUTABLE):
                self.report(default, "MUTABLE_DEFAULT",
                            f"函数 {node.name} 使用了可变默认参数，应改为 None")
        self._scope.append(node.name)
        self._defined[node.name] = []
        for a in node.args.args:
            self._defined[node.name].append(a.arg)
        self.generic_visit(node)
        # 规则 4：函数内定义但从未读取的局部变量（排除参数）
        loaded_here = set(self._loaded)      # Counter 的 key 就是变量名
        for name in self._defined[node.name]:
            if name not in loaded_here and not name.startswith("_"):
                self.report(node, "UNUSED_VAR", f"局部变量 {name!r} 定义后未使用")
        self._scope.pop()

    def visit_ExceptHandler(self, node):
        # 规则 2：裸 except
        if node.type is None:
            self.report(node, "BARE_EXCEPT", "裸 except 会吞掉 KeyboardInterrupt/SystemExit")
        self.generic_visit(node)

    def visit_Call(self, node):
        # 规则 3：print 残留
        if isinstance(node.func, ast.Name) and node.func.id == "print":
            self.report(node, "PRINT_CALL", "生产代码里发现 print，改用 logging")
        self.generic_visit(node)

    def visit_Global(self, node):
        # 规则 5：global 语句
        self.report(node, "GLOBAL_STMT", "global 让状态难追踪，考虑传参或类封装")
        self.generic_visit(node)

    def visit_Assign(self, node):
        if self._scope[-1] in self._defined:
            for t in node.targets:
                for n in ast.walk(t):
                    if isinstance(n, ast.Name):
                        self._defined[self._scope[-1]].append(n.id)
        self.generic_visit(node)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self._loaded[node.id] += 1
        self.generic_visit(node)


def lint(source, config=None):
    tree = ast.parse(source)
    l = Linter(source, config)
    l.visit(tree)
    return sorted(l.issues, key=lambda i: (i.line, i.col))


BAD_CODE = '''\
import os

cache = []

def add(item, bucket=[]):
    unused = 42
    try:
        bucket.append(item)
    except:
        print("failed")
    return bucket

def bump():
    global counter
    counter += 1

def clean(x):
    tmp = x * 2  # noqa
    return tmp
'''

print("== 扫描结果 ==")
issues = lint(BAD_CODE)
for i in issues:
    print("  ", i)
print(f"  共 {len(issues)} 条")

print("\n== 按级别 / 规则统计 ==")
print("  级别:", dict(Counter(i.level for i in issues)))
print("  规则:", dict(Counter(i.rule for i in issues)))

print("\n== 配置：关掉 PRINT_CALL ==")
config = Linter.RULES.copy()
config["PRINT_CALL"] = None
for i in lint(BAD_CODE, config):
    print("  ", i)

print("\n== noqa 抑制生效 ==")
print("  clean() 里的 tmp 带 # noqa，该行不报 UNUSED_VAR:",
      not any(i.rule == "UNUSED_VAR" and i.line ==
              BAD_CODE.splitlines().index("    tmp = x * 2  # noqa") + 1 for i in issues))

print("\n== 干净代码应零告警 ==")
GOOD = '''\
import logging

def add(item, bucket=None):
    if bucket is None:
        bucket = []
    try:
        bucket.append(item)
    except ValueError as e:
        logging.warning("skip %s", e)
    return bucket
'''
print("  ", lint(GOOD) or "无问题")

print("\n== 统一输出结构便于工具消费 ==")
import json
print("  ", json.dumps([vars(i) for i in issues[:2]], ensure_ascii=False))
print("  CI 里可按 level==ERROR 决定是否失败，IDE 里可渲染成波浪线")

print("\n== 与真实 linter 的差距 ==")
for line in (
    "  ruff/flake8: 几百条规则、增量缓存、自动修复、配置体系",
    "  mypy      : 基于类型注解做跨函数推导，不只是单文件结构",
    "  本课 mini : 展示「规则 = Visitor + 统一 Issue」这一核心模式",
    "  误报控制  : 白名单、noqa、按路径配置，是能否落地的关键",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 增加规则：函数超过 50 行、嵌套超过 4 层、参数超过 5 个。
# 2. 实现 --fix：把裸 except 自动改写成 except Exception（用 NodeTransformer）。
# 3. 按目录扫描所有 .py，输出按文件分组的 JSON 报告。
# 4. 思考：为什么 linter 必须支持「按文件/按行」抑制，否则很难在老项目落地？
