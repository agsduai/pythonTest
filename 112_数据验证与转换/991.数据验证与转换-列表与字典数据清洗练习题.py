# ===== 第991课：数据验证与转换-列表与字典数据清洗 =====
# 知识点：
#   - 列表去重：set() 快速去重但丢失顺序，循环保序去重
#   - 列表过滤：列表推导式 + 条件
#   - 字典清洗：删除 None/空值字段
#   - 嵌套数据清洗：字典列表中提取和过滤
#   - 实际场景：清洗爬虫抓到的脏数据、合并重复项

# 案例一：列表去重（两种方式）
print("== 列表去重 ==")
items = [1, 2, 2, 3, 3, 3, 4, 1]
# 方式 1: set 去重（丢失顺序）
unique_set = list(set(items))
print(f"  set 去重（顺序可能变）: {unique_set}")
# 方式 2: 循环保序去重
unique_ordered = []
for item in items:
    if item not in unique_ordered:
        unique_ordered.append(item)
print(f"  循环保序去重: {unique_ordered}")
# 方式 3: dict.fromkeys 保序去重
unique_fromkeys = list(dict.fromkeys(items))
print(f"  fromkeys 保序去重: {unique_fromkeys}")

# 案例二：列表过滤——去掉空值和无效项
print("\n== 过滤空值和无效项 ==")
raw_list = ["apple", "", None, "banana", "  ", "cherry", None]
# 过滤 None 和空字符串
valid = [item for item in raw_list if item]
print(f"  过滤 None/空字符串: {valid}")
# 过滤空字符串（保留 None 标记）
valid2 = [item for item in raw_list if item is not None and item.strip()]
print(f"  过滤空字符串（保留 None 检查）: {valid2}")
# 去掉首尾空格
valid3 = [item.strip() for item in raw_list if isinstance(item, str) and item.strip()]
print(f"  清理空格后: {valid3}")

# 案例三：字典清洗——删除空值字段
print("\n== 字典清洗 ==")
dirty_dict = {"name": "张三", "age": None, "email": "", "phone": "13812345678", "address": None}
clean_dict = {k: v for k, v in dirty_dict.items() if v is not None and v != ""}
print(f"  清洗前: {dirty_dict}")
print(f"  清洗后: {clean_dict}")

# 案例四：字典列表——提取和过滤
print("\n== 字典列表过滤 ==")
students = [
    {"name": "张三", "score": 85, "class": "A"},
    {"name": "李四", "score": 45, "class": "B"},
    {"name": "王五", "score": 92, "class": "A"},
    {"name": "赵六", "score": 60, "class": "B"},
]
# 提取所有及格的学生
passing = [s for s in students if s["score"] >= 60]
print(f"  及格学生: {[s['name'] for s in passing]}")
# 提取 A 班学生姓名
a_class_names = [s["name"] for s in students if s["class"] == "A"]
print(f"  A 班学生: {a_class_names}")
# 按分数排序（从高到低）
sorted_students = sorted(students, key=lambda s: s["score"], reverse=True)
print(f"  按分数排序: {[(s['name'], s['score']) for s in sorted_students]}")

# 案例五：合并重复数据
print("\n== 合并重复项 ==")
raw_records = [
    {"name": "张三", "score": 85},
    {"name": "李四", "score": 45},
    {"name": "张三", "score": 92},          # 张三出现两次，取最高分
]
merged = {}
for record in raw_records:
    name = record["name"]
    score = record["score"]
    if name not in merged or score > merged[name]:
        merged[name] = score
print(f"  合并后（取最高分）: {merged}")

# ===== 练习题 =====
# 1. 把 ["a", "b", "a", "c", "b"] 去重并保持原始顺序。
# 2. 从学生列表中筛选出 A 班且分数 ≥ 80 的学生姓名。
# 3. 清洗字典 {"name": "  张三  ", "age": None, "email": "  "}：去空格并删空值。
# 4. 思考：set 去重和 fromkeys 去重的区别是什么？什么时候用哪个？
