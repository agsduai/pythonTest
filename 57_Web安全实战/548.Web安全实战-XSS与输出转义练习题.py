# ===== 第548课：Web安全实战-XSS与输出转义 =====
# 知识点：
#   - XSS：把用户输入当 HTML/JS 执行（存储型、反射型、DOM 型）
#   - 防御核心：按“输出上下文”转义，而不是过滤输入
#   - HTML 文本：& < > " ' 转义
#   - HTML 属性：还要处理引号；属性值必须加引号
#   - URL/JS 上下文：使用专门编码，不要拼字符串
#   - CSP（内容安全策略）：限制可执行的脚本来源（第二道防线）
#   - 与第548课前后的输入校验配合：校验是“拒绝坏数据”，转义是“安全展示”
# 依赖：无（html 标准库）


def escape_html(text: str) -> str:
    """文本节点转义。"""
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&#x27;"))


def escape_attr(text: str) -> str:
    """属性值转义（属性必须用引号包起来）。"""
    return escape_html(text).replace("`", "&#x60;")


# ---------------- 演示：恶意输入 ----------------
attacks = [
    '<script>alert("xss")</script>',
    '<img src=x onerror=alert(1)>',
    '" onmouseover="alert(1)',
    "javascript:alert(1)",
    "正常文本 & 符号",
]

print("== 文本节点 ==")
for payload in attacks:
    print(f"  原文：{payload}")
    print(f"  转义：{escape_html(payload)}")

print("\n== 属性上下文 ==")
for payload in attacks[:3]:
    print(f"  <input value=\"{escape_attr(payload)}\">")

# ---------------- 错误 vs 正确渲染 ----------------
def render_comment_bad(comment: str) -> str:
    return f"<div class='comment'>{comment}</div>"


def render_comment_good(comment: str) -> str:
    safe = escape_html(comment)
    return f"<div class='comment'>{safe}</div>"


payload = '<img src=x onerror=alert(1)>'
print("\n== 渲染对比 ==")
print("  错误：", render_comment_bad(payload))
print("  正确：", render_comment_good(payload))

# ---------------- 属性与 URL 的坑 ----------------
print("\n== 危险上下文 ==")
print("  <a href='{user_url}'> → javascript: 伪协议可执行")
print("  <script>var name = '{user_name}'</script> → 字符串逃逸")
print("  正确做法：URL 用白名单协议（http/https），JS 数据用 json.dumps")
import json
name = "'); alert(1); //"
print("  json.dumps 安全嵌入：", json.dumps(name, ensure_ascii=False))

# ---------------- CSP 示例 ----------------
print("\n== CSP（第二道防线）==")
csp = "default-src 'self'; script-src 'self'; object-src 'none'; base-uri 'self'"
print("  Content-Security-Policy:", csp)
print("  作用：即使有注入点，内联脚本和外部恶意脚本也被浏览器阻止")
print("  注意：CSP 不能替代转义，只是降低危害")

# ---------------- 输入校验 vs 输出转义 ----------------
print("\n== 输入校验 vs 输出转义 ==")
rows = [
    ("输入校验", "拒绝明显恶意/非法格式", "不能百分百识别，且数据可能多处使用"),
    ("输出转义", "保证展示安全", "必须按上下文选择正确编码"),
]
print(f"  {'手段':<10}{'作用':<26}{'局限'}")
for r in rows:
    print(f"  {r[0]:<10}{r[1]:<26}{r[2]}")

# ---------------- 框架里的做法 ----------------
print("\n== 框架默认转义 ==")
for item in [
    "Jinja2/Django 模板默认自动转义 HTML",
    "使用 |safe 或 mark_safe 要非常谨慎",
    "React/JSX 默认转义，dangerouslySetInnerHTML 是危险入口",
    "富文本要用白名单清洗（bleach/DOMPurify），不能只转义",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 写函数 render_list(items)，把用户输入安全渲染成 <li>。
# 2. 模拟属性注入：构造一个能逃逸 value 引号的输入，验证转义有效。
# 3. 给一个页面加 CSP，说明每条指令的作用。
# 4. 思考：为什么“过滤 <script> 标签”不是可靠的 XSS 防御？
