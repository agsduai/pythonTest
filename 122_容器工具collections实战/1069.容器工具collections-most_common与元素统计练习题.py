# ===== 第1069课：容器工具collections-most_common与元素统计 =====
# 知识点：
#   - most_common(n)：返回出现次数前 n 名的 [(元素, 次数), ...] 列表
#   - most_common() 不带参数：全部按次数从高到低排
#   - elements()：按次数展开还原所有元素
#   - 实际场景：销量排行榜、热搜榜、找众数

# 案例一：销量排行榜
from collections import Counter

sales = ["苹果", "牛奶", "苹果", "面包", "苹果", "牛奶", "鸡蛋"]
c = Counter(sales)
print(f"前 2 名：{c.most_common(2)}")   # [(元素, 次数), ...]
print(f"完整榜单：{c.most_common()}")

# 案例二：找众数（出现最多的值）
# 场景：班级投票选出班长
votes = ["小张", "小李", "小张", "小王", "小张"]
top = Counter(votes).most_common(1)[0]
print(f"班长：{top[0]}（{top[1]} 票）")

# 案例三：并列第一的处理
# 场景：两人票数相同都要展示
all_ranked = Counter(votes).most_common()
max_count = all_ranked[0][1]
champions = [name for name, cnt in all_ranked if cnt == max_count]
print(f"并列最高票：{champions}")

# 案例四：elements 还原展开
c = Counter({"苹果": 3, "牛奶": 1})
print(f"展开：{list(c.elements())}")  # ['苹果','苹果','苹果','牛奶']

# 案例五：字符频率 Top3
# 场景：文章字数分析
text = "python is powerful and python is easy to learn"
char_counter = Counter(text.replace(" ", ""))
print(f"字符 Top3：{char_counter.most_common(3)}")

# ===== 练习题 =====
# 1. 统计 "mississippi" 中每个字母次数，打印 Top2 与完整榜单。
# 2. 商品销售列表 20 条（自造），用 most_common 找出卖得最多的商品并输出"销量冠军：xxx（n 件）"。
# 3. 列表 [1,2,2,3,3,4,4,4,5]：用 Counter 判断"众数是 4"，并打印所有与最高频次数并列的元素。
