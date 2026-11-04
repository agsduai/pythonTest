# yuer = int(input("请输入年份"))
#
# if yuer % 100 == 0 and yuer % 4 == 0:
#     print("当前年份是闰年")
# elif yuer % 100 != 0 and yuer % 4 == 0:
#     print("当前年份是闰年")
# else:
#     print("当前年份不是闰年")

yonghu = input("请输入账户")
mami = input("请输入密码")

if (yonghu == "admin" and mami == "1") or (yonghu == "root" and mami == "2") or (yonghu == "zhang" and mami == "3"):
    print(f"{yonghu}登录成功")
else:
    print("404")