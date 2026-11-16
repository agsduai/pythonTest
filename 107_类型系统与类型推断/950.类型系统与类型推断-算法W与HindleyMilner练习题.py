# ===== 第950课：类型系统与类型推断-算法W与Hindley-Milner =====
# 知识点：
#   - Hindley-Milner：λ 演算 + let 多态的完整推断 —— 不写任何标注
#   - 算法 W 三件套：infer 递归、unify(949 课)、generalize/instantiate
#   - let 多态：let 绑定的函数对每次使用实例化新的类型变量
#   - generalize：把类型中「未被环境约束」的变量提升为全称量词
#   - λ 参数是单态的（不可多态）—— 值限制（value restriction）的根源
# 依赖：无（标准库）


class InferError(Exception):
    pass


T_INT = ("int",)
T_BOOL = ("bool",)


def t_var(i):
    return ("tvar", i)


def t_arrow(a, b):
    return ("arrow", a, b)


def type_str(t, subst=None, names=None):
    subst = subst or {}
    if names is None:
        names = {}
    t = _walk(t, subst)
    if t[0] == "tvar":
        if t[1] not in names:
            names[t[1]] = "abcdefgh"[len(names) % 8] if len(names) < 8 \
                else f"t{len(names)}"
        return names[t[1]]
    if t == T_INT:
        return "Int"
    if t == T_BOOL:
        return "Bool"
    if t[0] == "arrow":
        return f"({type_str(t[1], subst, names)} -> {type_str(t[2], subst, names)})"
    return "?"


def _walk(t, subst):
    while t[0] == "tvar" and t[1] in subst:
        t = subst[t[1]]
    return t


def _walk_deep(t, subst):
    t = _walk(t, subst)
    if t[0] == "arrow":
        return ("arrow", _walk_deep(t[1], subst), _walk_deep(t[2], subst))
    return t


def occurs(var, t, subst):
    t = _walk_deep(t, subst)
    if t[0] == "tvar":
        return t[1] == var
    if t[0] == "arrow":
        return occurs(var, t[1], subst) or occurs(var, t[2], subst)
    return False


def free_vars(t, subst):
    """类型中未被代换钉死的变量集合。"""
    t = _walk_deep(t, subst)
    out = set()
    if t[0] == "tvar":
        out.add(t[1])
    elif t[0] == "arrow":
        out |= free_vars(t[1], subst)
        out |= free_vars(t[2], subst)
    return out


class Scheme:
    """全称量化的类型方案：∀vars. t（vars 是量词化的变量编号）。"""

    def __init__(self, vars_, t):
        self.vars = list(vars_)
        self.t = t


class AlgorithmW:
    def __init__(self):
        self.next_var = 0
        self.subst = {}

    def fresh(self):
        self.next_var += 1
        return t_var(self.next_var)

    def walk_deep(self, t):
        return _walk_deep(t, self.subst)

    def unify(self, a, b):
        a, b = self.walk_deep(a), self.walk_deep(b)
        if a == b:
            return
        if a[0] == "tvar":
            self._bind(a[1], b)
            return
        if b[0] == "tvar":
            self._bind(b[1], a)
            return
        if a[0] == "arrow" and b[0] == "arrow":
            self.unify(a[1], b[1])
            self.unify(a[2], b[2])
            return
        raise InferError(f"{type_str(a, self.subst)} ≠ "
                         f"{type_str(b, self.subst)}")

    def _bind(self, var, t):
        t = self.walk_deep(t)
        if t == t_var(var):
            return
        if occurs(var, t, self.subst):
            raise InferError(f"occurs check: t{var} ∈ {type_str(t, self.subst)}")
        for k in list(self.subst):
            self.subst[k] = _walk_deep(self.subst[k], {var: t})
        self.subst[var] = t

    def generalize(self, env, t):
        """提升：t 中不在环境自由变量里的变量成为全称量词。"""
        env_free = set()
        for scheme in env.values():
            s_free = free_vars(scheme.t, self.subst) - set(scheme.vars)
            env_free |= s_free
        t_free = free_vars(t, self.subst)
        return Scheme(sorted(t_free - env_free), t)

    def instantiate(self, scheme):
        """每次使用实例化：量词变量 -> 全新类型变量。"""
        mapping = {v: self.fresh() for v in scheme.vars}
        return _walk_deep(scheme.t, mapping)

    def infer(self, term, env):
        """算法 W 的 infer。env: name -> Scheme。返回类型。"""
        kind = term[0]
        if kind == "num":
            return T_INT
        if kind == "bool":
            return T_BOOL
        if kind == "var":
            name = term[1]
            if name not in env:
                raise InferError(f"未定义变量 {name!r}")
            return self.instantiate(env[name])
        if kind == "lam":
            _, param, body = term
            tv = self.fresh()
            env2 = dict(env)
            env2[param] = Scheme([], tv)          # λ 参数是单态的！
            body_t = self.infer(body, env2)
            return t_arrow(tv, body_t)
        if kind == "app":
            _, fn, arg = term
            tf = self.infer(fn, env)
            ta = self.infer(arg, env)
            result = self.fresh()
            self.unify(tf, t_arrow(ta, result))
            return result
        if kind == "let":
            _, name, expr, body = term
            t_expr = self.infer(expr, env)
            scheme = self.generalize(env, t_expr)   # let 才有多态！
            env2 = dict(env)
            env2[name] = scheme
            return self.infer(body, env2)
        raise InferError(f"未知节点 {kind}")


print("== 恒等函数：无标注推断出 a -> a ==")
w = AlgorithmW()
identity = ("lam", "x", ("var", "x"))
t_id = w.infer(identity, {})
print(f"  λx.x           : {type_str(t_id, w.subst)}")
scheme_id = w.generalize({}, t_id)
print(f"  generalize 后  : ∀{scheme_id.vars}. {type_str(scheme_id.t, w.subst)}")

print("\n== let 多态：同一身份函数用在两种类型上 ==")
# let id = λx.x in (id 1) 的类型
w2 = AlgorithmW()
env2 = {}
t_id2 = w2.infer(("lam", "x", ("var", "x")), env2)
env2["id"] = w2.generalize(env2, t_id2)
t_use_int = w2.infer(("app", ("var", "id"), ("num", 0)), env2)
print(f"  id 应用于 Int  -> {type_str(t_use_int, w2.subst)}")
# 关键：Bool 使用会实例化新的类型变量，不与 Int 冲突
w3 = AlgorithmW()
env3 = {}
t_id3 = w3.infer(("lam", "x", ("var", "x")), env3)
env3["id"] = w3.generalize(env3, t_id3)
w3.infer(("app", ("var", "id"), ("num", 0)), env3)
t_use_bool = w3.infer(("app", ("var", "id"), ("bool", 0)), env3)
print(f"  id 应用于 Bool -> {type_str(t_use_bool, w3.subst)}   （两次使用无冲突）")

print("\n== λ 参数的单态性（多态的边界）==")
w4 = AlgorithmW()
try:
    w4.infer(("lam", "f",
              ("if", ("bool", 0),
               ("app", ("var", "f"), ("num", 0)),
               ("app", ("var", "f"), ("bool", 0)))), {})
    print("  未报错（不应发生）")
except InferError as exc:
    print(f"  λf. 同一 f 既用于 Int 又用于 Bool -> 报错: {exc}")
print("  f 是 λ 引入的单态变量：两次使用必须同一类型 —— 值限制的由来")

print("\n== occurs check：λx. x x ==")
w5 = AlgorithmW()
try:
    w5.infer(("lam", "x", ("app", ("var", "x"), ("var", "x"))), {})
except InferError as exc:
    print(f"  λx. x x  -> 报错: {exc}")
print("  无限类型不存在有限表示 —— occurs check 拦截")

print("\n== 组合函数的推断链 ==")
# compose = λf. λg. λx. f (g x)
compose = ("lam", "f",
           ("lam", "g",
            ("lam", "x",
             ("app", ("var", "f"), ("app", ("var", "g"), ("var", "x"))))))
w6 = AlgorithmW()
t_comp = w6.infer(compose, {})
print(f"  compose = λf.λg.λx. f(g x) : {type_str(t_comp, w6.subst)}")
scheme_comp = w6.generalize({}, t_comp)
print(f"  generalize: ∀{scheme_comp.vars}. "
      f"{type_str(scheme_comp.t, w6.subst)}")
print("  一个 12 字符的表达式推出了完整的多态组合子类型")

print("\n== 加法帮助钉死类型 ==")
w7 = AlgorithmW()
env7 = {"plus": Scheme([], t_arrow(T_INT, T_INT))}
t_add = w7.infer(("lam", "x",
                  ("app", ("var", "plus"),
                   ("app", ("var", "x"), ("num", 0)))), env7)
print(f"  λx. plus (x 1)  : {type_str(t_add, w7.subst)}")
print("  plus: Int->Int 迫使 x 必须是 Int -> Int —— 约束从使用点流向定义点")

print("\n== 小结 ==")
for line in (
    "  算法 W = infer 递归 + unify + generalize/instantiate 四件套",
    "  let 多态是 HM 的灵魂：同一函数可当多种类型用",
    "  λ 参数单态、occurs check、值限制 —— 体系的三个『边界』",
    "  951 课：给语言加代数数据类型与模式匹配的穷尽性检查",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 把 generalize 改为「值限制」：只有 expr 是 λ 或字面量时才多态化。
# 2. 实现 letrec（递归 let）：先假设类型再 unify 自身，观察单态化效果。
# 3. 给推断器加「类型打印的最小括号」优化（∧箭头右结合时的括号省略）。
# 4. 思考：为什么 HM 推断可以在一次遍历内完成（无需迭代到不动点）？
