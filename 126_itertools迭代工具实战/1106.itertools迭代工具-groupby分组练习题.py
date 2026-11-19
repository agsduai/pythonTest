# ===== 第1106课：itertools迭代工具-groupby分组 =====
# 知识点：
#   - groupby(序列, key)：把"相邻的相同键"分成一组，返回 (键, 组迭代器)
#   - 最大陷阱：它只对"相邻"元素分组，用前必须先 sorted 排序！
#   - 每组的迭代器只能消费一次，要保存内容需 list() 立即展开
#   - 实际场景：按班级点名、按日期汇总日志、按分类输出商品

# 案例一：先排序再分组
import itertools

rows = [
    ("一班", "小张"), ("二班", "小李"), ("一班", "小王"),
]
# 直接分组（错误示范）："一班"不相邻，被拆成两段
segments = [(k, [r[1] for r in g]) for k, g in itertools.groupby(rows, key=lambda r: r[0])]
print(f"没排序直接分组（分段展示）：{segments}")
print("注意：'一班' 出现了两次，小张和小王被拆进了两个组！")

sorted_rows = sorted(rows, key=lambda r: r[0])
correct = {k: [r[1] for r in g] for k, g in itertools.groupby(sorted_rows, key=lambda r: r[0])}
print(f"先排序再分组：{correct}")

# 案例二：分组点名
# 场景：按班级输出名单
students = [
    ("一班", "小张"), ("一班", "小王"), ("二班", "小李"),
    ("二班", "小赵"), ("三班", "小周"),
]
students.sort(key=lambda s: s[0])  # 关键步骤
for cls, group in itertools.groupby(students, key=lambda s: s[0]):
    names = [s[1] for s in group]  # 组迭代器只能用一次，立即 list
    print(f"{cls}（{len(names)} 人）：{'、'.join(names)}")

# 案例三：按首字母分组单词
# 场景：字典式索引
words = ["apple", "avocado", "banana", "blueberry", "cherry"]
words.sort()
for letter, group in itertools.groupby(words, key=lambda w: w[0]):
    print(f"{letter}：{list(group)}")

# 案例四：按数据"段"分组 —— 找连续重复
# 场景：日志里"连续成功/失败"各有几段
log = ["成功", "成功", "失败", "失败", "失败", "成功"]
for result, group in itertools.groupby(log):
    length = len(list(group))
    print(f"连续 {result} x{length}")

# 案例五：与 defaultdict 分组的对比
# groupby 要先排序（O(n log n)），defaultdict 一次循环搞定（O(n)）
from collections import defaultdict
by_cls = defaultdict(list)
for cls, name in students:
    by_cls[cls].append(name)
print(f"defaultdict 分组：{dict(by_cls)}")
print("口诀：数据已排序用 groupby，乱序数据用 defaultdict")

# ===== 练习题 =====
# 1. 对 [("A",1),("B",2),("A",3)] 不排序直接 groupby，观察错误结果，再排序后正确分组。
# 2. 用 groupby 统计字符串 "aaabbcdd" 每个连续字符段的长度，输出 [('a',3),('b',2),('c',1),('d',2)]。
# 3. 写函数 compress_log(log)：用 groupby 把 ["成功","成功","失败","成功"] 摘要成 "成功2-失败1-成功1" 字符串。
