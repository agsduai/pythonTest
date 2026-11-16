# ===== 第859课：操作系统原理与资源管理-CPU调度算法 =====
# 知识点：
#   - 调度目标：吞吐量、周转时间、等待时间、公平性与响应时间之间的权衡
#   - FCFS：先来先服务，简单但对短作业不友好（护航效应）
#   - SJF/SRTF：最短(剩余)作业优先，平均等待最优，但需要预知时长、长作业饥饿
#   - Round Robin：时间片轮转，公平且响应快；量子越小切换开销越大
#   - 本课用离散时间步模拟，逐一统计每种算法的等待/周转时间
# 依赖：无（标准库）
from collections import deque


class Proc:
    def __init__(self, pid, arrive, burst):
        self.pid = pid
        self.arrive = arrive
        self.burst = burst

    def __repr__(self):
        return f"P{self.pid}"


def finish_times(timeline):
    """timeline: [(t, pid)] -> {pid: 完成时刻}"""
    ft = {}
    for t, pid in timeline:
        ft[pid] = t + 1
    return ft


def stats(procs, timeline):
    ft = finish_times(timeline)
    turnaround = {p.pid: ft[p.pid] - p.arrive for p in procs}
    waiting = {p.pid: turnaround[p.pid] - p.burst for p in procs}
    return {
        "avg_wait": sum(waiting.values()) / len(procs),
        "avg_turn": sum(turnaround.values()) / len(procs),
        "waiting": waiting,
        "turnaround": turnaround,
    }


def fcfs(procs):
    t, timeline = 0, []
    for p in sorted(procs, key=lambda x: (x.arrive, x.pid)):
        if t < p.arrive:
            t = p.arrive
        for _ in range(p.burst):
            timeline.append((t, p.pid))
            t += 1
    return timeline


def sjf(procs):
    bursts = {p.pid: p.burst for p in procs}     # 用副本，避免污染原数据
    t, done, timeline = 0, 0, []
    while done < len(procs):
        ready = [p for p in procs if p.arrive <= t and bursts[p.pid] > 0]
        if not ready:
            t = min(p.arrive for p in procs if bursts[p.pid] > 0)
            continue
        p = min(ready, key=lambda x: (bursts[x.pid], x.arrive, x.pid))
        for _ in range(bursts[p.pid]):
            timeline.append((t, p.pid))
            t += 1
        bursts[p.pid] = 0
        done += 1
    return timeline


def srtf(procs):
    remaining = {p.pid: p.burst for p in procs}
    t, done, timeline = 0, 0, []
    while done < len(procs):
        ready = [p for p in procs if p.arrive <= t and remaining[p.pid] > 0]
        if not ready:
            t += 1
            continue
        p = min(ready, key=lambda x: (remaining[x.pid], x.arrive, x.pid))
        remaining[p.pid] -= 1
        timeline.append((t, p.pid))
        t += 1
        if remaining[p.pid] == 0:
            done += 1
    return timeline


def round_robin(procs, quantum=2):
    order = sorted(procs, key=lambda x: (x.arrive, x.pid))
    remaining = {p.pid: p.burst for p in procs}
    queue = deque()
    i, t, done = 0, 0, 0
    timeline = []
    while done < len(procs):
        while i < len(order) and order[i].arrive <= t:
            queue.append(order[i])
            i += 1
        if not queue:
            t += 1
            continue
        p = queue.popleft()
        run = min(quantum, remaining[p.pid])
        for _ in range(run):
            timeline.append((t, p.pid))
            t += 1
        remaining[p.pid] -= run
        while i < len(order) and order[i].arrive <= t:
            queue.append(order[i])
            i += 1
        if remaining[p.pid] > 0:
            queue.append(p)
        else:
            done += 1
    return timeline


def gantt(timeline, width=60):
    """把时间线压缩成甘特图字符串。"""
    cells = [f"{pid}" if pid is not None else "." for _, pid in timeline]
    return "".join(cells)[:width]


procs = [Proc(1, 0, 7), Proc(2, 2, 4), Proc(3, 4, 1), Proc(4, 5, 4)]

print("== 进程集（到达时间, 突发长度）==")
for p in procs:
    print(f"  P{p.pid}: arrive={p.arrive}  burst={p.burst}")

print("\n== 四种算法的时间线（每字符 = 1 时间单位）==")
results = {}
for name, tl in (("FCFS", fcfs(procs)),
                 ("SJF ", sjf(procs)),
                 ("SRTF", srtf(procs)),
                 ("RR(2)", round_robin(procs, 2))):
    results[name] = stats(procs, tl)
    print(f"  {name}: {gantt(tl)}")

print("\n== 指标对比 ==")
print(f"  {'算法':<8}{'平均等待':>10}{'平均周转':>10}")
for name, st in results.items():
    print(f"  {name:<8}{st['avg_wait']:>10.2f}{st['avg_turn']:>10.2f}")
print("  SJF/SRTF 的平均等待最优；FCFS 因短作业被长作业押后而吃亏")

print("\n== RR 时间片的影响 ==")
print(f"  {'量子':>6}{'平均等待':>10}{'平均周转':>10}")
for q in (1, 2, 3, 4, 7):
    st = stats(procs, round_robin(procs, q))
    print(f"  {q:>6}{st['avg_wait']:>10.2f}{st['avg_turn']:>10.2f}")
print("  量子越大 RR 越接近 FCFS；越小响应越好但切换开销越大")

print("\n== 护航效应演示 ==")
convoy = [Proc(1, 0, 10), Proc(2, 1, 1), Proc(3, 2, 1)]
for name, tl in (("FCFS", fcfs(convoy)), ("RR(2)", round_robin(convoy, 2))):
    st = stats(convoy, tl)
    print(f"  {name}: {gantt(tl)}  短作业 P2/P3 等待 = "
          f"{st['waiting'][2]}/{st['waiting'][3]}")
print("  FCFS 下 1 时间的短作业要等 10+；RR 让它 2 个时间片内就开始跑")

print("\n== 小结 ==")
for line in (
    "  调度算法没有全局最优：SJF 等待最优但需预知时长，RR 公平但周转偏高",
    "  时间离散模拟 = 每个时间步做一次调度决策，足以看清机制",
    "  真实 OS（如 Linux CFS）用红黑树按虚拟运行时间调度，思想仍是公平分片",
    "  下一课：内存侧的页面置换算法",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现多级反馈队列（3 个队列，量子 1/2/4，进程降级），与 RR 对比等待时间。
# 2. 给 SJF 加「老化」：等待越久优先级越高（有效突发 = burst - wait/2），验证
#    长作业不再无限饥饿。
# 3. 在甘特图中加入空闲区间（用 "." 表示 CPU 空转），并统计 CPU 利用率。
# 4. 思考：量子从 1 增大到进程最大突发，RR 的行为如何逐渐退化为 FCFS？
