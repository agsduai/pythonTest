# ===== 第948课：类型系统与类型推断-λ函数与箭头类型检查 =====
# 知识点：
#   - λ 函数：λx. 表达式 —— 参数类型标注后，函数类型 = 箭头类型
#   - 箭头类型 τ1 → τ2：接受 τ1、产出 τ2；调用点检查实参匹配
#   - 高阶函数：函数作为参数（如 map 的 f: A → B）
#   - 闭包的捕获在类型层无痕：环境查不到的自由变量直接报错
#   - 柯里化：Int -> Int -> Int 等价于接受 Int 返回 (Int -> Int)
# 依赖：无（标准库）


T_INT = ("int",)
T_BOOL = ("bool",)
T_STR = ("str",)


def t_arrow(p, r):
    return ("arrow", p, r)


def type_name(t):
    if t == T_INT:
        return "Int"
    if t == T_BOOL:
        return "Bool"
    if t == T_STR:
        return "Str"
    if t[0] == "arrow":
        return f"({type_name(t[1])} -> {type_name(t[2])})"
    return "?"


class Checker:
    def __init__(self):
        self.errors = []

    def error(self, line, message):
        self.errors.append((line, message))
        return T_INT

    def check(self, term, env):
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
        if kind == "lam":                      # λ(参数: 类型). 体
            _, line, param, anno, body = term
            ptype = self.parse_anno(anno)
            env2 = dict(env)
            env2[param] = ptype
            body_t = self.check(body, env2)
            return t_arrow(ptype, body_t)
        if kind == "app":
            _, line, fn, arg = term
            tf = self.check(fn, env)
            ta = self.check(arg, env)
            if tf[0] != "arrow":
                return self.error(line, f"对 {type_name(tf)} 发起调用")
            if tf[1] != ta:
                return self.error(line, f"实参 {type_name(ta)} ≠ 形参 "
                                        f"{type_name(tf[1])}")
            return tf[2]
        if kind == "app2":                     # 双参柯里化调用
            _, line, fn, a1, a2 = term
            tf = self.check(fn, env)
            ta1 = self.check(a1, env)
            if tf[0] != "arrow" or tf[2][0] != "arrow":
                return self.error(line, "柯里化调用需要双箭头函数")
            if tf[1] != ta1:
                return self.error(line, "第一个实参类型不符")
            ta2 = self.check(a2, env)
            if tf[2][1] != ta2:
                return self.error(line, "第二个实参类型不符")
            return tf[2][2]
        if kind == "binop":
            _, line, op, left, right = term
            tl, tr = self.check(left, env), self.check(right, env)
            if op == "+" and tl == T_INT and tr == T_INT:
                return T_INT
            return self.error(line, f"{op} 类型不符: {type_name(tl)}/{type_name(tr)}")
        return self.error(term[1], f"未知节点 {kind}")

    def parse_anno(self, anno):
        pieces = [p.strip().lower() for p in anno.split("->")]
        def build(ps):
            if len(ps) == 1:
                return {"int": T_INT, "bool": T_BOOL, "str": T_STR}[ps[0]]
            return t_arrow(build(ps[:-1]), build([ps[-1]]))
        return build(pieces)


def render_fn(name, params, body_text):
    """辅助：给演示打印函数签名。"""
    return f"{name} : {params}"


print("== λ 函数的类型 ==")
checker = Checker()
inc = ("lam", 1, "x", "Int", ("binop", 1, "+", ("var", 1, "x"), ("num", 1, 1)))
t_inc = checker.check(inc, {})
print(f"  λx:Int. x+1  :  {type_name(t_inc)}")
compose_like = ("lam", 2, "f", "Int -> Bool",
                ("lam", 2, "x", "Int", ("app", 2, ("var", 2, "f"),
                                        ("var", 2, "x"))))
t_compose = checker.check(compose_like, {})
print(f"  λf:Int->Bool. λx:Int. f x  :  {type_name(t_compose)}")

print("\n== 调用点检查 ==")
t_call = checker.check(("app", 3, inc, ("num", 3, 41)), {})
print(f"  (λx:Int.x+1) 41  ->  {type_name(t_call)}")
t_wrong = checker.check(("app", 3, inc, ("bool", 3, True)), {})
print(f"  (λx:Int.x+1) true  ->  错误 {checker.errors[-1] if checker.errors else '无'}")

print("\n== 柯里化：Int -> Int -> Int ==")
add_curried = ("lam", 4, "a", "Int",
               ("lam", 4, "b", "Int",
                ("binop", 4, "+", ("var", 4, "a"), ("var", 4, "b"))))
t_add = checker.check(add_curried, {})
print(f"  λa:Int. λb:Int. a+b  :  {type_name(t_add)}")
t_partial = checker.check(("app2", 5, add_curried, ("num", 5, 3), ("num", 5, 4)), {})
print(f"  add 3 4  ->  {type_name(t_partial)}")

print("\n== 高阶函数：map 风格 ==")
map_fn = ("lam", 6, "f", "Int -> Bool",
          ("lam", 6, "x", "Int", ("app", 6, ("var", 6, "f"), ("var", 6, "x"))))
print(f"  map 类型: {type_name(checker.check(map_fn, {}))}")
print("  高阶检查的关键：f 的类型随 λ 标注注入环境，调用点按箭头匹配")

print("\n== 自由变量的报错 ==")
free_term = ("lam", 8, "x", "Int", ("binop", 8, "+", ("var", 8, "x"),
                                     ("var", 8, "missing")))
checker.check(free_term, {})
print(f"  捕获缺失的自由变量: {checker.errors[-1] if checker.errors else '无'}")
print("  闭包在类型层不留痕迹 —— 自由变量必须在 λ 处可解析")

print("\n== 错误恢复 ==")
print(f"  累计错误数 = {len(checker.errors)}")
for line, msg in checker.errors:
    print(f"    第 {line} 行: {msg}")

print("\n== 箭头类型的工程对应 ==")
for line in (
    "  Python 类型标注: def inc(x: int) -> int —— 与本课箭头同构",
    "  高阶函数: Callable[[int], bool] 就是 Int -> Bool",
    "  柯里化: functools.partial(add, 3) 的类型是 Int -> Int",
    "  返回函数的函数（工厂）在类型层就是两段箭头",
):
    print("  -", line)

print("\n== 小结 ==")
for line in (
    "  λ 的类型 = 参数标注 + 体类型 拼成箭头",
    "  调用点按箭头逐段匹配实参 —— 柯里化就是箭头链",
    "  高阶函数 = 箭头类型的参数，类型随 λ 标注入环境",
    "  949 课：去掉所有标注 —— 用合一算法自动推断",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 增加无标注 λ（λx. x+1），让参数默认 Int，观察哪些程序仍然可检查。
# 2. 实现『部分应用』的显式形式：add 3（只给第一个实参），类型应 Int -> Int。
# 3. 为错误信息附加「期望 vs 实际」的类型树打印（多行缩进展示）。
# 4. 思考：柯里化与『双参数函数』在类型层有什么本质区别？部分应用给
#    重用带来什么？
