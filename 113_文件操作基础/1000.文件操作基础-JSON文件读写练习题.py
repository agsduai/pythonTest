# ===== 第1000课：文件操作基础-JSON文件读写 =====
# 知识点：
#   - json.dumps() 把 Python 对象转为 JSON 字符串
#   - json.loads() 把 JSON 字符串转回 Python 对象
#   - json.dump() / json.load() 直接读写文件
#   - indent=2 让 JSON 格式化缩进，方便阅读
#   - ensure_ascii=False 让中文正常显示（默认转成 \uXXXX）
# 依赖：无（标准库）
import json

# 案例一：Python 对象与 JSON 字符串互转
print("== 对象转 JSON 字符串 ==")
student = {"name": "张三", "age": 20, "scores": [85, 92, 78]}
json_str = json.dumps(student, ensure_ascii=False)
print(f"  对象: {student}")
print(f"  JSON: {json_str}")

print("\n== JSON 字符串转回对象 ==")
parsed = json.loads(json_str)
print(f"  解析后: {parsed}")
print(f"  name = {parsed['name']}, 第一个分数 = {parsed['scores'][0]}")
print(f"  与原对象相等: {parsed == student}")

# 案例二：格式化输出（indent）
print("\n== indent 格式化 ==")
pretty = json.dumps(student, ensure_ascii=False, indent=2)
print(pretty)

# 案例三：写入 JSON 文件
print("\n== 写入 JSON 文件 ==")
with open("student.json", "w", encoding="utf-8") as f:
    json.dump(student, f, ensure_ascii=False, indent=2)
print("  已写入 student.json")

# 案例四：读取 JSON 文件
print("\n== 读取 JSON 文件 ==")
with open("student.json", "r", encoding="utf-8") as f:
    loaded = json.load(f)
print(f"  读取结果: {loaded}")
print(f"  name = {loaded['name']}")

# 案例五：JSON 类型对照
print("\n== Python 与 JSON 类型对照 ==")
pairs = [
    ({"k": "v"}, "对象 {}"),
    ([1, 2], "数组 []"),
    ("text", "字符串"),
    (42, "数字"),
    (True, "true"),
    (None, "null"),
]
for py_obj, desc in pairs:
    json_text = json.dumps(py_obj, ensure_ascii=False)
    print(f"  Python {py_obj!r:>12} -> JSON {json_text}")

# 案例六：保存配置并读取
print("\n== 实用：保存配置文件 ==")
config = {
    "app_name": "MyApp",
    "version": "1.0",
    "settings": {
        "theme": "dark",
        "language": "zh-CN",
        "auto_save": True
    }
}
with open("config.json", "w", encoding="utf-8") as f:
    json.dump(config, f, ensure_ascii=False, indent=2)
print("  配置已保存到 config.json")

with open("config.json", "r", encoding="utf-8") as f:
    loaded_config = json.load(f)
print(f"  应用名: {loaded_config['app_name']}")
print(f"  主题: {loaded_config['settings']['theme']}")

# ===== 练习题 =====
# 1. 把一个包含列表和字典的嵌套对象写入 JSON 文件，再读取验证。
# 2. 实现「追加配置项」：读取 config.json，添加新键，重新写入。
# 3. 把一段中文文本 {"msg": "你好世界"} 写入 JSON 并打印原始内容，
#    对比 ensure_ascii=True 和 False 的输出差异。
# 4. 思考：JSON 和 Python 字典有什么区别？（JSON 是文本格式，字典是内存对象）
