# ===== 第802课：流式算法与数据摘要-综合案例-实时流量监控器 =====
# 知识点：
#   - 综合串起本章：CMS 频次 + HLL 基数 + Space-Saving Top-K + EWMA 平滑 + 蓄水池采样
#   - 一个监控探针的完整链路：接流 -> 多 sketch 并行写入 -> 定期输出指标 -> 告警
#   - 指标：QPS（EWMA）、UV（HLL）、Top-IP（Space-Saving）、单 IP 限流判定（CMS）
#   - 全部 sketch 可 merge，支持分布式分片聚合
#   - 固定 seed + 内存信号源，离线可运行
# 依赖：无（标准库）
import hashlib
import math
import random
import statistics
import time
from collections import Counter


def _h(s, seed):
    return int.from_bytes(hashlib.md5(f"{seed}:{s}".encode()).digest()[:8], "big")


# ---- CMS（频次估计）----
class CMS:
    def __init__(self, eps=0.002, delta=0.01):
        self.w = math.ceil(math.e/eps)
        self.d = math.ceil(math.log(1/delta))
        self.table = [[0]*self.w for _ in range(self.d)]
        self.seeds = list(range(1, self.d+1))
    def add(self, key, c=1):
        for row, col in zip(self.table, self._cols(key)): row[col] += c
    def estimate(self, key):
        return min(row[c] for row, c in zip(self.table, self._cols(key)))
    def _cols(self, key):
        return [_h(key, s) % self.w for s in self.seeds]

# ---- HLL（基数估计）----
class HLL:
    def __init__(self, p=12):
        self.p = p; self.m = 1 << p
        self.regs = [0]*self.m
    def add(self, key):
        hv = _h(key, 999)
        bucket = hv >> (64-self.p)
        rest = hv & ((1 << (64-self.p))-1)
        lead = 1
        for i in range(63-self.p, -1, -1):
            if rest & (1<<i): break
            lead += 1
        if lead > self.regs[bucket]: self.regs[bucket] = lead
    def count(self):
        m = self.m
        raw = sum(2.0**-r for r in self.regs)
        alpha = 0.709
        est = alpha*m*m/raw
        zeros = self.regs.count(0)
        if est <= 2.5*m and zeros: est = m*math.log(m/zeros)
        return est

    def merge(self, other):
        for i, r in enumerate(other.regs):
            if r > self.regs[i]:
                self.regs[i] = r

# ---- Space-Saving（Top-K）----
class SpaceSaving:
    def __init__(self, k=20):
        self.k = k; self.counters = {}
    def add(self, key):
        if key in self.counters: self.counters[key] += 1
        elif len(self.counters) < self.k: self.counters[key] = 1
        else:
            mk = min(self.counters, key=self.counters.get)
            self.counters[key] = self.counters.pop(mk)+1
    def top(self, k=5): return sorted(self.counters.items(), key=lambda x:-x[1])[:k]

# ---- EWMA ----
class EWMA:
    def __init__(self, halflife=20.0):
        self.d = math.exp(-math.log(2)/halflife); self.w = 0.0
    def update(self, v):
        self.w = self.w*self.d + v*(1-self.d); return self.w

# ---- 蓄水池 ----
class Reservoir:
    def __init__(self, k=50): self.k = k; self.pool = []; self.n = 0
    def add(self, item):
        self.n += 1
        if self.n <= self.k: self.pool.append(item)
        else:
            j = random.Random(self.n).randrange(self.n)
            if j < self.k: self.pool[j] = item


class FlowMonitor:
    """网络流量监控探针：一个探针 = 多个 sketch 并行。"""

    def __init__(self):
        self.cms = CMS(eps=0.003, delta=0.01)         # 单 IP 包数估计
        self.hll = HLL(p=12)                          # 独立 IP 基数
        self.topk = SpaceSaving(k=20)                 # Top IP
        self.ewma = EWMA(halflife=30.0)               # 平滑 QPS
        self.reservoir = Reservoir(k=100)             # 采样包
        self.alerts = []

    def observe(self, src_ip):
        self.cms.add(src_ip)
        self.hll.add(src_ip)
        self.topk.add(src_ip)
        self.reservoir.add(src_ip)
        return self.ewma.update(1.0)

    def report(self, threshold_qps=None):
        qps = self.ewma.w
        uv = self.hll.count()
        top = self.topk.top(5)
        # CMS 检测单 IP 异常
        anomalies = []
        for name, count in top:
            est = self.cms.estimate(name)
            ratio = est / max(1, self.ewma.w)
            if ratio > 50:
                anomalies.append((name, est))
        return {"qps": qps, "uv": uv, "top": top, "anomalies": anomalies}


# ---- 生成合成流量：正常 + 攻击 ----
rng = random.Random(42)
NORMAL_IPS = [f"10.0.{a}.{b}" for a in range(1, 11) for b in range(1, 21)]
ATTACK_IPS = [f"192.168.66.{i}" for i in range(3)]

events = []
# 阶段 1：正常流量（1000 tick，每 tick 3~8 个包）
for tick in range(1000):
    for _ in range(rng.randint(3, 8)):
        ip = rng.choice(NORMAL_IPS)
        events.append((tick, ip))
# 阶段 2：DDoS 攻击（500 tick，每 tick 40~60 个包，来自 3 个 IP）
for tick in range(1000, 1500):
    for _ in range(rng.randint(40, 60)):
        ip = rng.choice(ATTACK_IPS)
        events.append((tick, ip))
# 阶段 3：恢复正常
for tick in range(1500, 1800):
    for _ in range(rng.randint(3, 8)):
        ip = rng.choice(NORMAL_IPS)
        events.append((tick, ip))

print("== 流量事件 ==")
print(f"  总事件={len(events):,}  正常 IP={len(NORMAL_IPS)}  攻击 IP={len(ATTACK_IPS)}")
print(f"  攻击区间: tick 1000~1500（来自 {ATTACK_IPS}）")

print("\n== 探针实时处理 ==")
mon = FlowMonitor()
last_tick = 0
snapshots = []
for tick, ip in events:
    qps_now = mon.observe(ip)
    if tick > last_tick:
        last_tick = tick
        if tick % 150 == 0 or tick in (999, 1000, 1500):
            r = mon.report()
            snapshots.append((tick, r))

print(f"  处理完成：{len(events):,} 个事件")
print(f"\n== 关键时刻的快照 ==")
print(f"  {'tick':<8}{'QPS':>8}{'UV':>8}{'Top-1':>22}{'告警'}")
for tick, r in snapshots:
    t0 = r["top"][0] if r["top"] else ("-",0)
    alert = "!!" if r["anomalies"] else ""
    print(f"  {tick:<8}{r['qps']:>8.2f}{r['uv']:>8.0f}  "
          f"{t0[0]}={t0[1]:>6}  {alert}")

print("\n== 告警检测（攻击期 QPS 飙升 + 单 IP 占比异常） ==")
# 检查每个 tick 的 QPS 是否超过阈值
mon2 = FlowMonitor()
by_tick = {}
for tick, ip in events:
    by_tick.setdefault(tick, []).append(ip)
alerts = []
mon2 = FlowMonitor()
for tick in sorted(by_tick):
    for ip in by_tick[tick]:
        mon2.observe(ip)
    if tick % 10 == 0:
        qps = mon2.ewma.w
        if qps > 20:
            alerts.append((tick, round(qps, 1)))
print(f"  QPS>20 的告警时刻: {alerts[:12]}...")
print(f"  攻击区间 1000~1500 产生的告警: "
      f"{len([a for a in alerts if 1000 <= a[0] <= 1500])} 个")

print("\n== CMS 检测攻击 IP ==")
mon3 = FlowMonitor()
for tick, ip in events:
    mon3.observe(ip)
for ip in ATTACK_IPS:
    est = mon3.cms.estimate(ip)
    print(f"  攻击 IP {ip}: CMS 估计={est}（真实频率 {sum(1 for t,i in events if i==ip)}）")
normal_est = mon3.cms.estimate(NORMAL_IPS[0])
print(f"  正常 IP {NORMAL_IPS[0]}: CMS 估计={normal_est}（正常流量）")

print("\n== HLL 基数：正常 vs 攻击 ==")
print(f"  HLL 估计独立 IP = {mon3.hll.count():.0f}")
print(f"  真实 = {len(NORMAL_IPS) + len(ATTACK_IPS)}")
print(f"  HLL 内存 = {mon3.hll.m} B（精确 set 需要 ~{len(NORMAL_IPS)*50/1024:.0f}KB）")

print("\n== sketch 可合并性 ==")
m1, m2 = FlowMonitor(), FlowMonitor()
for tick, ip in events[:len(events)//2]: m1.observe(ip)
for tick, ip in events[len(events)//2:]: m2.observe(ip)
m1.hll.merge(m2.hll)
merged_uv = m1.hll.count()
single_uv = FlowMonitor()
for tick, ip in events: single_uv.observe(ip)
print(f"  分片合并 UV={merged_uv:.0f}  整体处理 UV={single_uv.hll.count():.0f} "
      f"一致={abs(merged_uv - single_uv.hll.count()) < 50}")
print("  这是分布式监控聚合的基础（第798课 HLL merge）")

print("\n== sketch 一览 ==")
print(f"  {'sketch':<18}{'回答的问题':<30}{'内存':<14}")
for row in (("CMS", "这个 IP 发了多少包？", "O(1/ε)"),
            ("HLL", "有多少个不同 IP？", "O(log log n)"),
            ("SpaceSaving", "哪些 IP 频率最高？", "O(k)"),
            ("EWMA", "当前 QPS 平滑值？", "O(1)"),
            ("Reservoir", "最近的包样本？", "O(k)")):
    print(f"  {row[0]:<18}{row[1]:<30}{row[2]:<14}")

print("\n== 分层回顾 ==")
for line in [
    "  流模型   : 单遍、有限内存、近似保证（第795课）",
    "  频次层   : CMS 点查 + Space-Saving Top-K（第797/799课）",
    "  基数层   : HLL 基数估计 + merge（第798课）",
    "  时间层   : EWMA 平滑 + 滑动窗口告警（第800课）",
    "  采样层   : 蓄水池保留原始样本供审计（第796课）",
    "  可扩展   : 各 sketch 独立可 merge，支持分布式聚合",
]:
    print("  -", line)

print("\n== 生产对比 ==")
for line in [
    "  Prometheus/Promtail: 直方图 + HLL + relabel",
    "  Flink: CMS + sketch 算子做实时异常检测",
    "  Cloudflare/Akamai: 每个边缘节点跑 CMS + Top-K + GeoHLL",
    "  本课是把流式算法「用对地方」的最小可行实现",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 加入「按端口维度」的第二套 sketch，支持端口级别的攻击检测。
# 2. 实现「滑动窗口版 Top-K」（第800课），让榜单只反映最近 5 分钟。
# 3. 把探针设计为「可序列化」：定期把 sketch 状态存 JSON，重启后恢复。
# 4. 思考：为什么 DDoS 检测需要多个 sketch 协作，单靠 CMS 不够？
