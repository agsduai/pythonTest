# ===== 第228课：常用标准库-collections-Counter与defaultdict =====
# 知识点：
#   - Counter：计数器，一行统计频次，most_common 取 TopN
#   - defaultdict：带默认值的字典，省去“键不存在”的判断
#   - 两者都是 dict 的子类，可以和普通字典互转

from collections import Counter, defaultdict

words = "apple banana apple cherry banana apple".split()
c = Counter(words)
print(c)                        # Counter({'apple': 3, 'banana': 2, ...})
print(c.most_common(2))         # 前 2 名
print(c["banana"], c["不存在的词"])    # 缺失的键返回 0，不报错

c.update(["banana", "date"])    # 继续计数
print(c["banana"], c["date"])

# 统计字符频次
print(Counter("mississippi").most_common(3))

# defaultdict：访问不存在的键时自动创建默认值
scores = defaultdict(list)
records = [("一班", 90), ("二班", 85), ("一班", 78), ("二班", 92)]
for cls, score in records:
    scores[cls].append(score)      # 不需要先判断键是否存在
print(dict(scores))

# 普通 dict 的等价写法（对比繁琐程度）
normal = {}
for cls, score in records:
    normal.setdefault(cls, []).append(score)
print(normal)

# 组合技：按首字母归类单词
by_initial = defaultdict(list)
for w in words:
    by_initial[w[0]].append(w)
print(dict(by_initial))

# ===== 练习题 =====
# 1. 统计一段英文里出现次数最多的 5 个单词（先转小写再统计）。
# 2. 用 defaultdict(int) 统计每个班级的人数。
# 3. 用 Counter 验证一副牌洗牌后没有重复（配合第234课 random）。
# 4. 思考：defaultdict 与 dict.setdefault 各适合什么场景？
