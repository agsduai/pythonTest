# ===== 第273课：性能优化-字符串与循环优化 =====
# 知识点：
#   - 循环里 s += x 是 O(n²)：每次都新建字符串；join 一次成型 O(n)
#   - 列表推导式比等价 for+append 快（专用字节码，少一次方法查找）
#   - 局部变量访问快于全局变量（字节码层面 LOAD_FAST vs LOAD_GLOBAL）
#   - 微优化放最后：先换算法（第274课），再抠这些细节

import timeit

# ---- 字符串拼接：+= vs join ----
t_plus = timeit.timeit(
    "s = ''\nfor i in range(1000):\n    s += str(i)",
    number=200,
)
t_join = timeit.timeit(
    "s = ''.join(str(i) for i in range(1000))",
    number=200,
)
print(f"+= 拼接：{t_plus:.4f}s | join：{t_join:.4f}s")

# ---- 列表推导 vs for+append ----
t_loop = timeit.timeit(
    "out = []\nfor i in range(1000):\n    out.append(i * 2)",
    number=1000,
)
t_comp = timeit.timeit(
    "out = [i * 2 for i in range(1000)]",
    number=1000,
)
print(f"for+append：{t_loop:.4f}s | 推导式：{t_comp:.4f}s")

# ---- 局部变量 vs 全局变量 ----
GLOBAL_LIST = list(range(1000))


def use_global():
    total = 0
    for x in GLOBAL_LIST:          # 每次循环都要查全局名
        total += x
    return total


def use_local():
    local_list = GLOBAL_LIST       # 先绑定成局部
    total = 0
    for x in local_list:
        total += x
    return total


t_g = timeit.timeit(use_global, number=2000)
t_l = timeit.timeit(use_local, number=2000)
print(f"全局引用：{t_g:.4f}s | 局部绑定：{t_l:.4f}s")

# ---- 提醒：可读性优先 ----
# 这些优化的收益通常在“百万次循环”才明显；
# 业务代码里一行 join 换 += 顺手就做，为省 1ms 牺牲可读性则不值得。

# ===== 练习题 =====
# 1. 把 += 的规模改成 10000，验证 O(n²) 增长趋势。
# 2. 对比 sum(range(1000)) 与手写循环累加，感受内置函数的 C 实现优势。
# 3. 用第271课 cProfile 验证本评件哪个优化点最有收益。
# 4. 思考：为什么 f-string 通常比 % 和 format 快？
