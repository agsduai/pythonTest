# ===== 第1104课：itertools迭代工具-permutations排列 =====
# 知识点：
#   - permutations(序列, r)：从 n 个里取 r 个"排顺序"的所有方式，nPr = n!/(n-r)!
#   - 排列考虑顺序：(A, B) 和 (B, A) 算两种
#   - r 不写时默认全排列 n!，元素多了数量爆炸，注意规模
#   - 实际场景：比赛出场顺序、密码排列、日程排序枚举

# 案例一：3 选 2 的排列
import itertools

runners = ["小张", "小李", "小王"]
pairs = list(itertools.permutations(runners, 2))
print(f"两人接力共 {len(pairs)} 种顺序：")
for a, b in pairs:
    print(f"  {a} -> {b}")

# 案例二：全排列
# 场景：3 首歌的播放顺序共 3! = 6 种
songs = ["A歌", "B歌", "C歌"]
playlists = list(itertools.permutations(songs))
print(f"播放顺序 {len(playlists)} 种：")
for pl in playlists:
    print(f"  {' -> '.join(pl)}")

# 案例三：排列与组合的数量对比
# 4 人里选 2 人照相：排列 12 种（谁站左谁站右），组合 6 种（只看是谁）
people = ["甲", "乙", "丙", "丁"]
n_perm = len(list(itertools.permutations(people, 2)))
n_comb = len(list(itertools.combinations(people, 2)))
print(f"4 选 2：排列 {n_perm} 种，组合 {n_comb} 种（排列是组合的 2 倍）")

# 案例四：数字排列找符合条件的数
# 场景：用 1、2、3 能组成哪些两位数
digits = ["1", "2", "3"]
two_digit = [int(a + b) for a, b in itertools.permutations(digits, 2)]
print(f"可组成的两位数：{sorted(two_digit)}")

# 案例五：规模提醒
import math
print(f"5 个元素全排列 {math.factorial(5)} 种，10 个就是 {math.factorial(10)} 种")
print("全排列只适合小规模枚举，别对大列表使用")

# ===== 练习题 =====
# 1. 用 permutations 打印 "ABC" 的所有全排列（应为 6 种）。
# 2. 4 名选手的"前三名领奖顺序"共多少种？用 permutations(people, 3) 验证等于 24。
# 3. 用数字 0~9 的排列做一个"猜数字游戏候选集"：只取前 3 位排列（permutations("0123456789", 3)）输出前 5 个候选串。
