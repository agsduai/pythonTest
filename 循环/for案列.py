# 用法1:range(end)->
# 用法2:range(start,end)->
# 用法3: range(start,end,step)
j = 0
for i in range(100,500):
    if i % 3 == 0:
        j += i
print(j)