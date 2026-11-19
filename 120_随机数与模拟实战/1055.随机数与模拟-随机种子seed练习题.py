# ===== 第1055课：随机数与模拟-随机种子seed =====
# 知识点：
#   - random.seed(n)：固定随机起点，之后每次运行结果完全一样
#   - 用途：调试（结果可复现）、测试（断言固定值）、实验对比
#   - 不设种子时系统用时间做种子，每次都不同
#   - 同一个种子生成同一串数；换种子就换一串

# 案例一：固定种子 —— 两次运行结果一模一样
import random

random.seed(42)
a = [random.randint(1, 100) for _ in range(5)]
print(f"种子 42 第一轮：{a}")

random.seed(42)  # 重置到同一起点
b = [random.randint(1, 100) for _ in range(5)]
print(f"种子 42 第二轮：{b}")
print(f"两轮相同：{a == b}")

# 案例二：不同种子结果不同
random.seed(1)
x = random.randint(1, 100)
random.seed(2)
y = random.randint(1, 100)
print(f"种子 1 -> {x}，种子 2 -> {y}（多半不同）")

# 案例三：调试场景 —— 让"随机 bug"可复现
# 场景：抽查库存时发现 bug，用种子固定住输入来排查
def random_inspect(inventory, seed):
    random.seed(seed)
    return random.sample(inventory, 2)

stock = ["A", "B", "C", "D", "E"]
print(f"种子 7 抽查：{random_inspect(stock, 7)}")   # 每次运行都一样
print(f"种子 7 复现：{random_inspect(stock, 7)}")   # 和上一行相同，可稳定调试

# 案例四：种子只影响之后的序列
random.seed(99)
first = random.random()
second = random.random()
print(f"种子 99 的第一个数：{first:.4f}")
print(f"种子 99 的第二个数：{second:.4f}（同种子下也是固定的一串）")

# ===== 练习题 =====
# 1. 用 seed(2024) 生成 3 个 randint(1,10) 并记录；再重置 seed(2024) 生成一次，验证三次完全一致。
# 2. 写函数 stable_sample(lst, k, seed)：固定种子后 sample，保证同名多次调用结果一致；用 1~10 抽 3 个测试两次。
# 3. 对比实验：seed(1) 与 seed(100) 各生成 1000 次 randint(1,6)，分别算平均值并打印（说明"种子只管可复现，不改变随机性"）。
