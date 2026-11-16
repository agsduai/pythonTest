# ===== 第775课：博弈论与机制设计-匹配市场与稳定婚姻 =====
# 知识点：
#   - 稳定婚姻问题 stable marriage：n 男 n 女各有偏好序，找没有「阻塞对」的匹配
#   - 阻塞对 blocking pair：(m,w) 彼此都比当前伴侣更喜欢对方 -> 匹配不稳定
#   - Gale-Shapley（延迟接受）算法：男方轮流求婚、女方保留当前最优并暂拒其余
#   - 结果稳定且对「求婚方最优 / 被求婚方最劣」；O(n²) 时间
#   - 医院/住院医师匹配 NRMP、学校择校、 kidney exchange 都基于此
#   - 稳定室友问题（单边匹配）不一定有稳定解，比双边难
# 依赖：无（标准库）
import random

men = ["A","B","C","D"]
women = ["W","X","Y","Z"]
M_PREF = {
    "A": ["Y","X","Z","W"],
    "B": ["X","Y","W","Z"],
    "C": ["Y","W","X","Z"],
    "D": ["X","Z","Y","W"],
}
W_PREF = {
    "W": ["A","D","B","C"],
    "X": ["C","A","B","D"],
    "Y": ["B","D","A","C"],
    "Z": ["D","C","B","A"],
}


def rank(pref, person):
    return pref.index(person)


def gale_shapley(m_pref, w_pref, proposers=None):
    """延迟接受：返回 {男: 女}。"""
    proposers = proposers or list(m_pref)
    w_rank = {w: {m: r for r, m in enumerate(pref)} for w, pref in w_pref.items()}
    free = list(proposers)
    next_idx = {m: 0 for m in proposers}
    held = {}            # 女 -> 当前暂定男
    proposals = 0
    while free:
        m = free.pop(0)
        if next_idx[m] >= len(m_pref[m]):
            continue                     # 偏好列表用尽（不完全列表时可能）
        w = m_pref[m][next_idx[m]]
        next_idx[m] += 1
        proposals += 1
        if w not in held:
            held[w] = m
        elif w_rank[w][m] < w_rank[w][held[w]]:
            # 女方更爱新求婚者：原持有者被拒，回到队列继续求婚
            free.append(held[w])
            held[w] = m
        else:
            # 女方更爱现任：当前求婚者被拒，回去求下一个
            free.append(m)
    return {m: w for w, m in held.items()}, proposals


def find_blocking_pairs(matching, m_pref, w_pref):
    inv = {w: m for m, w in matching.items()}
    bad = []
    for m in m_pref:
        for w in m_pref[m]:
            if w == matching[m]: break           # 遇到现任就没更喜欢的了
            cur_w = matching[m]
            cur_m = inv.get(w)
            if (rank(w_pref[w], m) < rank(w_pref[w], cur_m)):
                bad.append((m, w, cur_w, cur_m))
    return bad


print("== 偏好表 ==")
for m in men: print(f"  {m}: {M_PREF[m]}")
for w in women: print(f"  {w}: {W_PREF[w]}")

match, n_prop = gale_shapley(M_PREF, W_PREF)
print("\n== Gale-Shapley（男方求婚）结果 ==")
print(f"  匹配={match}  总求婚次数={n_prop}")
for m, w in sorted(match.items()):
    print(f"    {m} - {w}  (男方偏好序第 {rank(M_PREF[m],w)+1} 位, "
          f"女方偏好序第 {rank(W_PREF[w],m)+1} 位)")
inv = {w: m for m, w in match.items()}      # 女 -> 男

print("\n== 稳定性校验 ==")
bad = find_blocking_pairs(match, M_PREF, W_PREF)
print(f"  阻塞对数量={len(bad)} -> {'稳定' if not bad else bad}")

print("\n== 换成女方求婚（结果偏向另一方）==")
# 把偏好表转置，女方当求婚方
M_PREF_T = {w: list(pref) for w, pref in W_PREF.items()}
W_PREF_T = {m: list(pref) for m, pref in M_PREF.items()}
match2, n2 = gale_shapley(M_PREF_T, W_PREF_T)
match2 = {w: m for m, w in match2.items()}    # 转回 女->男 再展示
print(f"  女方求婚匹配: {match2}  求婚次数={n2}")
inv2 = {m: w for w, m in match2.items()}
print("  两种结果对比:")
for w in women:
    print(f"    {w}: 男求婚时配 {inv.get(w)}, 女求婚时配 {inv2.get(w)}, "
          f"她更喜欢 {'女求婚' if rank(W_PREF[w],inv2.get(w)) < rank(W_PREF[w],inv.get(w)) else '男求婚'} 的结果")
print("  求婚方得到自己可能的最优稳定匹配，被求婚方得到最劣稳定匹配")

print("\n== 随机偏好：稳定婚姻总存在 ==")
for n in (4, 10, 30):
    ms = [f"m{i}" for i in range(n)]; ws = [f"w{i}" for i in range(n)]
    rng = random.Random(n)
    mp = {m: rng.sample(ws, n) for m in ms}
    wp = {w: rng.sample(ms, n) for w in ws}
    mt, props = gale_shapley(mp, wp)
    blocking = find_blocking_pairs(mt, mp, wp)
    print(f"  n={n:>2}: 求婚次数={props:>4}（≤n²={n*n}）, "
          f"阻塞对={len(blocking)} -> 稳定={not blocking}")

print("\n== 匹配任意（不一定稳定）会怎样 ==")
rng = random.Random(9)
random_match = dict(zip(men, rng.sample(women, len(women))))
print(f"  随机匹配: {random_match}")
bad_random = find_blocking_pairs(random_match, M_PREF, W_PREF)
print(f"  阻塞对={len(bad_random)}: {[(m,w) for m,w,_,_ in bad_random[:4]]}")
print("  这些人有动机私奔 -> 市场会瓦解，稳定是机制可用性的底线")

print("\n== 算法性质 ==")
for line in (
    "  一定终止：每次求婚消耗一个「尚未尝试」的偏好项，最多 n² 次",
    "  结果稳定：Gale-Shapley 证明无阻塞对",
    "  求婚方最优 / 被求婚方最劣（在所有稳定匹配中）",
    "  被求婚方谎报偏好有时能获益 -> 对双方都策略防护的稳定机制不存在",
):
    print(" ", line)

print("\n== 应用与扩展 ==")
for line in [
    "  NRMP 住院医师匹配、纽约/波士顿公立学校择校",
    "  肾脏交换（带环/链的匹配，NP 难变体）",
    "  广告位分配、云计算 VM 到物理机放置",
    "  与第773课拍卖对比：这里没有钱，偏好序是序数不可转移",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 枚举 4×4 的所有稳定匹配，验证「求婚方最优」性质。
# 2. 实现「稳定室友」问题（单边）并给出一个无稳定解的实例。
# 3. 给 Gale-Shapley 加「不完全偏好列表/不可接受对」，处理未匹配者。
# 4. 思考：为什么稳定婚姻里无法做到对双方都策略防护？
