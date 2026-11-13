# ===== 第138课：数据分析-环境准备(Jupyter Notebook) =====
# 课程来源：B站 BV1sHU9BmEne
# 依赖：pip install pandas jupyter
# 知识点：
#   - Jupyter Notebook 的安装与启动：pip install notebook；jupyter notebook
#   - 代码单元格（Code）与 Markdown 单元格（Markdown）
#   - 常用快捷键：Shift+Enter 运行并跳到下一格，Ctrl+Enter 运行当前格
#   - 魔法命令：%timeit、%matplotlib inline、!pip install ...
#   - Notebook 文件扩展名为 .ipynb，可与 .py 文件互相转换

# 示例：在普通 .py 文件中模拟 Notebook 的“逐格运行”
# 在 Jupyter 中，下面每个注释块可以放在一个独立的单元格里运行。

# 第 1 格：查看 Python 环境
import sys

print("Python 版本：", sys.version.split()[0])

# 第 2 格：检查数据分析常用库是否可用
libs = ["pandas", "numpy", "matplotlib"]
for lib in libs:
    try:
        module = __import__(lib)                    # 动态导入库
        version = getattr(module, "__version__", "未知")
        print(f"{lib} 已安装，版本：{version}")
    except ImportError:
        print(f"{lib} 未安装，请执行：pip install {lib}")

# 第 3 格：一个最小的数据分析片段（安装 pandas 后可运行）
try:
    import pandas as pd

    df = pd.DataFrame({"城市": ["北京", "上海", "广州"], "销量": [120, 98, 76]})
    print(df)
    print("总销量：", df["销量"].sum())
except ImportError:
    print("未安装 pandas，跳过本格示例")

# 常用 Jupyter 魔法命令（在 Notebook 单元格中执行）：
# %timeit sum(range(100000))      # 统计一行代码的耗时
# %matplotlib inline               # 让图表直接显示在 Notebook 中
# !pip install pandas openpyxl     # 在单元格中安装第三方库

# ===== 练习题 =====
# 1. 安装 Jupyter Notebook，启动后新建一个 Notebook，分别创建 Code 和 Markdown 单元格。
# 2. 在 Notebook 中运行示例的三段代码，观察每个单元格的输出。
# 3. 用 %timeit 比较列表推导式与 for 循环生成 1 万个平方数的耗时。
