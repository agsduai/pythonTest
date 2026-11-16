# ===== 第860课：操作系统原理与资源管理-页面置换算法 =====
# 知识点：
#   - 虚拟内存按页管理；物理帧不够时必须「置换」某页出去
#   - 缺页率是置换算法好坏的核心指标；引用串（access string）是评测输入
#   - FIFO：换最早进来的页 —— 有 Belady 异常（帧多缺页反而多）
#   - LRU：换最久未用的页（用过去近似未来）；OPT：换未来最久不用的页（理论下界）
#   - Clock（二次机会）：给页一个引用位，环状指针扫描，兼顾 LRU 效果与实现成本
# 依赖：无（标准库）


def fifo(refs, frames_n):
    frames, pointer, faults = [], 0, 0
    for r in refs:
        if r in frames:
            continue
        faults += 1
        if len(frames) < frames_n:
            frames.append(r)
        else:
            frames[pointer] = r
            pointer = (pointer + 1) % frames_n
    return faults


def lru(refs, frames_n):
    frames, faults = [], 0            # 按最近使用时间排序，末尾最近
    for r in refs:
        if r in frames:
            frames.remove(r)
            frames.append(r)
            continue
        faults += 1
        if len(frames) >= frames_n:
            frames.pop(0)
        frames.append(r)
    return faults


def opt(refs, frames_n):
    frames, faults = [], 0
    for i, r in enumerate(refs):
        if r in frames:
            continue
        faults += 1
        if len(frames) < frames_n:
            frames.append(r)
            continue
        future = refs[i + 1:]

        def next_use(x):
            return future.index(x) if x in future else len(future) + 1

        victim = max(frames, key=next_use)
        frames[frames.index(victim)] = r
    return faults


def clock_algo(refs, frames_n):
    frames = []                       # [page, refbit]
    pointer, faults = 0, 0
    for r in refs:
        hit = next((i for i, (pg, _) in enumerate(frames) if pg == r), None)
        if hit is not None:
            frames[hit][1] = 1
            continue
        faults += 1
        if len(frames) < frames_n:
            frames.append([r, 1])
            continue
        while True:
            pg, rb = frames[pointer]
            if rb == 1:
                frames[pointer][1] = 0          # 给第二次机会
                pointer = (pointer + 1) % frames_n
            else:
                frames[pointer] = [r, 1]        # 淘汰引用位为 0 的页
                pointer = (pointer + 1) % frames_n
                break
    return faults


print("== 引用串 ==")
refs = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1]
print(f"  {refs}（{len(refs)} 次访问）")

print("\n== 3 帧 vs 4 帧：各算法缺页数 ==")
algos = ("FIFO", "LRU", "OPT", "Clock")
funcs = (fifo, lru, opt, clock_algo)
print(f"  {'算法':<8}{'3帧':>6}{'4帧':>6}{'3帧命中率':>10}{'4帧命中率':>10}")
for name, fn in zip(algos, funcs):
    f3, f4 = fn(refs, 3), fn(refs, 4)
    print(f"  {name:<8}{f3:>6}{f4:>6}{1 - f3/len(refs):>10.1%}{1 - f4/len(refs):>10.1%}")
print("  OPT 是理论下界；LRU 接近 OPT；FIFO 最差但实现最便宜")

print("\n== Belady 异常：帧越多缺页越多 ==")
belady = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]
for name, fn in (("FIFO", fifo), ("LRU", lru), ("OPT", opt)):
    counts = [fn(belady, f) for f in (3, 4)]
    mark = " <- 异常！" if counts[1] > counts[0] else ""
    print(f"  {name:<6} 3帧={counts[0]}  4帧={counts[1]}{mark}")
print("  FIFO 在这条经典引用串上：4 帧比 3 帧多 1 次缺页（LRU/OPT 无此现象）")

print("\n== Clock 算法逐步过程（3 帧，前 8 次访问）==")
frames, pointer, faults = [], 0, 0
step_refs = refs[:8]
for r in step_refs:
    hit = next((i for i, (pg, _) in enumerate(frames) if pg == r), None)
    if hit is not None:
        frames[hit][1] = 1
        print(f"  访问 {r}: 命中，置引用位 = 1")
        continue
    faults += 1
    if len(frames) < 3:
        frames.append([r, 1])
        print(f"  访问 {r}: 缺页，装入 -> 帧={[pg for pg, _ in frames]}")
        continue
    print(f"  访问 {r}: 缺页，Clock 扫描（指针={pointer}）", end=" ")
    while True:
        pg, rb = frames[pointer]
        if rb == 1:
            frames[pointer][1] = 0
            pointer = (pointer + 1) % 3
            print(f"[{pg} 获得第二次机会]", end=" ")
        else:
            frames[pointer] = [r, 1]
            pointer = (pointer + 1) % 3
            print(f"淘汰 {pg} -> 帧={[p for p, _ in frames]}")
            break

print("\n== 局部性演示：两种工作集切换 ==")
phase_a = [1, 2, 3] * 6
phase_b = [4, 5, 6] * 6
mixed = phase_a + phase_b
for name, fn in (("LRU", lru), ("FIFO", fifo)):
    print(f"  {name}: 纯A段缺页 {fn(phase_a, 3)}, 切换后总缺页 {fn(mixed, 3)}"
          f"（切换瞬间旧工作集全被换出）")
print("  缺页集中在「阶段切换」处 —— 这正是工作集模型要解决的问题")

print("\n== 小结 ==")
for line in (
    "  置换算法在用「历史」或「预知未来」近似真正的使用模式",
    "  OPT 不可实现但是基准；LRU 好但硬件成本高；Clock 是工程折中",
    "  FIFO 简单，但 Belady 异常说明它没有捕捉任何使用模式",
    "  下一课：磁盘臂调度（同样的思想换到 I/O 侧）",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现工作集模型：维护最近 τ 次访问的集合，统计不同 τ 下缺页数的变化。
# 2. 实现 LFU（最不经常使用）置换，与 LRU 在「热页偶发冷访」模式下对比。
# 3. 给 Clock 加「脏位」：被修改过的页淘汰成本 ×2，统计两种策略的加权代价。
# 4. 思考：为什么现代 CPU 的 TLB 与操作系统页缓存都用近似 LRU 而不是精确 LRU？
