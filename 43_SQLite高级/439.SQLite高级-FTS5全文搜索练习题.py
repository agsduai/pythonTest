# ===== 第439课：SQLite高级-FTS5全文搜索 =====
# 知识点：
#   - FTS5 是 SQLite 内置的全文索引引擎（虚拟表），比 LIKE '%词%' 快几个数量级
#   - MATCH 查询支持 AND/OR/NOT、前缀（word*）、短语（"a b"）
#   - 排序用 bm25(表)：返回值越小越相关（通常 ORDER BY bm25(tbl)）
#   - snippet() 返回带上下文的摘要；highlight() 只做高亮标记
#   - 中文没有空格：需要先分词（第382课），演示里把中文预处理成空格分隔
#   - 工程上常与普通表配合（内容存普通表，FTS 表做索引）
# 依赖：无（sqlite3 内置 FTS5）

import sqlite3

conn = sqlite3.connect(":memory:")
conn.row_factory = sqlite3.Row

# 1) 建 FTS5 虚拟表（title/body 两列）
conn.execute("CREATE VIRTUAL TABLE docs USING fts5(title, body)")

# 2) 中文先“空格分词”再入库（真实项目用 jieba / 第382课的最大匹配）
DOCS = [
    ("Python 并发 编程", "Python 并发 编程 包括 多线程 多进程 与 协程 事件 循环"),
    ("Python 数据 分析", "pandas 数据 清洗 分组 透视表 时间 序列 可视化"),
    ("SQLite 全文 搜索", "SQLite FTS5 支持 全文 搜索 排序 摘要 高亮"),
    ("算法 入门", "二分 查找 排序 哈希表 动态 规划 时间 复杂度"),
    ("机器学习 入门", "特征 缩放 线性 回归 逻辑 回归 KNN 聚类 评估"),
]
conn.executemany("INSERT INTO docs (title, body) VALUES (?, ?)", DOCS)

print("== 基本搜索：MATCH 'python' ==")
rows = conn.execute("""
    SELECT rowid, title, bm25(docs) AS score
    FROM docs WHERE docs MATCH 'python'
    ORDER BY score
""").fetchall()
for r in rows:
    print(f"  [{r['score']:.3f}] {r['title']}")

print("\n== 多词 AND：'并发 协程' ==")
rows = conn.execute("""
    SELECT rowid, title,
           snippet(docs, 1, '[', ']', '…', 10) AS snip,
           bm25(docs) AS score
    FROM docs WHERE docs MATCH '并发 协程'
    ORDER BY score
""").fetchall()
for r in rows:
    print(f"  [{r['score']:.3f}] {r['title']}")
    print(f"      摘要：{r['snip']}")

print("\n== OR 查询：'pandas OR 协程' ==")
rows = conn.execute("""
    SELECT title, bm25(docs) AS score FROM docs
    WHERE docs MATCH 'pandas OR 协程'
    ORDER BY score
""").fetchall()
for r in rows:
    print(f"  [{r['score']:.3f}] {r['title']}")

print("\n== 前缀查询：'数据*' ==")
rows = conn.execute("""
    SELECT title FROM docs WHERE docs MATCH '数据*' ORDER BY bm25(docs)
""").fetchall()
print("  ", [r["title"] for r in rows])

print("\n== 短语查询：\"机器 学习\"（顺序必须一致）==")
rows = conn.execute("""
    SELECT title FROM docs WHERE docs MATCH '"机器 学习"'
""").fetchall()
print("  ", [r["title"] for r in rows])

print("\n== 高亮：highlight ==")
rows = conn.execute("""
    SELECT title, highlight(docs, 1, '<b>', '</b>') AS marked
    FROM docs WHERE docs MATCH '搜索'
""").fetchall()
for r in rows:
    print(f"  {r['title']}")
    print(f"    {r['marked']}")

print("\n== 对比 LIKE 的差距（示意）==")
rows = conn.execute("""
    SELECT title FROM docs WHERE body LIKE '%搜索%'
""").fetchall()
print("  LIKE 结果：", [r["title"] for r in rows])
print("  小数据一样，百万行时 FTS5 走倒排索引，LIKE 要全表扫描")

# ---- 中文分词提醒 ----
print("\n注意：FTS5 默认按空格/标点切词。")
print("  中文正文如果不分词，整句会成为一个 token，搜“并发”将匹配不到。")
print("  生产做法：入库前用 jieba/最大匹配切词，空格拼接；或用 trigram 分词器。")

conn.close()

# ===== 练习题 =====
# 1. 给 docs 增加 tags 列，测试 MATCH 'tag:python' 的列限定语法。
# 2. 实现“搜索建议”：用 FTS5 的 vocab 表或前缀查询返回补全词。
# 3. 用 trigram 分词器建表，测试中文两字查询是否可用。
# 4. 思考：FTS5 表与原文表如何保持一致？（下一章 442 用触发器演示）
