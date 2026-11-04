# i = 0
# while i <= 9:
#     print("难搞")
#     i = i + 1
# else:
#     print("完活")
# i = 1
# j = 0
# while i < 101:
#     if i % 2 == 0:
#         j += i
#     i += 1
# # print(f"加起来等于{j}")
# i = 1
# j = 1
# for j in range(1,10):
#     for i in range(1,10):
#         print(f"{i} * {j} = {i * j}",end = " " )
#         if(i == j):
#             break
#     print("\n")
# i = int(input("请输入"))
# j = 0
# for i in range(1,i +1):
#     j += 1
#     print()
#     for i in range(1,i+1):
#         print("*" , end=" ")
#         if i == j :
#             break

# i = int(input("输入"))
# for i in range(1,i+1):
#     print()
#     for i in range(1,i+1):
#         print(i, end=" ")
i = 8

for i in range(1,9):
    print()
    if i % 2 == 0:
        for i in range(1, 9):
            if i % 2 == 0:
                print("1", end=" ")
            else:
                print("0", end=" ")
    else:
        for i in range(1, 9):
            if i % 2 == 0:
                print("0", end=" ")
            else:
                print("1", end=" ")