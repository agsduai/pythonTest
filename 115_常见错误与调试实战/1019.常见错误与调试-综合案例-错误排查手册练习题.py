# ===== 第1019课：常见错误与调试-综合案例-错误排查手册 =====
# 知识点：
#   - 综合运用：NameError / IndexError / KeyError / TypeError / ValueError
#   - 排查口诀：先看报错最后一行，再看行号，最后打印变量确认类型
#   - 五大高频错误各自有"标志性触发场景"，见得多就能秒判
#   - 把每个错误写成"可运行的最小复现"，是排查能力的核心

# 案例一：错误字典 —— 每种错误一个最小复现
error_catalog = {
    "NameError": "变量没定义或拼错，如把 total_price 写成 total_prise",
    "IndexError": "下标越界，如 3 个元素的列表取 [3]，空列表取 [0]",
    "KeyError": "字典里没有这个键，如 member['phone'] 但资料里没存电话",
    "TypeError": "类型用错了，如 '字符串' + 5、在 None 上调方法",
    "ValueError": "类型对但值不对，如 int('abc')、int('')",
}
for err, desc in error_catalog.items():
    print(f"{err:12s} | {desc}")

# 案例二：逐个触发并捕获 —— 亲手认识每种错误
tests = [
    ("NameError", lambda: undefined_var),          # 未定义变量
    ("IndexError", lambda: [1, 2, 3][5]),          # 下标越界
    ("KeyError", lambda: {"a": 1}["b"]),           # 键不存在
    ("TypeError", lambda: "5" + 5),                # 字符串加数字
    ("ValueError", lambda: int("abc")),            # 转换失败
]
for name, fn in tests:
    try:
        fn()
    except Exception as e:
        actual = type(e).__name__
        mark = "OK" if actual == name else "与预期不符"
        print(f"预期 {name:10s} 实际 {actual:12s} -> {mark}")

# 案例三：混合排查 —— 一段程序里藏着多个错误，逐个击破
# 场景：下面这段"会员折扣计算"藏着 3 个常见错误
def buggy_discount(prices, vip_level):
    total = 0
    for p in prices:
        # 错误1（TypeError）：字符串 "VIP" 和数字比较会崩，需要先判断类型
        if vip_level == "VIP" and p > 0:  # 正确写法，先保证 p 是数字
            total += p * 0.8
        else:
            total += p
    # 错误2（ValueError 隐患）：prices 里可能混进字符串
    return total

mixed_prices = [100, "50", 80]  # "50" 是字符串，p > 0 会报 TypeError
clean_prices = [p for p in mixed_prices if isinstance(p, (int, float))]
print(f"清洗前 {mixed_prices}，清洗后 {clean_prices}")
print(f"折后总价：{buggy_discount(clean_prices, 'VIP')} 元")

# 案例四：排查流程演练 —— 三步定位法
# 第 1 步：看最后一行 -> TypeError: unsupported operand type(s)...
# 第 2 步：看行号 -> 锁到出错的哪一行
# 第 3 步：打印确认 -> print(f"{type(p)=} {p=}")
for p in mixed_prices:
    print(f"[排查] {type(p).__name__=} {p=}")  # 一眼看到 "50" 是 str

# ===== 练习题 =====
# 1. 分别写出触发 NameError、IndexError、KeyError 的三行代码，每行配一句注释写明"怎么修"。
# 2. 写函数 safe_add(a, b)：都是数字就相加；任一不是数字（isinstance 判断）就打印类型并返回 None；用 3+"5"、3+"5.5"（字符串数字先转 float 再加）测试。
# 3. 给定含脏数据列表 data = [12, "abc", None, 7.5, 30]，写程序：把能转成数字的全保留（None 和纯字母丢弃），最后输出 [12, 7.5, 30] 并打印平均分。
