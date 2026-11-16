# ===== 第679课：随机模拟与蒙特卡洛-排队论与离散事件模拟 =====
# 知识点：
#   - 离散事件模拟 DES：维护「未来事件优先队列」，时间跳到下一个事件
#   - M/M/1 模型：泊松到达（指数间隔）、指数服务时间、1 个服务台、FIFO
#   - Little 定律 L = λW：平均队长 = 到达率 × 平均逗留时间（普适，不依赖分布）
#   - 理论值：ρ=λ/μ，L=ρ/(1-ρ)，W=1/(μ-λ)；ρ≥1 队列爆炸
#   - 与「固定步长时钟」对比：DES 只在事件时刻推进，效率高且无步长误差
#   - 用 heapq 管理事件，可注入到达/服务时间序列便于单测
# 依赖：无（标准库）
import heapq
import math
import random
import statistics

ARRIVAL, DEPARTURE = 0, 1


class MM1:
    def __init__(self, lam, mu, seed=1):
        self.lam, self.mu, self.rng = lam, mu, random.Random(seed)

    def exp_interval(self, rate):
        return -math.log1p(-self.rng.random()) / rate

    def run(self, n_customers=10000):
        events = []
        t = 0.0
        # 预排首个到达
        heapq.heappush(events, (0.0, ARRIVAL, 0))
        queue, busy = [], False
        area_q, area_sys = 0.0, 0.0      # 积分：人数 × 时间
        last = 0.0
        system_times = []
        n_done = 0
        arrival_times = {}
        served = 0

        while events and served < n_customers:
            now, kind, cid = heapq.heappop(events)
            dt = now - last
            area_q += len(queue) * dt
            area_sys += (len(queue) + (1 if busy else 0)) * dt
            last = now

            if kind == ARRIVAL:
                arrival_times[cid] = now
                queue.append(cid)
                # 排下一个到达
                nxt = now + self.exp_interval(self.lam)
                heapq.heappush(events, (nxt, ARRIVAL, cid + 1))
                if not busy:
                    busy = True
                    c = queue.pop(0)
                    dep = now + self.exp_interval(self.mu)
                    heapq.heappush(events, (dep, DEPARTURE, c))
            else:
                served += 1
                a = arrival_times.pop(cid, now)
                system_times.append(now - a)          # 系统逗留时间（含服务）
                if queue:
                    c = queue.pop(0)
                    dep = now + self.exp_interval(self.mu)
                    heapq.heappush(events, (dep, DEPARTURE, c))
                else:
                    busy = False
        T = last
        return {
            "T": T, "served": served,
            "Lq": area_q / T, "L": area_sys / T,
            "W": statistics.fmean(system_times),
            "throughput": served / T,
        }


print("== M/M/1 理论值 ==")
def theory(lam, mu):
    rho = lam / mu
    if rho >= 1:
        return {"rho": rho, "L": float("inf"), "W": float("inf")}
    return {"rho": rho, "L": rho / (1 - rho), "Lq": rho**2 / (1 - rho),
            "W": 1 / (mu - lam), "Wq": rho / (mu - lam)}

for lam, mu in ((0.5, 1.0), (0.8, 1.0), (0.95, 1.0), (1.2, 1.0)):
    th = theory(lam, mu)
    print(f"  λ={lam:<5} μ={mu:<4} ρ={th['rho']:<5} L={th['L']:<10.3f} W={th['W']:.3f}")

print("\n== 离散事件模拟（N=20000 顾客）==")
for lam in (0.5, 0.8, 0.95):
    sim = MM1(lam, 1.0, seed=7).run(20000)
    th = theory(lam, 1.0)
    print(f"  λ={lam}: L模拟={sim['L']:.3f}/理论={th['L']:.3f}  "
          f"W模拟={sim['W']:.3f}/理论={th['W']:.3f}  "
          f"吞吐={sim['throughput']:.3f}")

print("\n== Little 定律 L = λW 验证 ==")
for lam in (0.5, 0.8):
    s = MM1(lam, 1.0, seed=11).run(20000)
    lhs, rhs = s["L"], s["throughput"] * s["W"]
    print(f"  λ={lam}: L={lhs:.4f}  λ_eff·W={rhs:.4f}  相对差={abs(lhs-rhs)/lhs:.2%}")

print("\n== ρ 接近 1 时队列爆炸 ==")
for lam in (0.5, 0.8, 0.9, 0.95, 0.99):
    s = MM1(lam, 1.0, seed=3).run(5000)
    print(f"  ρ={lam:<5}: L模拟={s['L']:>8.2f}  理论 L={lam/(1-lam):>8.2f}")

print("\n== DES vs 固定步长 ==")
for line in (
    "  固定步长: 每个 Δt 都扫描一次系统，Δt 小则慢、大则有离散误差",
    "  DES     : 只在「到达/离开」时刻推进，事件数 ∝ 顾客数",
    "  DES 需要优先队列按时间排序，同刻事件要定义稳定的 tie-break",
    "  本例用 (time, kind, cid) 三元组，kind/cid 保证顺序确定",
):
    print(" ", line)

print("\n== 事件类型扩展 ==")
for line in [
    "  多服务台 M/M/c：busy 改成「空闲台数」计数",
    "  优先级队列 / 超时放弃（renege）/ 服务台休息",
    "  非指数服务时间 M/G/1：换 exp_interval 为任意分布",
    "  生产用 SimPy；本课手写便于理解事件循环",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 修正本例：分别记录「排队等待 Wq」与「系统逗留 W」，验证 W = Wq + 1/μ。
# 2. 实现 M/M/2 双服务台，对比同等 λ 下的 L 与 W。
# 3. 增加「顾客等待超过 T 就放弃」，测量放弃率随 ρ 的变化。
# 4. 思考：为什么 ρ≥1 时队列长度趋于无穷，模拟却不会真的卡死？
