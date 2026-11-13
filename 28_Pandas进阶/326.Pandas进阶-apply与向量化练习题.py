# ===== 第326课：Pandas进阶-apply与向量化 =====
# 知识点：
#   - 优先级：列运算（向量化）> 单列 apply > 跨列 apply(axis=1)
#   - df[列].apply(func)：逐元素调用函数，灵活但慢
#   - df.apply(func, axis=1)：整行作为一个 Series 传入，可跨列计算
#   - 与第321课呼应：apply 底层是 Python 循环，能量化就别 apply
# 依赖：pip install pandas

import timeit

import numpy as np
import pandas as pd

df = pd.DataFrame({
    "姓名": ["小明", "小红", "小刚", "小丽", "小强"],
    "语文": [92, 85, 76, 88, 65],
    "数学": [88, 95, 70, 82, 60],
})

# ---- 一级：列向量化（最快）----
df["总分"] = df["语文"] + df["数学"]

# ---- 二级：单列 apply（有分支逻辑时）----
def grade(score):
    if score >= 180:
        return "优秀"
    if score >= 160:
        return "良好"
    return "继续努力"


df["等级"] = df["总分"].apply(grade)

# ---- 三级：跨列 apply（axis=1 整行传入）----
df["评语"] = df.apply(lambda row: f"{row['姓名']}：总分{row['总分']}，{row['等级']}", axis=1)
print(df[["姓名", "总分", "等级", "评语"]], end="\n\n")

# ---- 性能对比：np.where 向量化 vs apply ----
t_apply = timeit.timeit(lambda: df["总分"].apply(lambda x: "优" if x >= 180 else "良"), number=200)
t_vec = timeit.timeit(
    lambda: pd.Series(np.where(df["总分"] >= 180, "优", "良"), index=df.index),
    number=200,
)
print(f"apply：{t_apply:.3f}s | where 向量化：{t_vec:.3f}s")

# ===== 练习题 =====
# 1. 用向量化写法重写 grade（两个 np.where 嵌套或 np.select）。
# 2. 加一列“薄弱科目”：apply(axis=1) 找出每人分数最低的科目名。
# 3. 思考：什么样的函数适合 apply？什么信号说明该改向量化？
