# ===== 第1073课：容器工具collections-OrderedDict与dict顺序 =====
# 知识点：
#   - Python 3.7+ 普通 dict 就是有序的（按插入顺序），OrderedDict 的独门优势变少
#   - OrderedDict.move_to_end()：把某键移到头/尾，普通 dict 做不到
#   - pop(last=False)：从头部弹出键值对（LRU 缓存的基础操作）
#   - OrderedDict 相等判断与顺序有关：顺序不同即不相等

# 案例一：基本用法 —— 保持插入顺序
from collections import OrderedDict

od = OrderedDict()
od["香蕉"] = 5.5
od["苹果"] = 8.0
od["牛奶"] = 12.0
print(f"OrderedDict：{dict(od)}")  # 按插入顺序

d = {"香蕉": 5.5, "苹果": 8.0, "牛奶": 12.0}
print(f"普通 dict：{d}")  # 3.7+ 也按插入顺序

# 案例二：move_to_end —— 置顶 / 沉底
# 场景：音乐播放列表，"单曲循环的挪到最前"
od2 = OrderedDict([("歌曲A", 1), ("歌曲B", 2), ("歌曲C", 3)])
od2.move_to_end("歌曲B", last=False)  # last=False 移到最前
print(f"置顶后：{list(od2)}")
od2.move_to_end("歌曲A")  # 默认移到最后
print(f"沉底后：{list(od2)}")

# 案例三：pop 弹出头尾 —— 简易 FIFO 容量控制
# 场景：缓存最多存 3 个键，满了先淘汰最早的
cache = OrderedDict()
def cache_put(key, value):
    cache[key] = value
    if len(cache) > 3:
        oldest = cache.popitem(last=False)  # 弹出最早写入的
        print(f"  淘汰最早的键：{oldest[0]}")

for k, v in [("a", 1), ("b", 2), ("c", 3), ("d", 4)]:
    cache_put(k, v)
print(f"缓存现状：{list(cache)}")

# 案例四：顺序敏感的相等判断
od_a = OrderedDict([("a", 1), ("b", 2)])
od_b = OrderedDict([("b", 2), ("a", 1)])
print(f"内容相同顺序不同：{od_a == od_b}")  # False
print(f"普通 dict 比较：{dict(od_a) == dict(od_b)}")  # True，不看顺序

# 案例五：什么时候还需要 OrderedDict
# 1) 需要 move_to_end / popitem(last=False)
# 2) 需要顺序敏感的相等判断（如配置对比）
print("总结：日常用 dict；要'移动键位置'或'顺序参与比较'才用 OrderedDict")

# ===== 练习题 =====
# 1. 用 OrderedDict 存 4 首歌并把最后一首 move_to_end(last=False) 置顶，打印列表。
# 2. 写简易 LRU：容量 2 的 OrderedDict 缓存，依次写入 a、b、c，打印淘汰过程与最终缓存。
# 3. 对比两份配置 OrderedDict({"debug":True,"port":80}) 与 OrderedDict({"port":80,"debug":True})，分别用 OrderedDict 和转 dict 后比较，打印两次结果并解释差异。
