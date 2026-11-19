# ===== 第980课：字符串处理实战-查找与判断 =====
# 知识点：
#   - find() 返回第一次出现的位置，找不到返回 -1；index() 找不到直接报错
#   - in 判断是否包含，not in 判断不包含
#   - startswith() / endswith() 判断开头和结尾
#   - count() 统计出现次数
#   - 实际场景：文件名后缀判断、敏感词检测、邮箱验证

# 案例一：文件后缀判断
filename = "report.pdf"
print(f"文件: {filename}")
print(f"是 PDF 文件: {filename.endswith('.pdf')}")
print(f"是 Word 文件: {filename.endswith('.docx')}")
print(f"以 report 开头: {filename.startswith('report')}")

# 案例二：敏感词检测
message = "今天天气真好，我们去公园玩吧"
banned_words = ["暴力", "赌博"]
found = [w for w in banned_words if w in message]
print(f"\n消息: {message}")
print(f"敏感词检测结果: {found if found else '未发现'}")

# 案例三：查找位置
text = "hello world, hello python"
first = text.find("hello")
last = text.find("hello", first + 1)        # 从第一个出现位置之后继续找
not_found = text.find("goodbye")
print(f"\n文本: {text!r}")
print(f"第一个 hello 的位置: {first}")
print(f"第二个 hello 的位置: {last}")
print(f"goodbye 的位置: {not_found}（找不到返回 -1）")
print(f"hello 出现次数: {text.count('hello')}")

# 案例四：邮箱格式粗略检查
email = "user@example.com"
has_at = "@" in email
has_dot_after_at = email.find(".") > email.find("@")
print(f"\n邮箱: {email}")
print(f"包含 @: {has_at}")
print(f"@ 后面有 .: {has_dot_after_at}")
print(f"粗略判断合法: {has_at and has_dot_after_at}")

# 案例五：find 与 index 的区别
text2 = "hello"
print(f"\nfind 找不到: {text2.find('z')}（返回 -1）")
try:
    text2.index("z")
except ValueError as e:
    print(f"index 找不到: 直接报错 -> {e}")

# ===== 练习题 =====
# 1. 判断文件名 "data.csv" 是否以 ".csv" 结尾，是否以 "data" 开头。
# 2. 统计 "banana" 中字母 "a" 出现的次数。
# 3. 用 find() 找出 "hello world hello" 中所有 "hello" 的位置。
# 4. 思考：什么时候用 in 判断，什么时候用 find() 找位置？
