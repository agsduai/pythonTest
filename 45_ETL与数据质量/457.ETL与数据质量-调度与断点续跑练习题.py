# ===== 第457课：ETL与数据质量-调度与断点续跑 =====
# 知识点：
#   - 长任务要分页/分批，每批成功后记录游标（checkpoint）
#   - 失败后从游标继续，而不是从头再来（第454课的增量是数据层，本课是任务层）
#   - 状态表：job、cursor、status、last_error、updated_at
#   - 运行状态：idle / running / failed / done；启动时先检查上次状态
#   - 避免重复处理：目标表唯一键 + 幂等写入
# 依赖：无（sqlite3 内置）

import sqlite3
import time


class PagedSource:
    """模拟 5 页、每页 10 条的数据源，第 2 页会偶发失败。"""

    def __init__(self, fail_page=None):
        self.pages = [[f"R{p * 10 + i}" for i in range(10)] for p in range(5)]
        self.fail_page = fail_page
        self.calls = []

    def fetch(self, page: int):
        self.calls.append(page)
        if page == self.fail_page:
            raise ConnectionError(f"第 {page} 页读取超时")
        return self.pages[page]


conn = sqlite3.connect(":memory:")
conn.row_factory = sqlite3.Row
conn.executescript("""
CREATE TABLE target (record_id TEXT PRIMARY KEY, page INTEGER);
CREATE TABLE job_state (
    job TEXT PRIMARY KEY,
    cursor INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'idle',
    last_error TEXT,
    updated_at TEXT DEFAULT (datetime('now'))
);
INSERT INTO job_state (job, cursor, status) VALUES ('orders', 0, 'idle');
""")


def get_state(job="orders"):
    return conn.execute("SELECT * FROM job_state WHERE job = ?", (job,)).fetchone()


def set_state(job, cursor, status, error=None):
    conn.execute("""
        UPDATE job_state
        SET cursor = ?, status = ?, last_error = ?, updated_at = datetime('now')
        WHERE job = ?
    """, (cursor, status, error, job))
    conn.commit()


def run_job(source: PagedSource, job="orders", max_pages=10):
    state = get_state(job)
    if state["status"] == "done":
        print("  任务已完成，跳过")
        return

    cursor = state["cursor"]
    print(f"  从第 {cursor} 页开始（状态 {state['status']}）")
    set_state(job, cursor, "running")
    page = cursor
    pages_done = 0

    try:
        while page < len(source.pages) and pages_done < max_pages:
            print(f"    处理第 {page} 页 ...")
            records = source.fetch(page)
            for rid in records:
                conn.execute(
                    "INSERT INTO target (record_id, page) VALUES (?, ?) "
                    "ON CONFLICT(record_id) DO NOTHING",
                    (rid, page),
                )
            conn.commit()
            page += 1
            pages_done += 1
            set_state(job, page, "running")        # 每页成功后推进游标
    except Exception as exc:
        set_state(job, page, "failed", str(exc))
        print(f"  失败：{exc}（游标停在 {page}）")
        return False

    set_state(job, page, "done")
    print(f"  完成，共处理 {pages_done} 页")
    return True


print("== 第一次运行：第 2 页故障 ==")
source = PagedSource(fail_page=2)
run_job(source)
state = get_state()
print(f"  状态={state['status']} 游标={state['cursor']} 错误={state['last_error']}")
print(f"  目标表已写入：{conn.execute('SELECT COUNT(*) FROM target').fetchone()[0]} 条")

print("\n== 第二次运行：故障修复，从游标续跑 ==")
source2 = PagedSource(fail_page=None)
run_job(source2)
state = get_state()
print(f"  状态={state['status']} 游标={state['cursor']}")
print(f"  目标表共：{conn.execute('SELECT COUNT(*) FROM target').fetchone()[0]} 条")

print("\n== 第三次运行：已完成，直接跳过 ==")
run_job(PagedSource())
print("  访问过的页码（第二次运行）：", source2.calls, "（从 2 开始，没有重跑 0/1）")

print("\n== 数据校验 ==")
rows = conn.execute("SELECT page, COUNT(*) AS cnt FROM target GROUP BY page ORDER BY page").fetchall()
for r in rows:
    print(f"  第 {r['page']} 页：{r['cnt']} 条")
print("  重复记录数：", conn.execute(
    "SELECT COUNT(*) - COUNT(DISTINCT record_id) FROM target").fetchone()[0])

print("\n== 断点续跑设计清单 ==")
for item in [
    "游标 = 下一个要处理的页码/偏移量/主键，不是“已处理条数”",
    "每批成功后立刻持久化游标（失败时最多重做一批）",
    "目标写入必须幂等（UPSERT），防止重做产生重复",
    "记录 last_error 与状态，启动时能判断“继续/重试/人工介入”",
    "增加最大运行时长；超时主动停，避免跑飞",
]:
    print("  -", item)

conn.close()

# ===== 练习题 =====
# 1. 把游标改成“最后处理的 record_id”，支持按主键分页。
# 2. 增加“重试次数”字段：同一页连续失败 3 次才标 failed。
# 3. 模拟运行超时：超过 1 秒主动停止，游标保留在最后成功页。
# 4. 思考：任务层游标与数据层 watermark 有什么区别和联系？
