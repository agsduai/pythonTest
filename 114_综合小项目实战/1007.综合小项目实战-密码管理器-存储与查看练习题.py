# ===== 第1007课：综合小项目实战-密码管理器——存储与查看 =====
# 知识点：
#   - 密码不能明文存储：用哈希保存密码的「指纹」而不是原文
#   - hashlib.sha256 哈希是单向的：从哈希值推不出原文
#   - 加盐（salt）：同一个密码每次哈希结果不同，防彩虹表攻击
#   - 服务端验证：比较哈希值而不是比较明文
# 依赖：无（标准库）
import hashlib
import json
import os
import random

PM_FILE = "passwords.json"


def hash_password(password, salt):
    """加盐哈希：SHA256(password + salt)。"""
    data = f"{password}{salt}".encode()
    return hashlib.sha256(data).hexdigest()


def generate_salt():
    """生成随机盐。"""
    return str(random.randint(10 ** 9, 10 ** 10 - 1))


def store_password(vault, site, password):
    """存储密码的哈希和盐。"""
    salt = generate_salt()
    hashed = hash_password(password, salt)
    vault[site] = {"salt": salt, "hash": hashed}
    return True


def verify_password(vault, site, password):
    """验证密码：哈希比对。"""
    entry = vault.get(site)
    if entry is None:
        return False
    return hash_password(password, entry["salt"]) == entry["hash"]


def load_vault():
    if not os.path.exists(PM_FILE):
        return {}
    with open(PM_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_vault(vault):
    with open(PM_FILE, "w", encoding="utf-8") as f:
        json.dump(vault, f, ensure_ascii=False, indent=2)


print("== 密码管理器 ==")
vault = load_vault()

# 存储密码
print("\n== 存储密码 ==")
store_password(vault, "github", "MyGitHubPass123")
store_password(vault, "email", "EmailPass456")
save_vault(vault)
for site, entry in vault.items():
    print(f"  {site}: hash={entry['hash'][:16]}..., salt={entry['salt']}")

print("\n  注意：存储的是哈希值和盐，不是密码原文")

# 验证密码
print("\n== 验证密码 ==")
print(f"  github + 正确密码: {verify_password(vault, 'github', 'MyGitHubPass123')}")
print(f"  github + 错误密码: {verify_password(vault, 'github', 'WrongPass')}")
print(f"  不存在的网站: {verify_password(vault, 'nosuch', 'any')}")

# 同一密码不同 salt → 不同哈希
print("\n== 加盐的意义 ==")
h1 = hash_password("samepass", "salt1")
h2 = hash_password("samepass", "salt2")
print(f"  samepass + salt1 -> {h1[:16]}...")
print(f"  samepass + salt2 -> {h2[:16]}...")
print(f"  两次哈希不同: {h1 != h2}")
print("  如果不加 salt：所有用户的 samepass 哈希值一样 → 攻击者可查彩虹表")

# 哈希的单向性
print("\n== 哈希不可逆 ==")
demo_hash = hash_password("secret123", "salt")
print(f"  哈希值: {demo_hash[:20]}...")
print("  从哈希值推不出原文 —— 只有试遍所有可能的密码才能匹配")

# ===== 练习题 =====
# 1. 实现「修改密码」：验证旧密码正确后才能设置新密码。
# 2. 实现「删除密码」：从 vault 中移除指定网站的记录。
# 3. 实现密码强度提示：新密码太短或太简单时给出警告。
# 4. 思考：为什么验证密码用「比对哈希」而不是「比对原文」？如果数据库
#    被泄露，攻击者能拿到什么、拿不到什么？
