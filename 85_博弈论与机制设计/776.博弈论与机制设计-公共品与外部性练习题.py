# ===== 第776课：博弈论与机制设计-公共品与外部性 =====
# 知识点：
#   - 公共品：非排他、非竞争（路灯、开源软件、清洁空气）；易出现搭便车
#   - 自愿贡献博弈 VCM：个人边际收益 < 社会边际收益 -> 纳什贡献低于社会最优
#   - 社会最优由萨缪尔森条件决定：Σ MRS = MRT（边际替代率之和 = 边际转换率）
#   - 外部性：私人成本 ≠ 社会成本；庇古税/补贴把外部性内部化
#   - 公地悲剧：共享资源被过度使用；配额、产权、可交易许可证是常见解法
#   - 与第772课重复博弈呼应：重复互动 + 惩罚可 sustain 合作
# 依赖：无（标准库）

print("== 自愿贡献博弈（线性公共品）==")
# n 人，每人初始禀赋 e=10，可选择贡献 g_i 到公共池；
# 公共品回报乘数 M：每贡献 1 单位，所有人各得 M/n。
# 个人收益 u_i = (e - g_i) + (M/n)·Σg_j
n, e, M = 5, 10.0, 3.0
alpha = M / n                 # 个人从公共池拿回的边际系数 0.6
print(f"  {n} 人, 禀赋={e}, 乘数 M={M}, 个人边际回报 M/n={alpha}")
print(f"  私人边际成本=1, 私人边际收益={alpha} < 1 -> 不贡献是占优策略")

def utility_i(g_i, others_sum):
    return (e - g_i) + alpha * (g_i + others_sum)

print("\n== 单人最优反应 ==")
for others_sum in (0, 10, 30, 40):
    u0 = utility_i(0, others_sum)
    u10 = utility_i(10, others_sum)
    print(f"  其他人共贡献 {others_sum:>2}: 我贡献0得{u0:.1f}, 贡献10得{u10:.1f} "
          f"-> 最优 {'搭便车' if u0>u10 else '全贡献'}")

print("\n== 纳什均衡 vs 社会最优 ==")
# NE: 所有人 g=0
g_ne = [0.0]*n
payoff_ne = sum(utility_i(g, sum(g_ne)-g) for g in g_ne)
# 社会最优：总福利 = n·e + (M-n)·Σg ; M>n 时全贡献最优
g_so = [e]*n
payoff_so = sum(utility_i(g, sum(g_so)-g) for g in g_so)
print(f"  NE: 全不贡献, 总福利={payoff_ne:.1f}")
print(f"  社会最优: 全贡献, 总福利={payoff_so:.1f}")
print(f"  效率损失 = {1-payoff_ne/payoff_so:.1%}（搭便车导致的无谓损失）")
print(f"  个体在 NE 的收益={utility_i(0,0):.1f}, 在社会最优={utility_i(10,40):.1f} "
      f"-> 人人其实都更好，但没人有单方面动机改")

print("\n== 参数敏感性：M 决定困境强度 ==")
for M2 in (1.0, 2.0, 4.0, 5.0, 6.0):
    a = M2/n
    ne = n*e                                    # 全不贡献
    so = n*e + (M2-n)*n*e if M2 > n else n*e
    print(f"  M={M2:<4}: M/n={a:.2f} -> {'有搭便车困境' if a<1 else '个人也愿意贡献'}, "
          f"效率损失={1-ne/so:.0%}" if so else "")
print("  M>n 时全贡献是社会最优；M<n 时连社会最优都是不贡献")

print("\n== 庇古税/补贴：把外部性内部化 ==")
# 每贡献 1 单位给补贴 s = 1 - alpha，让私人边际收益补齐到 1
s = 1 - alpha
print(f"  给每单位贡献补贴 s=1-M/n={s:.2f}")
for others_sum in (0, 20, 40):
    u0 = utility_i(0, others_sum)
    u10 = utility_i(10, others_sum) + s*10
    print(f"  其他人贡献 {others_sum:>2}: 贡献0(含补贴)={u0:.1f}, "
          f"贡献10(含补贴)={u10:.1f} -> {'愿意贡献' if u10>u0 else '仍搭便车'}")
print("  补贴把私人边际收益抬到 1，个人最优与社会最优一致")
print("  对称地，负外部性（污染）应征庇古税 = 边际损害")

print("\n== 公地悲剧 ==")
# 共享牧场：n 个牧民各放 x_i 头牛，总牛数 X=Σx_i
# 每头牛收益 v(X) = a - b·X（拥挤），成本 c
a, b, c = 100.0, 1.0, 10.0
def profit_i(x, others):
    X = x + others
    return x*(a - b*X - c) if a - b*X - c > 0 else 0.0
print(f"  每头牛收益 v(X)={a}-{b}·X, 成本={c}")
# NE: 对称下 x_i = (a-c)/(b(n+1))；社会最优 x_i = (a-c)/(2bn)
x_ne = (a-c)/(b*(n+1))
x_so = (a-c)/(2*b*n)
X_ne, X_so = n*x_ne, n*x_so
print(f"  NE 每人放 {x_ne:.2f} 头, 总 {X_ne:.1f} 头, 总利润={n*profit_i(x_ne,(n-1)*x_ne):.1f}")
print(f"  社会最优每人 {x_so:.2f} 头, 总 {X_so:.1f} 头, "
      f"总利润={n*profit_i(x_so,(n-1)*x_so):.1f}")
print(f"  过度使用: 总牛数多 {X_ne/X_so-1:.0%}，总利润反而更低")

print("\n== 解法对照 ==")
for line in (
    "  庇古税: 每头牛征 b·X_ne 的拥挤税，把私人边际成本抬到社会成本",
    "  配额/产权: 直接把资源分成 n 份，各自内部化拥挤",
    "  可交易许可证(cap-and-trade): 总量封顶 + 市场分配，兼顾效率与灵活",
    "  社区自治(Ostrom): 重复互动 + 监督 + 分级惩罚，也能长期可持续",
):
    print(" ", line)

print("\n== 与机制设计的关系 ==")
for line in [
    "  公共品供给需要「成本分担规则」，VCG 可用但预算不平衡",
    "  Groves-Ledyard / dAGVA 机制试图兼顾 IC 与预算平衡",
    "  林达尔均衡：按个人边际收益定价，但偏好 elicitation 难",
    "  与第773/774课拍卖、显示原理同属「设计规则对齐个体与社会目标」",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现带惩罚的重复公共品博弈，观察合作能否维持（第772课）。
# 2. 计算 cap-and-trade 下的许可证均衡价格，验证等于庇古税率。
# 3. 用 VCG 决定「是否建路灯 + 各自分摊多少」，检查预算是否平衡。
# 4. 思考：为什么「人人收益都更高」的社会最优仍不是纳什均衡？
