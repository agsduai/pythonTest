# ===== 第265课：加密安全-哈希摘要 =====
# 知识点：
#   - 哈希：任意输入 → 固定长度“指纹”，不可逆
#   - md5 已可碰撞，只用于非安全场景；安全场景用 sha256
#   - 雪崩效应：输入差一个字节，摘要面目全非
#   - 用途：文件完整性校验、去重、缓存键
#   - 大文件要分块 update，不能一次性读入

import hashlib
from pathlib import Path

# 基本用法


def digest(text, algo="sha256"):
    return hashlib.new(algo, text.encode("utf-8")).hexdigest()


print("sha256:", digest("hello"))
print("md5 　:", digest("hello", "md5"))
print("摘要长度：", len(digest("a")), "个十六进制字符 =", len(digest("a")) * 4, "位")

# 雪崩效应：只差一个字母
print("hello  :", digest("hello")[:32])
print("hellp  :", digest("hellp")[:32])

# 同一内容永远同一摘要（确定性）
print("确定性：", digest("abc") == digest("abc"))


# 文件校验：分块读取
def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


p = Path("check_me.txt")
p.write_text("重要数据 v1", encoding="utf-8")
v1 = file_sha256(p)
print("文件摘要 v1：", v1[:32], "...")

p.write_text("重要数据 v2", encoding="utf-8")     # 改一个字
v2 = file_sha256(p)
print("文件摘要 v2：", v2[:32], "...")
print("内容变了摘要必然变：", v1 != v2)

p.unlink()      # 清理

# ===== 练习题 =====
# 1. 计算本项目某个 .py 文件的 sha256，再改动一个字符重算对比。
# 2. 用 md5 给“下载列表”做去重键（非安全场景，md5 够用且更快）。
# 3. 编写函数 sha256_of_many(*texts)：多个文本合并成一个摘要。
# 4. 思考：哈希“不可逆”，那网站是怎么验证你输入的密码的？（下一课）
