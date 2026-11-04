# yrt: int = int(input("请输入年份"))
# if yrt % 100 == 0:
#     if yrt % 400 == 0:
#         print(f"{yrt}是闰年")
#     else:
#         print(f"{yrt}不是闰年")
# else:
#     if yrt % 4 == 0:
#         print(f"{yrt}是闰年")
#     else:
#         print(f"{yrt}不是闰年")
dian: int = int(input("请输入当前用电度数"))
fei  = 0
if dian < 2880 :
    fei  = dian * 0.4883
    print(f"当前电费为{fei}")
elif 2880 < dian <4800 :
    fei = 2880 * 0.4883 + (dian - 2880) * 0.5383
    print(f"当前电费为{fei}")
else :
    fei = 2880 * 0.4883 + (4800 - 2880) * 0.5383 + (dian - 4800) * 0.7883
    print(f"当前电费为{fei}")