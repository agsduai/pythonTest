# ===== 第442课：SQLite高级-综合案例-本地知识库 =====
# 知识点：
#   - 综合运用：FTS5（439）+ JSON1（438）+ 触发器同步 + bm25 排序
#   - 结构：notes 普通表存原文与标签（JSON），notes_fts 虚拟表只做索引
#   - 触发器保证两张表一致：INSERT/UPDATE/DELETE 自动同步
#   - 搜索：FTS5 MATCH + 标签过滤（json_each）+ bm25 排序 + snippet 摘要
#   - 这是 Obsidian/Notion 类工具“本地搜索”的最小实现
# 依赖：无（sqlite3 内置 FTS5/JSON1）

import json
import sqlite3
from datetime import datetime

conn = sqlite3.connect(":memory:")
conn.row_factory = sqlite3.Row

# ---------------- 建表 ----------------
conn.executescript("""
CREATE TABLE notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    body TEXT NOT NULL,          -- 中文用空格分词后存储（第382课）
    tags TEXT NOT NULL DEFAULT '[]',
    updated_at TEXT NOT NULL
);
CREATE VIRTUAL TABLE notes_fts USING fts5(title, body);

CREATE TRIGGER notes_ai AFTER INSERT ON notes BEGIN
    INSERT INTO notes_fts(rowid, title, body) VALUES (new.id, new.title, new.body);
END;
CREATE TRIGGER notes_ad AFTER DELETE ON notes BEGIN
    DELETE FROM notes_fts WHERE rowid = old.id;
END;
CREATE TRIGGER notes_au AFTER UPDATE ON notes BEGIN
    UPDATE notes_fts SET title = new.title, body = new.body WHERE rowid = new.id;
END;
""")

# ---------------- 写入笔记 ----------------
NOTES = [
    ("Python 并发 编程", "Python 并发 编程 多线程 多进程 协程 事件 循环 线程 安全",
     ["python", "并发"]),
    ("pandas 数据 分析", "pandas 数据 清洗 分组 透视表 时间 序列 缺失 值 处理",
     ["python", "数据"]),
    ("SQLite 全文 搜索", "SQLite FTS5 全文 搜索 倒排 索引 bm25 排序 摘要",
     ["数据库", "搜索"]),
    ("可靠性 设计", "重试 超时 熔断 限流 幂等 降级 补偿 死信",
     ["架构", "可靠性"]),
]
for title, body, tags in NOTES:
    conn.execute(
        "INSERT INTO notes (title, body, tags, updated_at) VALUES (?, ?, ?, ?)",
        (title, body, json.dumps(tags, ensure_ascii=False),
         datetime.now().isoformat(timespec="seconds")),
    )
conn.commit()
print(f"已写入 {len(NOTES)} 条笔记")

# ---------------- 搜索函数 ----------------
def search(keyword: str, tag: str | None = None, limit: int = 3):
    """FTS5 搜索 + 可选标签过滤 + bm25 排序。"""
    params = [keyword]
    tag_clause = ""
    if tag:
        tag_clause = """
            AND EXISTS (
                SELECT 1 FROM json_each(n.tags) WHERE json_each.value = ?
            )
        """
        params.append(tag)
    params.append(limit)
    return conn.execute(f"""
        SELECT n.id, n.title, n.tags,
               snippet(notes_fts, 1, '[', ']', '…', 12) AS snip,
               bm25(notes_fts) AS score
        FROM notes_fts
        JOIN notes n ON n.id = notes_fts.rowid
        WHERE notes_fts MATCH ? {tag_clause}
        ORDER BY score
        LIMIT ?
    """, params).fetchall()


print("\n== 搜索 '并发' ==")
for r in search("并发"):
    print(f"  [{r['score']:.2f}] {r['title']} | 标签 {r['tags']}")
    print(f"      {r['snip']}")

print("\n== 搜索 '数据' 且标签=python ==")
for r in search("数据", tag="python"):
    print(f"  [{r['score']:.2f}] {r['title']}")
    print(f"      {r['snip']}")

print("\n== 搜索 '搜索' 且标签=数据库 ==")
for r in search("搜索", tag="数据库"):
    print(f"  [{r['score']:.2f}] {r['title']}")

# ---------------- 更新笔记：触发器自动同步索引 ----------------
print("\n== 更新笔记后重新搜索 ==")
conn.execute("""
    UPDATE notes SET body = body || ' 向量 检索 与 关键词 检索 结合',
                     updated_at = ?
    WHERE title = 'SQLite 全文 搜索'
""", (datetime.now().isoformat(timespec="seconds"),))
conn.commit()
for r in search("向量"):
    print(f"  [{r['score']:.2f}] {r['title']}")
    print(f"      {r['snip']}")

# ---------------- 标签统计（JSON1 + json_each）----------------
print("\n== 标签统计 ==")
rows = conn.execute("""
    SELECT json_each.value AS tag, COUNT(*) AS cnt
    FROM notes, json_each(notes.tags)
    GROUP BY tag ORDER BY cnt DESC, tag
""").fetchall()
for r in rows:
    print(f"  {r['tag']}: {r['cnt']} 篇")

# ---------------- 删除笔记：索引同步清理 ----------------
print("\n== 删除一篇后搜索 ==")
conn.execute("DELETE FROM notes WHERE title = '可靠性 设计'")
conn.commit()
for keyword in ("熔断", "并发"):
    hits = search(keyword)
    print(f"  {keyword}: {[r['title'] for r in hits]}")

# ---------------- 一致性自检 ----------------
print("\n== 索引一致性自检 ==")
notes_count = conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
fts_count = conn.execute("SELECT COUNT(*) FROM notes_fts").fetchone()[0]
print(f"  notes={notes_count} | notes_fts={fts_count} | 一致={notes_count == fts_count}")

conn.close()

# ===== 练习题 =====
# 1. 给 search 增加“按标签列表过滤”（OR 关系）。
# 2. 增加 notes_history 表，用触发器记录每次修改的旧版本。
# 3. 把知识库持久化到文件，启动时加载（第441课备份）。
# 4. 思考：FTS5 表与原文表用触发器同步，有什么性能代价？
