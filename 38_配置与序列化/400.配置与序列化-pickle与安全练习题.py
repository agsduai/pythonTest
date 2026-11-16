# ===== 第400课：配置与序列化-pickle与安全 =====
# 知识点：
#   - pickle：Python 对象 → 字节流，能保留类型（tuple/date/自定义类）
#   - json 只能存基础类型：元组变列表、日期存不了
#   - pickle 适合：本机缓存、模型文件、进程间传递；不适合跨语言交换
#   - ⚠ 安全红线：绝不 unpickle 不可信来源的数据 —— 反序列化会执行代码
#   - 只想存数据就用 JSON；必须用 pickle 时确保来源可信 + 校验哈希
import datetime
import json
import pickle
import pickletools

data = {
    "name": "小明",
    "created": datetime.date(2026, 11, 13),
    "tags": ("python", "course"),
}

# ---- pickle 往返：类型完整保留 ----
blob = pickle.dumps(data)
restored = pickle.loads(blob)
print("pickle 还原：", restored)
print("日期类型保留：", type(restored["created"]).__name__)
print("元组类型保留：", type(restored["tags"]).__name__)

# ---- JSON 对照：类型丢失 / 直接报错 ----
print("\nJSON 对照：")
try:
    json.dumps(data)
except TypeError as exc:
    print("  日期无法直接序列化：", exc)
json_ready = {**data, "created": data["created"].isoformat(), "tags": list(data["tags"])}
print("  手动转换后：", json.dumps(json_ready, ensure_ascii=False))

# ---- 体积对比（pickle 通常更紧凑，但不绝对）----
json_bytes = json.dumps(json_ready, ensure_ascii=False).encode("utf-8")
print(f"\n体积：pickle {len(blob)} 字节 | JSON {len(json_bytes)} 字节")

# ---- 查看字节码指令（理解 pickletools 可用于审计）----
print("\n.pkl 头部字节：", blob[:8])
print("前 6 条指令：")
for i, (opcode, arg, pos) in enumerate(pickletools.genops(blob)):
    if i >= 6:
        break
    print(f"  {opcode.name} {arg!r}")

# ---- 安全演示：反序列化会“执行对象自己声明的行为” ----
print("\n== 安全演示（良性示例）==")


class Demo:
    def __reduce__(self):
        # 真实攻击会用 os.system / subprocess 执行命令
        return (print, ("⚠ 反序列化时执行了对象附带的代码！",))


payload = pickle.dumps(Demo())
print("即将反序列化一个“会打印”的对象：")
pickle.loads(payload)          # 这里执行了 print —— 这就是风险所在

print("\n结论：")
print("  - 自己写、自己读的缓存文件：可以 pickle")
print("  - 网络传输、用户上传、第三方来源：只用 JSON 等纯数据格式")
print("  - 必须接收 pickle 时：验签（第267课）+ 隔离环境")

# ===== 练习题 =====
# 1. 用 pickle 保存一个自定义类的实例，load 后验证类型与属性。
# 2. 对比 pickle 的 5 个协议版本（protocol=0/2/5）体积差异。
# 3. 写一个 safe_load(path) 函数：文件哈希不在白名单时拒绝加载。
# 4. 思考：为什么说“pickle 是 Python 专属”，跨语言项目该用什么？
