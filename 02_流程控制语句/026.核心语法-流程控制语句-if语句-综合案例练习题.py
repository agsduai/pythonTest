# ===== 第026课：核心语法-流程控制语句-if语句-综合案例 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 比较运算符、逻辑运算符与 if 的综合运用
#   - if...elif...else 的分支顺序很重要
#   - if 的嵌套：在一个分支里再写 if
#   - 复杂条件可以用小括号提高可读性

# 案例一：快递运费计算
amount = 120
province = "广东"
if amount >= 99:
    print("已满 99 元，包邮")  # 先判断满额，避免后续分支误判
elif province == "新疆" or province == "西藏":
    print("偏远地区，运费 15 元")
elif amount >= 50:
    print("运费 8 元")
else:
    print("运费 12 元")

# 案例二：判断闰年
year = 2024
if (year % 4 == 0 and year % 100 != 0) or year % 400 == 0:
    print(f"{year} 年是闰年")
else:
    print(f"{year} 年不是闰年")

# 案例三：景区购票（if 嵌套）
age = 65
height = 1.4
if age < 6:
    print("免票")
elif age >= 60:
    print("老年票：半价")
else:
    if height < 1.2:
        print("身高不足 1.2 米：免票")
    else:
        print("成人票：全价")

# 案例四：判断三角形是否成立
a = 3
b = 4
c = 5
if a + b > c and a + c > b and b + c > a:
    print("三条边可以组成三角形")
else:
    print("三条边不能组成三角形")

# ===== 练习题 =====
# 1. 定义变量 weight = 3.5，用 if...elif...else 计算运费：2 公斤内 10 元；2 到 5 公斤，超出部分每公斤加 5 元；超过 5 公斤统一 30 元。
# 2. 定义变量 score = 95 和 is_leader = False，判断：分数大于 90 且是班干部，输出“评选优秀干部”；分数大于 90，输出“评选三好学生”；否则输出“继续努力”。
# 3. 定义变量 num = -8，判断它是正数、负数还是零，并进一步判断正数是否为偶数、负数绝对值是否大于 5。
