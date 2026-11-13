# ===== 第264课：加密安全-编码与混淆 =====
# 知识点：
#   - Base64 是“编码”不是加密：人人可解码，零安全性
#   - str ↔ bytes：编码前必须先 encode
#   - urlsafe 版本：把 +/ 换成 -_，适合放 URL
#   - 常见误用：用 base64 “藏”密码 —— 一秒还原

import base64

text = "Hello 你好"
raw = text.encode("utf-8")

# 编码与解码
encoded = base64.b64encode(raw)
print(encoded)                                   # b'SGVsbG8g5L2g5aW9...'
print(base64.b64decode(encoded).decode("utf-8"))

# URL 安全版本
print(base64.urlsafe_b64encode(b"a+b/c?").decode())

# 图片转 base64 的场景（网页内嵌小图标）
tiny_png = b"\x89PNG\r\n"                        # 演示用的假图片头
print("data:image/png;base64," + base64.b64encode(tiny_png).decode())

# 警告演示：base64 “看着像加密”，其实毫无安全性
print(base64.b64decode("MTIzNDU2"))              # b'123456' 立刻还原
print(base64.b64decode(base64.b64encode("密码123".encode())).decode())

# hex 表示：把 bytes 显示成十六进制（第265课哈希摘要就是这个格式）
print(raw.hex())
print(bytes.fromhex(raw.hex()).decode("utf-8"))

# ===== 练习题 =====
# 1. 把“用户名:密码”用 base64 编码再解码，模拟 HTTP Basic 认证流程。
# 2. 验证：对同一内容，b64encode 与 urlsafe_b64encode 何时输出不同？
# 3. 编写函数 is_base64(s)：尝试解码，成功返回 True。
# 4. 思考：编码、压缩、加密三者的本质区别是什么？
