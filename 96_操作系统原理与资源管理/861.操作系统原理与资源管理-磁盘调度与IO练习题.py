# ===== 第861课：操作系统原理与资源管理-磁盘调度与I/O =====
# 知识点：
#   - 机械盘寻道时间是主要延迟来源 -> 磁盘臂调度决定 I/O 吞吐
#   - FCFS：按请求顺序服务，公平但磁臂来回大幅摆动
#   - SSTF：每次选最近请求 —— 总移动小，但边缘请求饥饿
#   - SCAN（电梯）：沿一个方向扫到底再折返；C-SCAN：到底后跳回另一端单向扫
#   - LOOK/C-LOOK：不到物理端点，到最远请求即折返（SCAN 的工程优化）
# 依赖：无（标准库）


def fcfs_disk(head, reqs):
    order, total, cur = list(reqs), 0, head
    for r in order:
        total += abs(cur - r)
        cur = r
    return order, total


def sstf_disk(head, reqs):
    pending, order, total, cur = list(reqs), [], 0, head
    while pending:
        nxt = min(pending, key=lambda r: (abs(r - cur), r))
        pending.remove(nxt)
        total += abs(cur - nxt)
        cur = nxt
        order.append(nxt)
    return order, total


def scan_disk(head, reqs, max_cyl, direction=1):
    """SCAN：沿方向扫到盘端（含端点），再折返。"""
    right = sorted(r for r in reqs if r >= head)
    left = sorted((r for r in reqs if r < head), reverse=True)
    seq = right + [max_cyl] + left if direction == 1 else left + [0] + right
    total, cur = 0, head
    for r in seq:
        total += abs(cur - r)
        cur = r
    return seq, total


def cscan_disk(head, reqs, max_cyl):
    """C-SCAN：单向扫描，到端点跳回 0 继续同向扫。"""
    right = sorted(r for r in reqs if r >= head)
    left = sorted(r for r in reqs if r < head)
    seq = right + [max_cyl, 0] + left
    total, cur = 0, head
    for r in seq:
        total += abs(cur - r)
        cur = r
    return seq, total


def look_disk(head, reqs, direction=1):
    """LOOK：SCAN 但不到端点，到最远请求即折返。"""
    right = sorted(r for r in reqs if r >= head)
    left = sorted((r for r in reqs if r < head), reverse=True)
    seq = right + left if direction == 1 else left + right
    total, cur = 0, head
    for r in seq:
        total += abs(cur - r)
        cur = r
    return seq, total


print("== 请求队列 ==")
head, max_cyl = 53, 199
reqs = [98, 183, 37, 122, 14, 124, 65, 67]
print(f"  磁头在 {head}（柱面 0~{max_cyl}），请求 {reqs}")

print("\n== 五种算法 ==")
print(f"  {'算法':<10}{'服务顺序':<44}{'总移动':>8}")
for name, (seq, total) in (
    ("FCFS", fcfs_disk(head, reqs)),
    ("SSTF", sstf_disk(head, reqs)),
    ("SCAN", scan_disk(head, reqs, max_cyl, 1)),
    ("C-SCAN", cscan_disk(head, reqs, max_cyl)),
    ("LOOK", look_disk(head, reqs, 1)),
):
    print(f"  {name:<10}{str(seq):<44}{total:>8}")
print("  SSTF 移动最小；SCAN/C-SCAN 用有序大扫除避免饥饿")

print("\n== SSTF 的饥饿演示 ==")
far_reqs = [10, 190]
near_stream = [55, 60, 58, 62]
pending = far_reqs + near_stream
cur, order = head, []
while pending:
    nxt = min(pending, key=lambda r: (abs(r - cur), r))
    pending.remove(nxt)
    order.append(nxt)
    cur = nxt
print(f"  磁头 {head}，远端请求 {far_reqs}，持续到达近端请求 {near_stream}")
print(f"  SSTF 服务顺序 = {order}")
print(f"  远端请求 {far_reqs} 被排到最后 —— 长期负载下可能永远得不到服务")
print(f"  SCAN 则保证每个方向一圈内必然轮到")

print("\n== SCAN vs LOOK：端点开销 ==")
small = [60, 70]
seq_scan, t_scan = scan_disk(head, small, max_cyl, 1)
seq_look, t_look = look_disk(head, small, 1)
print(f"  请求 {small}: SCAN 顺序={seq_scan} 总移动={t_scan}")
print(f"           LOOK 顺序={seq_look} 总移动={t_look}")
print(f"  LOOK 少走 {t_scan - t_look}（不去无请求的端点）—— 现代磁盘多用 LOOK 类策略")

print("\n== C-SCAN 的均匀等待 ==")
print("  SCAN 折返方向上刚被越过的请求要等一个来回")
print("  C-SCAN 单向循环 -> 各柱面最大等待时间一致，适合负载重的服务器")

print("\n== 顺序访问 vs 随机访问 ==")
seq_reqs = list(range(head, head + 40))
rand_reqs = [10, 120, 30, 180, 50, 90]
_, t_seq = sstf_disk(head, seq_reqs)
_, t_rand = sstf_disk(head, rand_reqs)
print(f"  40 个顺序请求总移动 ≈ {t_seq}（接近线性）")
print(f"  6 个随机请求总移动   ≈ {t_rand}")
print("  这就是为什么数据库顺序扫描远快于随机点查，也是预读存在的理由")

print("\n== 小结 ==")
for line in (
    "  磁盘调度与 CPU 调度同构：都是等待队列 + 服务顺序策略",
    "  SSTF 最优化单步、SCAN 最优化公平；LOOK 是工程取舍",
    "  SSD 没有磁臂，调度退化为 NCQ 命令排队 —— 算法随硬件演化",
    "  下一课：不用「事后检测」而用「事前规避」处理死锁的银行家算法",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 C-LOOK：跳回时直接到最小请求柱面（不落到 0），与 C-SCAN 对比总移动。
# 2. 给请求加到达时间，实现「SSTF + 老化」：等待超过阈值就强制提升优先级。
# 3. 模拟电梯高峰：两个方向持续请求，统计 SCAN 下每个请求的最大等待时间。
# 4. 思考：SSD 的 FTL 内部为什么仍需要类似调度的机制（写放大、垃圾回收）？
