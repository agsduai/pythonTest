# ===== 第365课：底层机制-字符串驻留与性能 =====
# 知识点：
#   - 字符串不可变：“修改”永远是新建对象
#   - 驻留（intern）：相同字面量共享同一对象，省内存、is 可比较
#   - 运行期拼接的字符串默认不驻留；sys.intern 可手动驻留
#   - 大量重复字符串（如百万行日志的“级别”字段）→ intern 收益明显
import sys

# 字面量驻留
a = "hello"
b = "hello"
print("字面量共享：", a is b)

# 运行期拼接：值相等但对象不同
c = "".join(["he", "llo"])
print("运行期拼接：值相等", c == a, "| 身份不同", c is not a)

# 手动 intern
print("intern 后共享：", sys.intern(c) is a)

# 不可变的直接后果：每次 += 都是新对象（第273课 O(n²) 的根源）
s = "abc"
old_id = id(s)
s += "d"
print("拼接后是新对象：", id(s) != old_id)

# 驻留的实战收益：大量重复短字符串
words = ["INFO"] * 100_000
normal = [w + "" for w in words]                    # 新对象（非驻留）
interned = [sys.intern(w) for w in words]           # 全部指向同一对象
print("普通列表内字符串各自为政；intern 后共享同一对象")

# 与第273课呼应：join 之所以快，还因为它“一次算好总长度”只分配一次

# ===== 练习题 =====
# 1. 用 tracemalloc（下一课）实测 10 万个 "INFO" 的驻留 vs 非驻留内存差。
# 2. 验证：只含字母数字下划线的运行期拼接结果有时也会被自动驻留。
# 3. 思考：intern 有代价吗？（提示：驻留表本身要维护）
