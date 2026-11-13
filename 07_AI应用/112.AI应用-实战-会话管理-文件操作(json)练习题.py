# ===== 第112课：AI应用-实战-会话管理-文件操作(json) =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - JSON 与 Python 类型的对应：对象→dict、数组→list、字符串→str
#   - json.dump 写入文件、json.load 读取文件
#   - ensure_ascii=False 保留中文，indent=2 格式化输出
#   - json.dumps / json.loads 完成字符串与对象的互转
# 依赖：无（使用 Python 标准库 json）

import json

data = {
    "name": "张三",
    "age": 18,
    "skills": ["Python", "AI"],
    "active": True,
}

# 1. 写入 JSON 文件：ensure_ascii=False 让中文不被转义
with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# 2. 读取 JSON 文件，返回 Python 字典
with open("data.json", "r", encoding="utf-8") as f:
    loaded = json.load(f)
print("姓名：", loaded["name"])
print("技能：", loaded["skills"])

# 3. 修改后重新写回文件
loaded["age"] = 19
with open("data.json", "w", encoding="utf-8") as f:
    json.dump(loaded, f, ensure_ascii=False, indent=2)

# 4. 字符串与 Python 对象互转
text = json.dumps(data, ensure_ascii=False)
print("JSON 字符串：", text)
print("转回字典：", json.loads(text)["age"])

# ===== 练习题 =====
# 1. 定义一个包含 3 个会话的列表，用 json.dump 保存到 sessions.json。
# 2. 读取 sessions.json，打印每个会话的 title 和消息条数。
# 3. 把 indent 改为 4 和 None，对比生成文件的可读性。
