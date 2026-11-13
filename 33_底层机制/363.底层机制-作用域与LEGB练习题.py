# ===== 第363课：底层机制-作用域与LEGB =====
# 知识点：
#   - LEGB 查找顺序：Local → Enclosing → Global → Built-in
#   - nonlocal：改外层函数变量（第186课闭包的钥匙）
#   - global：改模块级变量（能用但尽量少用）
#   - 经典坑：函数里“先读后赋”同名变量 → UnboundLocalError
counter = 0                     # Global


def outer():
    n = 10                      # Enclosing（相对 inner 而言）

    def inner():
        nonlocal n              # 声明：我要改的是外层的 n
        n += 1
        return n

    return inner


f = outer()
print("闭包计数：", f(), f(), f())       # 11 12 13 —— n 被闭包记住（第186课）


def bump_global():
    global counter
    counter += 1


bump_global()
bump_global()
print("global 计数：", counter)

# ---- LEGB 遮蔽演示 ----
x = "全局"


def shadow():
    x = "局部"                  # Local 遮蔽 Global
    return x


print(shadow(), "|", x)          # 局部 全局 —— 全局没被动过

# ---- 经典坑：局部赋值让整个函数把 x 当局部变量 ----
x2 = 0


def broken():
    try:
        print(x2)               # Python 看到“函数内某处有 x2 = 1”
        x2 = 1                  # 于是这里按“未赋值的局部变量”处理 → 报错
    except UnboundLocalError as exc:
        print("UnboundLocalError：", exc)


broken()

# builtins 层：len/range 不用导入就能用 —— 因为它们在最外一层
print("builtins 层：", len("abc"))

# ===== 练习题 =====
# 1. 写三层嵌套函数，在最内层用 nonlocal 修改最外层的变量。
# 2. 故意制造 global 与 local 同名遮蔽，打印两处的 id。
# 3. 思考：为什么 Python 选择“赋值即局部”，而不是“按运行时动态判断”？
