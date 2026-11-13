# ===== 第152课：数据分析-实战案例-准备工作 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 实战目标：统计电影数据的年份、语言、类型与评分分布
#   - 准备流程：导入库 → 获取数据 → 查看结构 → 清洗缺失与类型 → 确认可用字段
#   - head/info/isna/describe 是快速了解 DataFrame 的常用方法
#   - 中文绘图前置设置：字体与负号，后续所有图表文件都会复用
# 依赖：pip install pandas matplotlib

import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False

# 用字典模拟从 csv 读取到的原始数据；真实项目可改为 pd.read_csv("movies.csv")
raw_data = {
    "title": ["肖申克的救赎", "霸王别姬", "千与千寻", "泰坦尼克号",
              "盗梦空间", "无间道", "大话西游", "楚门的世界"],
    "year": ["1994", "1993", "2001", "1997", "2010", "2002", "1995", "1998"],
    "language": ["英语", "汉语", "日语", "英语", "英语", "汉语", "汉语", "英语"],
    "genres": ["剧情/犯罪", "剧情/爱情", "动画/奇幻", "剧情/爱情",
               "剧情/科幻", "剧情/犯罪", "喜剧/爱情", "剧情/科幻"],
    "rating": [9.7, 9.6, 9.4, 9.5, 9.4, 9.3, 9.2, 9.4],
}
df = pd.DataFrame(raw_data)

print(df.head())                    # 查看前 5 行，确认数据内容
print(df.info())                    # 查看列名、非空数量与数据类型
print(df.isna().sum())              # 统计每一列的缺失值数量

df["year"] = df["year"].astype(int)                         # 年份转整数
df["rating"] = pd.to_numeric(df["rating"], errors="coerce")  # 评分转数值，异常值变 NaN
df = df.dropna(subset=["year", "language", "genres", "rating"])  # 删除关键字段缺失的行
df = df.drop_duplicates(subset=["title"])                   # 按片名去重

print("清洗后数据量：", len(df))
print(df.describe())                # 数值列统计摘要：均值、最值等

# ===== 练习题 =====
# 1. 给原始数据再添加一条电影记录，重新运行并观察 describe 的变化。
# 2. 增加一个“时长（分钟）”字段，并用 info 查看它的类型。
# 3. 思考：为什么统计前要先转换 year 和 rating 的类型，而不是直接分组？
