# ===== 第897课：模型检测与形式化验证-程序验证与循环不变量 =====
# 知识点：
#   - 程序验证三要素：前置条件 + 后置条件 + 循环不变量
#   - 不变量归纳法：初始成立 + 每步保持 => 循环任意时刻都成立
#   - 有界模型检查（BMC）：把循环展开 k 次，编码成 SAT/算术约束找反例
#   - 不变量找错人的能力：错的不变量「归纳不成立」，反例自动出现
#   - 与 896 课的关系：程序状态空间 = 模型；不变量 = AG 性质
# 依赖：无（标准库）


def reachable_states(init, step_fn, guard_fn, max_steps=64):
    """枚举程序可达状态（显式模型检测）。"""
    seen = {init}
    frontier = [init]
    while frontier and len(seen) < max_steps:
        new_frontier = []
        for state in frontier:
            nxt = step_fn(state)
            if guard_fn(nxt) and nxt not in seen:
                seen.add(nxt)
                new_frontier.append(nxt)
        frontier = new_frontier
    return seen


def check_invariant(init, step_fn, guard_fn, invariant, max_steps=64):
    """所有可达状态都满足不变量？返回 (通过, 违反状态)。"""
    states = reachable_states(init, step_fn, guard_fn, max_steps)
    bad = [s for s in states if not invariant(s)]
    return len(bad) == 0, bad[:3]


print("== 程序 1：求和 1+2+...+n（n≤5）==")
print("""
  i := 1; s := 0
  while i <= n:
      s := s + i
      i := i + 1
  assert s == n*(n+1)/2
""")
n_bound = 5
init_sum = (1, 0)                                   # (i, s)


def sum_step(state, n=n_bound):
    i, s = state
    return (i + 1, s + i) if i <= n else state


def sum_guard(state, n=n_bound):
    return state[0] <= n + 1


def invariant_sum(state):
    i, s = state
    expected = (i - 1) * i // 2
    return s == expected and 1 <= i <= n_bound + 1


ok, bad = check_invariant(init_sum, sum_step, sum_guard, invariant_sum, 100)
print(f"  不变量: s == i(i-1)/2 ∧ 1 ≤ i ≤ n+1")
states = reachable_states(init_sum, sum_step, sum_guard, 100)
print(f"  可达状态数 = {len(states)}")
print(f"  全部满足: {ok}" + ("" if ok else f"  违反状态: {bad}"))
final = [s for s in states if s[0] == n_bound + 1]
print(f"  终止状态: {final} -> s = n(n+1)/2 ✓")
print("  归纳三步：初始 (1,0) 满足；每步 s+=i 后关系保持；故任意时刻成立")


print("\n== 程序 2：有 bug 的求和（漏加第一项）==")
print("""
  i := 2; s := 0            # 从 2 开始 —— 错误
  while i <= n:
      s := s + i
      i := i + 1
""")
init_bug = (2, 0)


def bug_step(state, n=n_bound):
    i, s = state
    return (i + 1, s + i) if i <= n else state


def bug_guard(state, n=n_bound):
    return state[0] <= n + 1


def invariant_bug(state):
    i, s = state
    expected = (i - 1) * i // 2 - 1               # bug 版的正确不变量是少 1
    return s == (i - 1) * i // 2 - 1


ok_bug, bad_bug = check_invariant(init_bug, bug_step, bug_guard, invariant_bug, 100)
print(f"  不变量: s == i(i-1)/2 − 1（与 bug 版程序匹配）")
print(f"  该不变量归纳成立: {ok_bug}")
def post_ok(state, n=n_bound):
    i, s = state
    return s == n * (n + 1) // 2
final_bug = [s for s in reachable_states(init_bug, bug_step, bug_guard, 100)
             if s[0] == n_bound + 1]
print(f"  终止状态: {final_bug}")
print(f"  后置条件 s == n(n+1)/2 成立: {[post_ok(s) for s in final_bug]}")
print("  -> 反例：s = n(n+1)/2 − 1 ≠ n(n+1)/2，程序有错")


print("\n== 有界模型检查：把循环展开成约束 ==")
print("""
  BMC(k=3)：展开循环 3 次，检查可达状态是否违反不变量
  约束: s1 = s0 + i0; i1 = i0 + 1; s2 = s1 + i1; ...
  找到违反点即反例；找不到只能说「前 k 步没问题」（完备性靠归纳）
""")
for k in (1, 2, 3, 6):
    state = init_bug
    violated = False
    trace = [state]
    for _ in range(k):
        state = bug_step(state)
        trace.append(state)
        if not invariant_sum(state):
            violated = True
    print(f"  k={k}: 违反旧不变量 s==i(i-1)/2 -> {violated}，迹 = {trace}")
print("  BMC 找反例快（SAT 驱动），归纳法证正确 —— 二者互补（CEGIS 思想）")


print("\n== 程序 3：不变量找错（除零风险）==")


def div_step(state):
    x, y = state
    return (x - 1, y)


def div_invariant(state):
    x, y = state
    return y != 0                                  # 想证 y 恒非零


states_div = reachable_states((5, 0), div_step, lambda s: True, 20)
bad_div = [s for s in states_div if not div_invariant(s)]
print("  程序: x := 5; y := 0; while x > 0: x := x - 1; (y 不再更新)")
print(f"  不变量 y≠0 的可达检查: {not bad_div}  违反状态样例: {bad_div[:2]}")
print("  y 初始就是 0 -> 不变量根本不成立 —— 初始条件也要被检查")


print("\n== 归纳验证的完整流程 ==")
for line in (
    "  1. 猜不变量 I（难点！常由人给或 CEGIS 自动合成）",
    "  2. 验证初始状态满足 I（初始化成立）",
    "  3. 验证 I 在每步转移后保持（归纳步）",
    "  4. 验证 I ∧ 终止条件 → 后置条件",
    "  失败时用有界检查/可达性枚举找反例，修程序或修不变量",
):
    print("  -", line)

print("\n== 小结 ==")
for line in (
    "  程序验证 = 模型检测的符号化版本：状态无限时靠不变量抽象",
    "  BMC 找 bug 快、归纳证明对 —— 工业工具（如 CBMC）两条路都走",
    "  不变量是程序的『数学说明书』：写得好，验证就是机械劳动",
    "  898 课综合：验证并发协议的互斥性质",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 为「斐波那契循环」猜不变量并用可达性枚举验证（提示：与黄金比例的
#    封闭式有关）。
# 2. 实现 CEGIS 雏形：BMC 找反例 -> 从反例猜新不变量 -> 再验证，循环两轮。
# 3. 验证「二分查找不变量」：lo ≤ mid ≤ hi 且 target 不在 [lo,hi) 之外。
# 4. 思考：为什么循环不变量本质上无法全自动推导？（与 791 课停机问题呼应）
