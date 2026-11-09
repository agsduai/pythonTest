# 嵌套循环案例:打印99乘法表
for i in range(1, 20):  #外层循环-控制行
    for j in range(1, i + 1):  #内层循环- 控制列
        print(f"{j} x {i} = {j * i}", end="\t")
    print()
  