# ===== 第949课：类型系统与类型推断-合一算法与代换 =====
# 知识点：
#   - 类型变量 T_a：未知类型的占位符 —— 推断的目标就是把它们「钉死」
#   - 合一（unification）：找到使两个类型相等的代换（substitution）
#   - 代换 σ：类型变量 -> 类型的映射；应用 = 把变量替换为映射值
#   - occurs check：T 不能出现在 T 自身里（防无限类型 a -> a 的病态解）
#   - 合一是 Prolog/泛型编程/Hindley-Milner 共同的引擎
# 依赖：无（标准库）


class UnifyError(Exception):
    pass


class OccursError(UnifyError):
    pass


T_INT = ("int",)
T_BOOL = ("bool",)


def t_var(name):
    return ("var", name)


def t_arrow(a, b):
    return ("arrow", a, b)


def type_str(t, subst=None):
    subst = subst or {}
    t = walk(t, subst)
    if t[0] == "var":
        return t[1]
    if t == T_INT:
        return "Int"
    if t == T_BOOL:
        return "Bool"
    if t[0] == "arrow":
        return f"({type_str(t[1], subst)} -> {type_str(t[2], subst)})"
    return repr(t)


def walk(t, subst):
    """沿代换链走到底（支持 var -> var -> type）。"""
    while t[0] == "var" and t[1] in subst:
        t = subst[t[1]]
    return t


def walk_deep(t, subst):
    """递归应用代换到类型结构深处。"""
    t = walk(t, subst)
    if t[0] == "arrow":
        return ("arrow", walk_deep(t[1], subst), walk_deep(t[2], subst))
    return t


def occurs(var, t, subst):
    """var 是否出现在 t 中（应用代换后）—— occurs check。"""
    t = walk_deep(t, subst)
    if t[0] == "var":
        return t[1] == var
    if t[0] == "arrow":
        return occurs(var, t[1], subst) or occurs(var, t[2], subst)
    return False


class Unifier:
    def __init__(self):
        self.subst = {}

    def unify(self, a, b):
        """合一 a 与 b，更新代换。返回是否成功（失败抛 UnifyError）。"""
        a = walk_deep(a, self.subst)
        b = walk_deep(b, self.subst)
        if a == b:
            return True
        if a[0] == "var":
            return self._bind(a[1], b)
        if b[0] == "var":
            return self._bind(b[1], a)
        if a[0] == "arrow" and b[0] == "arrow":
            ok = self.unify(a[1], b[1])
            return ok and self.unify(a[2], b[2])
        raise UnifyError(f"{type_str(a)} 与 {type_str(b)} 无法合一")

    def _bind(self, var, t):
        if t == ("var", var):
            return True
        if occurs(var, t, self.subst):
            raise OccursError(f"occurs check: {var} 出现在 {type_str(t)} 中")
        # 重要：把既有代换中的 var 全部重写为 t（保持代换的一致性）
        for k in list(self.subst):
            self.subst[k] = walk_deep(self.subst[k], {var: t})
        self.subst[var] = t
        return True


print("== 基本合一 ==")
u = Unifier()
ta, tb = t_var("a"), t_var("b")
u.unify(ta, T_INT)
print(f"  Int ~ a     -> 代换 a = {type_str(ta, u.subst)}")
u.unify(tb, t_arrow(ta, ta))
print(f"  b ~ a -> a  -> 代换 b = {type_str(tb, u.subst)}")
print(f"  最终代换表: { {k: type_str(v, u.subst) for k, v in u.subst.items()} }")

print("\n== 箭头结构合一 ==")
u2 = Unifier()
# (a -> b) ~ (Int -> Bool)  =>  a=Int, b=Bool
u2.unify(t_arrow(t_var("a"), t_var("b")), t_arrow(T_INT, T_BOOL))
print(f"  (a->b) ~ (Int->Bool): a = {type_str(t_var('a'), u2.subst)}, "
      f"b = {type_str(t_var('b'), u2.subst)}")

print("\n== 失败情形 1：类型冲突 ==")
u3 = Unifier()
try:
    u3.unify(T_INT, T_BOOL)
except UnifyError as exc:
    print(f"  Int ~ Bool -> {exc}")

print("\n== 失败情形 2：occurs check（无限类型）==")
u4 = Unifier()
try:
    # a ~ a -> a：解不存在（有限类型中无解）
    u4.unify(t_var("a"), t_arrow(t_var("a"), t_var("a")))
except OccursError as exc:
    print(f"  a ~ a->a -> {exc}")
print("  没有 occurs check 就会造出无限类型 —— λx.x x 之所以不可类型化")

print("\n== 变量链与 walk ==")
u5 = Unifier()
u5.unify(t_var("a"), t_var("b"))
u5.unify(t_var("b"), T_INT)
print(f"  a=b, b=Int -> walk(a) = {type_str(t_var('a'), u5.subst)}")
print(f"  walk 只走链不递归；walk_deep 深入箭头结构内部")

print("\n== 合一在泛型编程中的影子 ==")
for line in (
    "  Rust/TS 的泛型推导：let v = vec![1,2] -> Vec<i32> 由合一得出",
    "  SQL 参数绑定、JSON Schema 校验都是受限的合一",
    "  Prolog 直接把合一当执行模型 —— 变量未绑定就是类型变量",
    "  下一课：把合一装进 λ 演算 = 完整的 Hindley-Milner 推断",
):
    print("  -", line)

print("\n== 小结 ==")
for line in (
    "  合一 = 『找出一组赋值使两个类型相等』的算法",
    "  walk 跟随代换链；bind 时重写旧代换保持全局一致",
    "  occurs check 是类型系统健壮性的守门员",
    "  失败不是错误而是『类型不符』的诊断信息来源",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「合一求解所有解」：对完全未约束的两个变量，枚举有限域上的代换。
# 2. 把代换表改成持久化的（917 课路径复制），支持「尝试性合一 + 回溯」。
# 3. 实现 tuple 类型的合一 (a,b) ~ (Int, b) 并报告部分绑定。
# 4. 思考：occurs check 的复杂度是多少？为什么工业实现会用「延迟 occurs」？
