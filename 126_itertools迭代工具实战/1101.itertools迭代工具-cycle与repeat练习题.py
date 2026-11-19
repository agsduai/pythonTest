# ===== 第1101课：itertools迭代工具-cycle与repeat =====
# 知识点：
#   - cycle(序列)：无限循环重复，取不完；同样必须 islice/break 限量
#   - repeat(值, n)：重复同一个值 n 次，不写 n 就是无限
#   - cycle 实际场景：轮流值班、轮播广告词、红绿灯模拟
#   - repeat 实际场景：发同样的通知给 n 个人、初始化固定值

# 案例一：cycle 轮流值班
import itertools

duty = itertools.cycle(["张三", "李四", "王五"])
for week in range(1, 7):
    print(f"第 {week} 周值班：{next(duty)}")
# 三个人轮流，循环往复

# 案例二：cycle + zip 给列表配对
# 场景：给任意多个学生轮流分配教室
students = ["学生1", "学生2", "学生3", "学生4", "学生5", "学生6", "学生7"]
rooms = ["A教室", "B教室", "C教室"]
arrange = dict(zip(students, itertools.cycle(rooms)))
print(f"教室分配：{arrange}")

# 案例三：islice 限量取 cycle
# 场景：红绿灯模拟，看前 8 个灯
lights = list(itertools.islice(itertools.cycle(["红", "绿", "黄"]), 8))
print(f"灯序：{lights}")

# 案例四：repeat 重复值
# 场景：给 3 位用户发同一条公告
notice = "系统将于今晚 22:00 维护"
for user, msg in zip(["小张", "小李", "小王"], itertools.repeat(notice, 3)):
    print(f"发给 {user}：{msg}")

# 案例五：repeat 配 map —— 平方表速写
# map(pow, 列表, repeat(2)) 等价于每项平方
squares = list(map(pow, [1, 2, 3, 4, 5], itertools.repeat(2)))
print(f"平方：{squares}")  # [1, 4, 9, 16, 25]

# ===== 练习题 =====
# 1. 用 cycle 模拟"石头剪刀布"机器人出拳：取 10 次输出其出拳序列。
# 2. 用 islice + cycle 打印 1~12 月的"值班人表"（3 人轮班），输出 12 行"X月：某人"。
# 3. 用 repeat + map 计算 [2, 5, 7] 的立方（repeat(3)），输出 [8, 125, 343]。
