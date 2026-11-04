# coswes = int(input("请输入考试成绩"))
#
# if coswes >= 85:
#     print("优秀")
# elif 60 < coswes < 85:
#     print("及格")
# else:
#     print("不及格")

# money = float(input("当前金额"))
# if money > 500:
#     print("应付金额",money * 0.8)
# elif 500 > money >= 300:
#     print("应付金额", money * 0.9)
# elif 300 > money >= 100:
#     print("应付金额", money * 0.95)
# else:
#     print("应付金额", money)
a1 = int(input("1"))
a2 = int(input("2"))
a3 = int(input("3"))
b = a1 + a2 > a3
if b and (a1 == a2 ==a3):
    print("等边三角形")
elif b and ((a1 == a2) or (a1 == a3) or (a2 == a3)):
    print("2")
elif b and ((a1 != a2) or (a1 != a3) or (a2 != a3)):
    print("3")
else:
    print("4")