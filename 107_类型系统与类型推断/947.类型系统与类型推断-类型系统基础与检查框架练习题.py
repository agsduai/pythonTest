# ===== 第947课：类型系统与类型推断-类型系统基础与检查框架 =====
# 知识点：
#   - 类型 = 对程序的静态证明：『这个表达式不会返回字符串』在运行前成立
#   - 判断（judgement）：Γ ⊢ e : τ —— 在环境 Γ 下，表达式 e 具有类型 τ
#   - 类型环境 Γ：变量名 -> 类型的映射（作用域即环境的嵌套）
#   - 检查（check）与推断（infer）：标注驱动 vs 自动推导，本章两者都做
#   - 本课搭一个带类型环境的最小检查器，后续课程逐步升级到完整推断
# 依赖：无（标准库）
from collections import deque


# ---------- 类型表示（元组，不可变） ----------
T_INT = ("int",)
T_BOOL = ("bool",)
T_STR = ("str",)


def t_arrow(param, result):
    return ("arrow", param, result)


def type_name(t):
    if t == T_INT:
        return "Int"
    if t == T_BOOL:
        return "Bool"
    if t == T_STR:
        return "Str"
    if t[0] == "arrow":
        return f"({type_name(t[1])} -> {type_name(t[2])})"
    return repr(t)


# ---------- 程序 AST（带行号） ----------
# ("num", line, n) / ("bool", line, b) / ("str", line, s)
# ("var", line, name) / ("let", line, name, annotated_type, expr, body)
# ("if", line, cond, then, else) / ("binop", line, op, left, right)
# ("app", line, fn, arg)


def type_from_annotation(anno):
    """标注语法：'Int' / 'Bool' / 'Str' / 'Int -> Bool'（右结合）。"""
    def build(pieces):
        if len(pieces) == 1:
            low = pieces[0].strip().lower()
            return {"int": T_INT, "bool": T_BOOL, "str": T_STR}[low]
        return t_arrow(build(pieces[:-1]), build([pieces[-1]]))
    return build([p.strip() for p in anno.split("->")])


class TypeErrorReport(Exception):
    def __init__(self, line, message):
        super().__init__(f"第 {line} 行: {message}")
        self.line = line


class TypeChecker:
    """带标注的检查器：环境 Γ + 逐节点 check。"""

    def __init__(self, errors=None):
        self.errors = list(errors or [])

    def error(self, line, message):
        self.errors.append(TypeErrorReport(line, message))
        return T_INT                          # 错误恢复：假装是 Int 继续检查

    def check(self, term, env):
        """返回表达式类型（错误时返回占位类型并记录）。"""
        kind = term[0]
        if kind == "num":
            return T_INT
        if kind == "bool":
            return T_BOOL
        if kind == "str":
            return T_STR
        if kind == "var":
            _, line, name = term
            if name not in env:
                return self.error(line, f"未定义变量 {name!r}")
            return env[name]
        if kind == "let":
            _, line, name, anno, expr, body = term
            expected = type_from_annotation(anno)
            actual = self.check(expr, env)
            if actual != expected:
                self.error(line, f"{name} 标注为 {type_name(expected)}，"
                                 f"实际 {type_name(actual)}")
            env2 = dict(env)
            env2[name] = expected
            return self.check(body, env2)
        if kind == "if":
            _, line, cond, then_t, else_t = term
            if self.check(cond, env) != T_BOOL:
                self.error(term[1], "if 条件必须是 Bool")
            t_then = self.check(then_t, env)
            t_else = self.check(else_t, env)
            if t_then != t_else:
                return self.error(line, f"两分支类型不一致: "
                                        f"{type_name(t_then)} vs {type_name(t_else)}")
            return t_then
        if kind == "binop":
            _, line, op, left, right = term
            tl = self.check(left, env)
            tr = self.check(right, env)
            if op in ("+", "-", "*"):
                if tl != T_INT or tr != T_INT:
                    return self.error(line, f"{op} 需要 Int 操作数，"
                                            f"得到 {type_name(tl)}/{type_name(tr)}")
                return T_INT
            if op == "==":
                if tl != tr:
                    return self.error(line, "== 两侧类型不一致")
                return T_BOOL
            return self.error(line, f"未知运算符 {op!r}")
        if kind == "app":
            _, line, fn, arg = term
            tf = self.check(fn, env)
            ta = self.check(arg, env)
            if tf[0] != "arrow":
                return self.error(line, f"对非函数（{type_name(tf)}）发起调用")
            if tf[1] != ta:
                return self.error(line, f"实参类型 {type_name(ta)} 与形参 "
                                        f"{type_name(tf[1])} 不符")
            return tf[2]
        return self.error(term[1] if len(term) > 1 else 0, f"未知节点 {kind}")


def typecheck_program(terms):
    checker = TypeChecker()
    env = {}
    for term in terms:
        checker.check(term, env)
    return checker.errors


print("== 类型环境与判断 ==")
env = {"n": T_INT, "flag": T_BOOL, "greet": t_arrow(T_STR, T_STR)}
print(f"  Γ = {{n: {type_name(T_INT)}, flag: {type_name(T_BOOL)}, "
      f"greet: {type_name(env['greet'])}}}")
print("  判断示例: Γ ⊢ n : Int（在环境中可查）")
print(f"  标注解析 'Int -> Bool' = {type_name(type_from_annotation('Int -> Bool'))}")

print("\n== 合法程序：全程通过 ==")
good = [
    ("let", 1, "age", "Int", ("num", 1, 18),
     ("if", 2, ("binop", 2, "==", ("var", 2, "age"), ("num", 2, 18)),
      ("str", 3, "成年"), ("str", 3, "未成年"))),
]
errors = typecheck_program(good)
print(f"  错误数 = {len(errors)}")
print("  let age: Int = 18; if age == 18 then '成年' else '未成年' -> Str ✓")

print("\n== 四类典型错误 ==")
bad_cases = [
    ("未定义变量",
     [("var", 1, "oops")]),
    ("标注不符",
     [("let", 1, "flag", "Bool", ("num", 1, 42), ("var", 1, "flag"))]),
    ("分支不一致",
     [("if", 1, ("bool", 1, True), ("num", 1, 1), ("str", 1, "x"))]),
    ("调用非函数",
     [("app", 1, ("num", 1, 7), ("num", 1, 8))]),
]
for label, program in bad_cases:
    errors = typecheck_program(program)
    print(f"  [{label}]")
    for e in errors:
        print(f"    ✗ {e}")

print("\n== 错误恢复：继续检查后续代码 ==")
mixed = [
    ("var", 1, "missing"),                     # 错误 1
    ("binop", 2, "+", ("num", 2, 1), ("num", 2, 2)),   # 合法
    ("var", 3, "another"),                     # 错误 2
]
errors = typecheck_program(mixed)
print(f"  3 条语句报出 {len(errors)} 个错误（不影响彼此）:")
for e in errors:
    print(f"    ✗ {e}")
print("  工业编译器都做错误恢复 —— 一次给出全部诊断而非逐个修")

print("\n== 静态类型防住什么 ==")
for line in (
    "  运行期才炸的 TypeError/AttributeError 在检查期全部现形",
    "  if 分支类型不一致 = 忘记处理某条路径的返回值",
    "  未定义变量 = 拼写错误/作用域错误，0 成本捕获",
    "  类型即文档：签名 'Int -> Bool' 一眼读出契约",
):
    print("  -", line)

print("\n== 检查 vs 推断 ==")
for line in (
    "  检查（check）：程序带标注，验证一致 —— 本课的做法",
    "  推断（infer）：程序不带标注，机器推导类型 —— 950 课算法 W",
    "  工业实践：两者混合（推断为主，关键边界手写标注）",
):
    print("  -", line)

print("\n== 小结 ==")
for line in (
    "  类型检查 = 递归遍历 AST + 环境查询 + 一致性断言",
    "  错误恢复让编译器像医生：一次诊断所有问题",
    "  标注类型系统足够防呆，但写标注很累 → 推断登场",
    "  948 课：引入 λ 函数与箭头类型的完整检查",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 增加除法运算符：检查除零无法静态发现，但可检查『除数必须是 Int』。
# 2. 实现 let 的遮蔽（shadowing）：内层 let 同名变量覆盖外层，验证环境嵌套。
# 3. 增加 Unit 类型（无返回值语句），并规定 if 的两分支允许 Unit/Unit。
# 4. 思考：为什么『两分支类型必须一致』？动态语言不要求，代价是什么？
