# ===== 第862课：操作系统原理与资源管理-银行家算法与死锁避免 =====
# 知识点：
#   - 死锁四个必要条件：互斥、占有等待、不可剥夺、循环等待
#   - 825 课的锁排序是「破坏循环等待」；银行家算法是「动态规避」
#   - 银行家算法：仅当「分配后系统仍处于安全状态」才批准资源请求
#   - 安全状态 = 存在某种完成顺序（安全序列），让所有进程都能拿到最大需求
#   - 代价：必须预知每个进程的最大需求（Max 矩阵），且执行保守
# 依赖：无（标准库）


def need_matrix(alloc, maxm):
    return [[maxm[i][j] - alloc[i][j] for j in range(len(alloc[0]))]
            for i in range(len(alloc))]


def is_safe(avail, alloc, maxm):
    """银行家安全性检查 -> (是否安全, 安全序列)。"""
    n, m = len(alloc), len(avail)
    need = need_matrix(alloc, maxm)
    work = list(avail)
    finish = [False] * n
    seq = []
    while len(seq) < n:
        progressed = False
        for i in range(n):
            if not finish[i] and all(need[i][j] <= work[j] for j in range(m)):
                for j in range(m):
                    work[j] += alloc[i][j]
                finish[i] = True
                seq.append(i)
                progressed = True
        if not progressed:
            break
    return len(seq) == n, seq


def request(avail, alloc, maxm, pid, req):
    """处理请求：三步检查 -> (批准?, 消息, 新alloc)。"""
    n, m = len(alloc), len(avail)
    need = need_matrix(alloc, maxm)
    if any(req[j] > need[pid][j] for j in range(m)):
        return False, f"P{pid} 请求超过其声明的最大需求（涉嫌撒谎，拒绝）", alloc
    if any(req[j] > avail[j] for j in range(m)):
        return False, f"P{pid} 请求超过当前可用资源，进入等待", alloc
    # 试探性分配
    trial = [row[:] for row in alloc]
    trial_avail = list(avail)
    for j in range(m):
        trial[pid][j] += req[j]
        trial_avail[j] -= req[j]
    safe, seq = is_safe(trial_avail, trial, maxm)
    if not safe:
        return False, f"P{pid} 分配后系统不安全（找不到安全序列），拒绝并回滚", alloc
    return True, f"P{pid} 请求批准，安全序列 P{'->P'.join(str(i) for i in seq)}", trial


print("== 系统快照：5 进程 3 类资源（A/B/C），总量 10/5/7 ==")
alloc = [[0, 1, 0], [2, 0, 0], [3, 0, 2], [2, 1, 1], [0, 0, 2]]
maxm = [[7, 5, 3], [3, 2, 2], [9, 0, 2], [2, 2, 2], [4, 3, 3]]
avail = [10 - sum(a[0] for a in alloc),
         5 - sum(a[1] for a in alloc),
         7 - sum(a[2] for a in alloc)]
need = need_matrix(alloc, maxm)
print(f"  {'进程':<6}{'Alloc(A,B,C)':<16}{'Max(A,B,C)':<14}{'Need(A,B,C)'}")
for i in range(5):
    print(f"  P{i:<5}{str(tuple(alloc[i])):<16}{str(tuple(maxm[i])):<14}{tuple(need[i])}")
print(f"  Available = {tuple(avail)}")

print("\n== 安全性检查 ==")
safe, seq = is_safe(avail, alloc, maxm)
print(f"  安全: {safe}   安全序列: P{' -> P'.join(str(i) for i in seq)}")
print("  推演：P1 只差 (1,2,2) 可满足 -> 完成后归还 -> P3 可满足 -> ... 全部完成")

print("\n== 请求仲裁 ==")
cases = [
    ("P1 请求 (1,0,2)", 1, [1, 0, 2]),
    ("P4 请求 (3,3,0)", 4, [3, 3, 0]),
    ("P0 请求 (0,2,0)", 0, [0, 2, 0]),
]
for label, pid, req in cases:
    ok, msg, _ = request(avail, alloc, maxm, pid, req)
    print(f"  {label}: {'批准' if ok else '拒绝'} -> {msg}")

print("\n== 拒绝后的状态保持不变 ==")
ok4, msg4, _ = request(avail, alloc, maxm, 4, [3, 3, 0])
print(f"  P4 被拒后 Available 仍为 {tuple(avail)}（回滚，等待他人释放）")

print("\n== 与死锁检测/锁排序的对比 ==")
for line in (
    "  825 课锁排序：设计期破坏「循环等待」，运行零开销，但要求全序加锁",
    "  死锁检测（等待图找环）：事后发现 + 剥夺/回滚，代价大",
    "  银行家算法：事前规避，每次申请做 O(n²m) 安全性检查",
    "  适用前提：最大需求可预知。通用系统做不到，所以真实 OS 不用银行家",
    "  银行家思想活在数据库/交易系统：预留额度、现金储备检查",
):
    print("  -", line)

print("\n== 全量消耗压力测试 ==")
bad_max = [[7, 5, 3], [3, 2, 2], [9, 0, 2], [2, 2, 2], [4, 3, 3]]
big_alloc = [[7, 4, 3], [3, 1, 2], [0, 0, 0], [0, 0, 0], [0, 0, 0]]
big_avail = [0, 0, 2]
safe2, seq2 = is_safe(big_avail, big_alloc, bad_max)
print(f"  资源几乎耗尽（Available={tuple(big_avail)}）: 安全={safe2}"
      f"{'' if safe2 else '，任何新请求都会被拒绝直到有进程释放'}")

print("\n== 小结 ==")
for line in (
    "  银行家算法 = 「先假装分配 -> 检查还能不能全员完成 -> 决定批不批」",
    "  安全序列不唯一，找到任意一个即可；找不到才拒绝",
    "  它牺牲并发度换取不死锁的保证 —— 典型的保守策略",
    "  下一课：内存分配的伙伴系统",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「资源释放」流程：某进程完成并释放全部资源后重新做安全性检查。
# 2. 实现死锁检测算法（资源分配图化简/等待图找环），构造一个真正死锁的快照，
#    与银行家的「拒绝进入」对比。
# 3. 让银行家支持「多次申请累计」：进程分多次申请资源，每次都做检查。
# 4. 思考：为什么通用操作系统不用银行家算法？「最大需求不可预知」本质上
#    违背了死锁四条件的哪一条的破坏思路？
