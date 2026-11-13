# ===== 第325课：Pandas进阶-缺失值处理进阶 =====
# 知识点：
#   - 定位：isna().sum() 每列缺失数；df[df.isna().any(axis=1)] 找出含缺失的行
#   - 删除：dropna(subset=关键列) —— 关键字段缺了才删
#   - 填充：fillna(均值/中位数)、ffill 前向填充、interpolate 线性插值
#   - 原则：先想业务含义（该删？该填 0？该插值？），再动手
# 依赖：pip install pandas numpy

import numpy as np
import pandas as pd

df = pd.DataFrame({
    "日期": ["11-01", "11-02", "11-03", "11-04", "11-05"],
    "销量": [120, np.nan, 150, np.nan, 190],
    "温度": [22, 21, np.nan, np.nan, 20],
})
print(df, end="\n\n")

# ---- 定位缺失 ----
print("每列缺失数：", df.isna().sum().to_dict())
print("含缺失的行：", df[df.isna().any(axis=1)].index.tolist())

# ---- 删除：关键列（日期）缺失才删，辅助列缺失保留 ----
print("dropna(subset=['日期'])：", df.dropna(subset=["日期"]).shape[0], "行", sep="")

# ---- 填充策略对比 ----
print("均值填充：", df["销量"].fillna(df["销量"].mean().round(1)).tolist())
print("前向填充：", df["销量"].ffill().tolist())
print("线性插值：", df["销量"].interpolate().round(1).tolist())

# ---- 组合拳：不同列不同策略 ----
clean = df.assign(
    销量=df["销量"].interpolate().round(1),
    温度=df["温度"].ffill(),
)
print("处理后：", clean.to_dict("records"), sep="\n")

# 说明：pandas 3.x 默认“写时复制”，assign 返回新表，原 df 不变 —— 链式处理更安全

# ===== 练习题 =====
# 1. 统计缺失比例：df.isna().mean()，超过 50% 的列直接整列丢弃。
# 2. 思考：销量数据该用均值还是插值？什么情况下该填 0？
# 3. 进阶：把缺失行单独导出成“待人工核对.csv”（结合第284课）。
