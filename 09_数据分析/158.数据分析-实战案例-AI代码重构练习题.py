# ===== 第158课：数据分析-实战案例-AI代码重构 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 重构：不改变功能，改善结构，消除重复、提升可读性
#   - 把“数据准备、统计、绘图”拆成独立函数，每个函数只做一件事
#   - 用参数驱动绘图函数（标题、轴标签、颜色），避免复制粘贴
#   - if __name__ == "__main__" 作为入口，便于复用与测试
# 依赖：pip install pandas matplotlib

import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False

def build_movies() -> pd.DataFrame:
    """构造示例电影数据，代替真实项目中的 read_csv。"""
    return pd.DataFrame({
        "title": ["肖申克的救赎", "霸王别姬", "千与千寻", "泰坦尼克号", "盗梦空间", "流浪地球"],
        "year": [1994, 1993, 2001, 1997, 2010, 2019],
        "language": ["英语", "汉语", "日语", "英语", "英语", "汉语"],
        "rating": [9.7, 9.6, 9.4, 7.5, 6.2, 5.4],
    })

def count_by_year(df: pd.DataFrame) -> pd.Series:
    """按年份统计电影数量，并按年份排序。"""
    return df.groupby("year").size().sort_index()

def count_by_language(df: pd.DataFrame) -> pd.Series:
    """按语言统计电影数量，次数从多到少排列。"""
    return df["language"].value_counts()

def rating_distribution(df: pd.DataFrame) -> pd.Series:
    """把评分分箱后统计各分数段数量。"""
    bins = [0, 6, 7, 8, 9, 10]
    labels = ["6分以下", "6-7分", "7-8分", "8-9分", "9-10分"]
    groups = pd.cut(df["rating"], bins=bins, labels=labels, include_lowest=True)
    return groups.value_counts().sort_index()

def draw_bar(series: pd.Series, title: str, xlabel: str, ylabel: str,
             rotation: int = 0, color: str = "#4C72B0") -> None:
    """通用柱状图：传入统计结果和文字信息即可绘图。"""
    plt.figure(figsize=(8, 4.5))
    bars = plt.bar(series.index.astype(str), series.values, width=0.6, color=color)
    for bar, value in zip(bars, series.values):
        plt.text(bar.get_x() + bar.get_width() / 2,
                 bar.get_height() + 0.05, str(value), ha="center", va="bottom")
    plt.title(title, fontsize=14)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.xticks(rotation=rotation)
    plt.ylim(0, series.max() + 1)
    plt.tight_layout()

def draw_pie(series: pd.Series, title: str) -> None:
    """通用饼图：展示各部分占比。"""
    plt.figure(figsize=(7, 7))
    plt.pie(series.values, labels=series.index, autopct="%1.1f%%",
            startangle=90, wedgeprops={"edgecolor": "white"})
    plt.title(title, fontsize=14)
    plt.axis("equal")
    plt.tight_layout()

def main() -> None:
    """主流程：准备数据 → 三次统计 → 三张图。"""
    movies = build_movies()
    draw_bar(count_by_year(movies), "每年电影数量统计", "年份", "电影数量（部）", 45)
    draw_bar(count_by_language(movies), "不同语言电影数量统计", "语言", "电影数量（部）",
             color="#55A868")
    draw_pie(rating_distribution(movies), "各评分电影占比统计")
    plt.show()

if __name__ == "__main__":
    main()
# ===== 练习题 =====
# 1. 新增 draw_barh 函数，复用 draw_bar 的思路绘制横向柱状图。
# 2. 把三张图的标题、颜色整理成一个配置字典，让 main 更简洁。
# 3. 思考：重构后的代码如果新增“按类型统计”，需要改动哪些地方？
