# ===== 第898课：模型检测与形式化验证-综合案例-互斥协议验证器 =====
# 知识点：
#   - 综合：Kripke 结构(895) + 可达性/不变量(895) + 不动点/CTL(896) + 环检测
#   - Peterson 互斥协议：两个进程的并发交错 —— 状态空间 = 交错语义的乘积
#   - 安全性质（互斥）：可达状态中「双临界区」必须为空 —— BFS 检查
#   - 活性性质（无饥饿）：不存在「卡死在等待」的可达环 —— 三色 DFS 找环
#   - 反例提取：破坏协议的版本直接给出交错序列 —— 并发 bug 的教科书读法
# 依赖：无（标准库）
from collections import deque

IDLE, WANT, CS = 0, 1, 2


def step_peterson(state, who):
    """Peterson 协议的一个原子步骤。
    P1 进入条件：¬flag2 ∨ turn=1；P2 进入条件：¬flag1 ∨ turn=0。"""
    pc1, pc2, flag1, flag2, turn = state
    if who == 1:
        if pc1 == IDLE:
            return (WANT, pc2, True, flag2, turn)      # 想进：先举旗
        if pc1 == WANT:
            if not flag2 or turn == 1:                 # 对方没来 或 让权给我
                return (CS, pc2, flag1, flag2, turn)
            return None                                # 等待（无状态变化）
        return (IDLE, pc2, False, flag2, turn)         # 退出临界区
    else:
        if pc2 == IDLE:
            return (pc1, WANT, flag1, True, turn)
        if pc2 == WANT:
            if not flag1 or turn == 0:
                return (pc1, CS, flag1, flag2, turn)
            return None
        return (pc1, IDLE, flag1, False, turn)


def step_naive(state, who):
    """坏协议：只有 turn 的朴素轮流（进入时检查一次，之后不再复查）。"""
    pc1, pc2, turn = state
    if who == 1:
        if pc1 == IDLE:
            return (WANT, pc2, 0)
        if pc1 == WANT:
            return (CS, pc2, 0) if turn == 0 else None
        return (IDLE, pc2, turn)
    else:
        if pc2 == IDLE:
            return (pc1, WANT, 1)
        if pc2 == WANT:
            return (pc1, CS, 1) if turn == 1 else None
        return (pc1, IDLE, turn)


def successors(state, protocol="peterson"):
    step = step_naive if protocol == "naive" else step_peterson
    out = set()
    for who in (1, 2):
        nxt = step(state, who)
        if nxt is not None:
            out.add(nxt)
    return out


def explore(initial, protocol="peterson"):
    """BFS 可达状态 + 父指针（用于反例回溯）。"""
    seen = {initial: None}
    queue = deque([initial])
    while queue:
        v = queue.popleft()
        for w in successors(v, protocol):
            if w not in seen:
                seen[w] = v
                queue.append(w)
    return seen


def find_violation(seen):
    """找双临界区状态并回溯反例路径。"""
    for s in seen:
        if s[0] == CS and s[1] == CS:
            path = [s]
            while seen[s] is not None:
                s = seen[s]
                path.append(s)
            return list(reversed(path))
    return None


def has_stuck_cycle(seen, who):
    """饥饿检测：可达图中是否存在「进程 who 全程停在 WANT」的环（三色 DFS）。"""
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {s: WHITE for s in seen}
    found = []

    def dfs(s, stack):
        color[s] = GRAY
        stack.append(s)
        for w in successors(s):
            if w not in seen:
                continue
            if color[w] == GRAY:
                cycle = stack[stack.index(w):]
                if all((s2[0] == WANT if who == 1 else s2[1] == WANT)
                       for s2 in cycle):
                    found.append(list(cycle))
            elif color[w] == WHITE:
                dfs(w, stack)
        stack.pop()
        color[s] = BLACK

    dfs(next(iter(seen)), [])
    return found


def deadlocks(seen, protocol="peterson"):
    return [s for s in seen if not successors(s, protocol)]


print("== Peterson 互斥协议 ==")
print("""
  P1: flag1:=true; turn:=0;  while flag2∧turn=0: 等待; 进临界区; flag1:=false
  P2: flag2:=true; turn:=1;  while flag1∧turn=1: 等待; 进临界区; flag2:=false
""")
init = (IDLE, IDLE, False, False, 0)

print("== 正确协议：安全性质（互斥）==")
seen_ok = explore(init)
double_cs = [s for s in seen_ok if s[0] == CS and s[1] == CS]
print(f"  可达状态数 = {len(seen_ok)}")
print(f"  双临界区可达状态 = {double_cs if double_cs else '无'}")
print(f"  互斥性质 AG ¬(双临界区): {'成立 ✓' if not double_cs else '被违反'}")

print("\n== 无死锁与饥饿检查 ==")
dl = deadlocks(seen_ok)
print(f"  死锁状态 = {dl if dl else '无'}（等待者的自旋用『无变化步』表示）")
stuck = has_stuck_cycle(seen_ok, 1)
print(f"  P1 永久停在 WANT 的可达环 = {stuck if stuck else '无'}")
print(f"  饥饿性质 AF 离开 WANT: {'成立 ✓' if not stuck else '被违反'}")
print("  直觉：turn 轮流让权，等待者最多等对方用完一轮临界区")

print("\n== 坏协议：只有 turn 的朴素轮流 ==")
print("""
  P1: turn:=0;  if turn=0: 进临界区
  P2: turn:=1;  if turn=1: 进临界区
  （进入后不再复查 —— turn 只是「入场券」而非「互斥锁」）
""")
init_naive = (IDLE, IDLE, 0)
seen_bad = explore(init_naive, protocol="naive")
cex = find_violation(seen_bad)
print(f"  可达状态数 = {len(seen_bad)}")
if cex:
    print(f"  双临界区可达！反例（交错序列，共 {len(cex)} 步）:")
    for i, s in enumerate(cex):
        pc1, pc2, turn = s
        tag = f"P1:{['空闲', '想进', '临界区'][pc1]}  P2:{['空闲', '想进', '临界区'][pc2]}  turn={turn}"
        print(f"    第{i}步: {tag}")
    print("  P1 检查完 turn 后，P2 改写 turn 并入场 —— 检查与进入之间没有保护")
else:
    print("  未找到违反（不应该）")

print("\n== 状态空间爆炸的直观感受 ==")
print(f"  单进程状态 = pc(3) × flag(2) = 6；两进程乘积 × turn(2) = 72")
print(f"  Peterson 实际可达 = {len(seen_ok)}（不可达组合被交互约束剪掉）")
print(f"  朴素协议可达 = {len(seen_bad)}")
print("  n 个进程的交错按 n! 增长 —— 状态爆炸；对策：偏序/对称约简、BDD、抽象")

print("\n== 协议验证检查单 ==")
for line in (
    "  安全性：AG ¬(双临界区) —— 可达性检查（BFS 一次搞定）",
    "  无死锁：每个可达状态有后继 —— 与安全检查同一次遍历",
    "  活性：AF 离开等待 —— 需要环检测（三色 DFS / Büchi 自动机）",
    "  反例质量：交错序列直接对应并发调试时的线程日志",
):
    print("  -", line)

print("\n== 小结 ==")
for line in (
    "  并发协议 = 状态机乘积；交错语义让小协议也有可观的状态空间",
    "  Peterson 用一个 turn 变量同时解决互斥与无饥饿 —— 优雅的算法设计",
    "  模型检测器（SPIN/TLA+）就是把本章流程做到工业级",
    "  形式化闭环：建模(71章) + 性质(895) + 检查(896/898) + 反例修复",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 给验证器加「无死锁」检查：所有可达状态都有后继，报告卡死状态。
# 2. 实现 Lamport 面包店算法建模，与 Peterson 对比状态数与性质结果。
# 3. 把进程数推广到 3 个（回合制数组），观察状态空间的增长倍数。
# 4. 思考：为什么 Peterson 需要「对方的 flag」和「turn」两条信息？删掉 flag
#    只留 turn 会退化成什么（提示：朴素协议）？删掉 turn 呢（提示：死锁）？
