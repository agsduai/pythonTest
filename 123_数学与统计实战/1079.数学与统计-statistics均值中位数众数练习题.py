# ===== 第1079课：数学与统计-statistics均值中位数众数 =====
# 知识点：
#   - import statistics：mean 平均值、median 中位数、mode 众数
#   - 中位数把数据排序后取中间（偶数个取中间两个平均），抗极端值
#   - mode 返回出现最多的值；多个众数时 Python 3.8+ 返回第一个
#   - 实际场景：工资水平用中位数更真实（老板工资会拉高均值）

# 案例一：三种统计量对比
import statistics

scores = [88, 92, 75, 60, 95]
print(f"平均分：{statistics.mean(scores)}")        # 82.0
print(f"中位数：{statistics.median(scores)}")      # 88
print(f"众数：{statistics.mode([1, 2, 2, 3, 3])}")  # 2（先出现的）

# 案例二：中位数抗极端值 —— 工资统计
# 场景：5 名员工月薪，老板 10 万
salaries = [5000, 6000, 7000, 8000, 100000]
print(f"平均工资：{statistics.mean(salaries):.0f}（被老板拉高了）")
print(f"中位数工资：{statistics.median(salaries)}（更代表大多数人）")

# 案例三：偶数个数据的中位数
# 场景：4 个人的年龄
ages = [20, 22, 24, 60]
print(f"中位数：{statistics.median(ages)}")  # (22+24)/2 = 23.0

# 案例四：众数找爆款
# 场景：统计点单最多的菜品
dish_orders = ["宫保鸡丁", "鱼香肉丝", "宫保鸡丁", "麻婆豆腐", "宫保鸡丁"]
from collections import Counter
print(f"众数（点单王）：{statistics.mode(dish_orders)}")
print(f"完整票数：{Counter(dish_orders).most_common()}")  # 众数只给一个，要全部用 Counter

# 案例五：中位数 vs 均值选择口诀
data_normal = [70, 72, 74, 76, 78]      # 数据均匀
data_extreme = [70, 72, 74, 76, 700]    # 有极端值
for name, d in [("均匀数据", data_normal), ("含极端值", data_extreme)]:
    print(f"{name}：均值 {statistics.mean(d):.1f}，中位数 {statistics.median(d):.1f}")

# ===== 练习题 =====
# 1. 对 [85, 90, 78, 92, 88] 计算均值、中位数并打印，两者相差不多说明数据均匀。
# 2. 房价列表 [100, 120, 130, 150, 2000]（万），分别算均值和中位数，打印哪个更代表"普通房价"。
# 3. 写函数 summarize(nums)：一行返回 (mean, median, mode) 元组，用 [1, 2, 2, 3, 4] 测试，结果应为 (2.4, 2, 2)。
