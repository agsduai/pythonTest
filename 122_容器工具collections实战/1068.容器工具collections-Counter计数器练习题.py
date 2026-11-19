# ===== 第1068课：容器工具collections-Counter计数器 =====
# 知识点：
#   - Counter(可迭代对象)：自动统计每个元素出现次数，本质是 dict 子类
#   - 取值与 dict 一样：c["键"]；键不存在返回 0 而不是报错
#   - update() 追加统计、c1 + c2 相加、c1 - c2 相减
#   - 实际场景：词频统计、投票计数、库存变化累加

# 案例一：统计字母出现次数
from collections import Counter

text = "abracadabra"
c = Counter(text)
print(f"统计结果：{c}")
print(f"a 出现：{c['a']} 次")
print(f"不存在的键 'z'：{c['z']}")  # 返回 0，不会 KeyError

# 案例二：统计列表元素
# 场景：统计投票结果
votes = ["小张", "小李", "小张", "小王", "小李", "小张"]
votes_count = Counter(votes)
print(f"得票：{dict(votes_count)}")
print(f"小张得票：{votes_count['小张']}")

# 案例三：update 追加统计
# 场景：上午统计完，下午的选票继续累加
counter = Counter(["苹果", "牛奶"])
counter.update(["苹果", "面包"])  # 追加
print(f"追加后：{counter}")

# 案例四：Counter 相加减
# 场景：入库 + 出库 = 当前库存
stock_in = Counter({"苹果": 10, "牛奶": 5})
stock_out = Counter({"苹果": 3, "牛奶": 8, "面包": 2})
current = stock_in - stock_out  # 只保留正数部分
print(f"当前库存：{current}")  # 牛奶 8-5=3？不对：入库5-出库8=-3，负数被丢弃
print("注意：相减会丢弃负数项，需要负数时用普通 dict 手动算")

# 案例五：统计字符串中单词
sentence = "the quick brown fox jumps over the lazy dog the fox"
word_counter = Counter(sentence.split())
print(f"词频：{word_counter}")

# ===== 练习题 =====
# 1. 统计字符串 "hello world hello python" 中每个单词出现次数，打印 Counter。
# 2. 列表 [1, 2, 2, 3, 3, 3, 4]，用 Counter 统计后打印出现次数最多的元素及次数（手动找最大值，下一课讲 most_common）。
# 3. 用 Counter 统计 ["A","B","A"] 和 ["A","C"]，先 update 合并再打印总结果。
