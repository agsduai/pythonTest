# ===== 第025课：核心语法-流程控制语句-if进阶(if...elif...else)-案例 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - if...elif...else 多分支语法
#   - 条件从上到下依次判断，命中一个分支后其余分支跳过
#   - else 负责处理所有条件都不成立的情况
#   - elif 可以有多个，else 最多一个且放在最后

# 案例一：根据分数输出等级
score = 85
if score >= 90:
    print("等级：优秀")
elif score >= 80:
    print("等级：良好")  # 85 满足此条件，后面的分支不再判断
elif score >= 60:
    print("等级：及格")
else:
    print("等级：不及格")

# 案例二：根据月份输出季节
month = 10
if month >= 3 and month <= 5:
    print("春季")
elif month >= 6 and month <= 8:
    print("夏季")
elif month >= 9 and month <= 11:
    print("秋季")  # 10 月命中这一分支
elif month == 12 or month == 1 or month == 2:
    print("冬季")
else:
    print("月份不合法")

# 案例三：会员折扣
vip_level = 2
if vip_level == 3:
    print("享受 7 折优惠")
elif vip_level == 2:
    print("享受 8 折优惠")
elif vip_level == 1:
    print("享受 9 折优惠")
else:
    print("暂无折扣")

# ===== 练习题 =====
# 1. 定义变量 score = 72，用 if...elif...else 输出等级：90 及以上优秀，80 及以上良好，60 及以上及格，否则不及格。
# 2. 定义变量 age = 8，用 if...elif...else 判断：小于 6 岁免票，6 到 17 岁半价，18 岁及以上全价。
# 3. 定义变量 hour = 20，用 if...elif...else 输出问候：5-11 点早上好，12-13 点中午好，14-18 点下午好，其他时间晚上好。
