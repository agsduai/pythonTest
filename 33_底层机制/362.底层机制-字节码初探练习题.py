# ===== 第362课：底层机制-字节码初探 =====
# 知识点：
#   - Python 先编译成字节码，再由虚拟机逐条执行
#   - dis 模块：把函数“反汇编”，看清每一步
#   - LOAD_FAST（局部变量）快于 LOAD_GLOBAL（全局查找）—— 第273课的底层解释
#   - 常量折叠：2 ** 10 在编译期就变成了 1024
import dis

GLOBAL_X = 10


def use_local():
    x = 1
    return x + 1


def use_global():
    return GLOBAL_X + 1


print("=== use_local（局部变量）===")
dis.dis(use_local)
print("=== use_global（全局变量，多一次字典查找）===")
dis.dis(use_global)


# ---- 常量折叠：编译期直接算好 ----
def folded():
    return 2 ** 10


print("=== folded（常量折叠）===")
dis.dis(folded)
print("结果：", folded())

# ---- 短函数会被优化器内联吗？字节码说了算 ----
def add(a, b):
    return a + b


print("=== add ===")
dis.dis(add)

# 读懂字节码的三步：LOAD（取值）→ 计算 → STORE/RETURN（存/返回）
# 不用背指令集 —— 会用 dis 验证“哪个写法更快”就够了

# ===== 练习题 =====
# 1. 用 dis 对比 "s += x 循环" 与 ''.join 的字节码条数。
# 2. 验证 3 + 4 会被折叠，而 x = 3; y = 4 不会。
# 3. 思考：为什么第271课 cProfile 是函数级、而 dis 能到语句级？
