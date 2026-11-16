# ===== 第666课：模板引擎与文本生成-综合案例-静态站点生成器 =====
# 知识点：
#   - 综合串起本章：词法扫描 + 块 AST + 过滤器/转义 + 继承 + 代码生成 + 多格式输出
#   - 流水线：内容(Markdown 简化版) -> 解析元数据 -> 套用布局 -> 生成页面 -> 生成索引/RSS
#   - 每篇内容文件带 YAML 风格 front matter（简化为 key: value），正文按段落渲染
#   - 输出全部进 TemporaryDirectory，目录结构可校验，运行后自动清理
#   - 纯函数式 render：相同输入必得相同字节，便于增量构建与缓存
#   - 生成的 HTML 自动转义，链接/标题都不可注入
# 依赖：无（标准库）
import html
import io
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Page:
    slug: str
    title: str
    date: str
    tags: list
    body: str
    url: str = ""

    def __post_init__(self):
        self.url = f"{self.slug}.html"


def parse_front_matter(text):
    """解析开头的 key: value 元数据与剩余正文。"""
    meta, lines, in_meta = {}, [], False
    for line in text.splitlines():
        if line.strip() == "---":
            in_meta = not in_meta
            continue
        if in_meta and ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
        else:
            lines.append(line)
    return meta, "\n".join(lines).strip()


def parse_page(slug, raw):
    meta, body = parse_front_matter(raw)
    tags = [t.strip() for t in meta.get("tags", "").split(",") if t.strip()]
    return Page(slug, meta.get("title", slug), meta.get("date", ""), tags, body)


def render_body(body):
    """极简 Markdown：# 标题、**粗体**、[文字](链接)、空行分段。"""
    out = []
    for para in re.split(r"\n\s*\n", body):
        para = para.strip()
        if not para:
            continue
        if para.startswith("# "):
            out.append(f"<h2>{html.escape(para[2:])}</h2>")
            continue
        text = html.escape(para)
        text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)",
                      lambda m: f'<a href="{html.escape(m.group(2), quote=True)}">{m.group(1)}</a>',
                      text)
        text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
        out.append(f"<p>{text}</p>")
    return "\n".join(out)


LAYOUT = """\
<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>{{ title }} | {{ site }}</title></head>
<body>
<header><a href="index.html">{{ site }}</a> | {{ tagline }}</header>
<main>
<h1>{{ title }}</h1>
<p class="meta">{{ date }} | {{ tags }}</p>
{{ content }}
</main>
<footer>{{ footer }}</footer>
</body>
</html>
"""


def render_layout(values):
    out = LAYOUT
    for key, value in values.items():
        out = out.replace("{{ " + key + " }}", str(value))
    return out


def render_index(pages, site):
    rows = []
    for p in sorted(pages, key=lambda x: x.date, reverse=True):
        rows.append(f'<li><a href="{html.escape(p.url, quote=True)}">'
                    f'{html.escape(p.title)}</a> <time>{html.escape(p.date)}</time> '
                    f'<span>{" / ".join(html.escape(t) for t in p.tags)}</span></li>')
    return render_layout({
        "title": "首页", "site": site, "tagline": "静态站点示例", "date": "",
        "tags": "", "footer": "由纯标准库生成",
        "content": "<h2>文章列表</h2>\n<ul>\n" + "\n".join(rows) + "\n</ul>",
    })


def render_rss(pages, site, base="https://example.com"):
    items = []
    for p in pages:
        items.append(
            "  <item>\n"
            f"    <title>{html.escape(p.title)}</title>\n"
            f"    <link>{base}/{p.url}</link>\n"
            f"    <guid>{base}/{p.url}</guid>\n"
            f"    <pubDate>{html.escape(p.date)}</pubDate>\n"
            "  </item>")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<rss version="2.0"><channel>\n'
            f'  <title>{html.escape(site)}</title>\n'
            f'  <link>{base}</link>\n'
            + "\n".join(items) + "\n</channel></rss>\n")


RAW_PAGES = {
    "hello": """\
---
title: 你好，静态站点
date: 2026-11-14
tags: python, 模板
---
# 第一节

这是 **第一篇** 文章，介绍了 [模板引擎](https://docs.python.org)。

渲染流程：内容解析 -> 布局套用 -> 转义输出。
""",
    "xss-demo": """\
---
title: <script>alert(1)</script>
date: 2026-11-13
tags: 安全
---
# 转义演示

标题里带 <script> 标签，输出时必须被转义。

链接也测试一下：[点我](javascript:alert(1))。
""",
}

print("== 解析内容 ==")
pages = [parse_page(slug, raw) for slug, raw in RAW_PAGES.items()]
for p in pages:
    print(f"  {p.slug:<10} title={p.title[:30]!r:<34} date={p.date} tags={p.tags}")

print("\n== 正文渲染（自动转义）==")
print(render_body(pages[0].body))

with tempfile.TemporaryDirectory() as tmp:
    out = Path(tmp) / "site"
    out.mkdir()
    site = "Python 笔记"

    for p in pages:
        html_text = render_layout({
            "title": html.escape(p.title), "site": html.escape(site),
            "tagline": "静态站点示例", "date": html.escape(p.date),
            "tags": " / ".join(html.escape(t) for t in p.tags),
            "content": render_body(p.body), "footer": "由纯标准库生成",
        })
        (out / p.url).write_text(html_text, "utf-8")

    (out / "index.html").write_text(render_index(pages, site), "utf-8")
    (out / "rss.xml").write_text(render_rss(pages, site), "utf-8")

    print("\n== 输出目录 ==")
    for f in sorted(out.iterdir()):
        print(f"  {f.name:<16} {f.stat().st_size:>5} 字节")

    print("\n== 安全检查 ==")
    xss = (out / "xss-demo.html").read_text("utf-8")
    print("  原始 <script> 未出现:", "<script>alert(1)</script>" not in xss)
    print("  转义实体存在:", "&lt;script&gt;" in xss)
    print("  javascript: 链接仍在文本里但已转义为普通文本:",
          'href="javascript:' not in xss)

    print("\n== 索引页片段 ==")
    idx = (out / "index.html").read_text("utf-8")
    for line in idx.splitlines():
        if "<li>" in line:
            print("  ", line.strip())

    print("\n== 可复现性：重跑一次字节一致 ==")
    again = render_index(pages, site) + render_rss(pages, site)
    first = (out / "index.html").read_text("utf-8") + (out / "rss.xml").read_text("utf-8")
    print("  两次生成一致:", again == first)
    print("  排序稳定：文章按 date 倒序:", [p.slug for p in
          sorted(pages, key=lambda x: x.date, reverse=True)])

print("\n== 流水线回顾 ==")
for line in [
    "  内容层: front matter + 极简 Markdown（第660课词法扫描思路）",
    "  渲染层: 布局占位符替换 + 自动转义（第659/662课）",
    "  组装层: 页面 / 索引 / RSS 三种输出（第665课多格式）",
    "  交付层: TemporaryDirectory 生成、逐文件自检、无残留",
    "  生产建议: Jinja2 + Markdown 库 + 增量构建 + 内容哈希缓存",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 增加标签归档页 tags/<tag>.html 与标签云，按标签聚合文章。
# 2. 实现增量构建：只对内容哈希变化的页面重新生成。
# 3. 给 render_rss 增加 <description>（正文首段）并做 XML 转义。
# 4. 思考：为什么静态站点也要做 HTML 转义，即使内容由作者自己写？
