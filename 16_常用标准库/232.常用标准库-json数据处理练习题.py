# ===== 第232课：常用标准库-json数据处理 =====
# 知识点：
#   - dumps/loads：对象 ↔ JSON 字符串；dump/load：对象 ↔ 文件
#   - ensure_ascii=False 保留中文；indent 缩进美化
#   - 类型对应：dict↔对象 list↔数组 None↔null True↔true 元组→数组
#   - JSONDecodeError：解析非法 JSON 时的异常

import json
import os

user = {"name": "小明", "age": 15, "tags": ["python", "初学"], "vip": None}

# 序列化：Python 对象 → JSON 字符串
s = json.dumps(user, ensure_ascii=False, indent=2)
print(s)

# 反序列化：JSON 字符串 → Python 对象
data = json.loads(s)
print(data["tags"], type(data["vip"]).__name__)

# 文件读写（第112课的会话保存就是这么做的）
with open("user_232.json", "w", encoding="utf-8") as f:
    json.dump(user, f, ensure_ascii=False, indent=2)
with open("user_232.json", encoding="utf-8") as f:
    loaded = json.load(f)
print(loaded["name"])

# 类型对应验证
print(json.dumps({"a": (1, 2)}))                    # 元组 → 数组
print(json.loads('{"ok": true, "n": null, "pi": 3.14}'))

# 容错：解析用户输入 / 外部接口返回时不要裸奔
for text in ('{"ok": 1}', "{非法JSON}"):
    try:
        print(json.loads(text))
    except json.JSONDecodeError as exc:
        print("解析失败：", exc)

os.remove("user_232.json")     # 清理演示文件

# ===== 练习题 =====
# 1. 把一个嵌套列表[班级->学生列表]存成 JSON 再读回来，验证类型不变。
# 2. 编写函数 load_config(path, default)：文件不存在或解析失败都返回 default。
# 3. 用 indent=4 和 sort_keys=True 输出对比格式差异。
# 4. 思考：JSON 不支持元组和 datetime，遇到它们怎么存？
