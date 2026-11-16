# ===== 第631课：终端与命令行应用-进度与日志输出 =====
# 知识点：
#   - 进度条用 \r 覆写同一行，配合 flush=True；结束时补换行避免提示符粘住
#   - 日志分级：DEBUG < INFO < WARNING < ERROR < CRITICAL，按 level 过滤
#   - logging.Formatter 统一格式；StreamHandler 与 FileHandler 分别输出到终端/文件
#   - 进度信息不该进日志：高频、易变、无保留价值；日志也不该刷屏覆盖进度
#   - 用 io.StringIO 捕获输出做单测，避免测试时污染真实终端
#   - 耗时估算：已用时间 / 完成比例 - 已用时间 = ETA，需防止除零
# 依赖：无（标准库）
import io
import logging
import time


def render_bar(done, total, width=24, elapsed=0.0) -> str:
    ratio = done / total if total else 1.0
    filled = int(width * ratio)
    bar = "█" * filled + "░" * (width - filled)
    eta = (elapsed / ratio - elapsed) if ratio > 0 else 0.0
    return f"\r  [{bar}] {done}/{total} {ratio:5.1%}  已用 {elapsed:4.1f}s  ETA {eta:4.1f}s"


def run_with_progress(items, sink, delay=0.0):
    """模拟逐项处理，把进度帧写入 sink（可注入，便于测试）。"""
    start = time.perf_counter()
    results = []
    for i, item in enumerate(items, 1):
        time.sleep(delay)
        results.append(item * item)
        elapsed = time.perf_counter() - start
        sink.write(render_bar(i, len(items), elapsed=elapsed))
    sink.write("\n")     # 结束补换行
    return results


print("== 进度条帧（用 StringIO 捕获，不刷屏）==")
buf = io.StringIO()
results = run_with_progress(list(range(1, 6)), buf)
frames = buf.getvalue().replace("\r", "\n").strip().splitlines()
for f in frames[:3] + ["  ..."] + frames[-2:]:
    print("  " + f)
print("  处理结果:", results)

print("\n== 空任务与边界 ==")
for total in (0, 1, 3):
    b = io.StringIO()
    run_with_progress(range(total), b)
    print(f"  total={total}: 输出帧数={b.getvalue().count(chr(13))}，末尾换行={b.getvalue().endswith(chr(10))}")

print("\n== logging 分级与格式 ==")
logger = logging.getLogger("demo")
logger.setLevel(logging.DEBUG)
logger.handlers.clear()
stream = io.StringIO()
handler = logging.StreamHandler(stream)
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)-8s %(name)s | %(message)s",
                                       datefmt="%H:%M:%S"))
logger.addHandler(handler)

for level, msg in (
    (logging.DEBUG, "解析配置完成"), (logging.INFO, "开始处理 5 个文件"),
    (logging.WARNING, "第 3 个文件编码未知，按 UTF-8 读取"),
    (logging.ERROR, "写入失败，已跳过"), (logging.CRITICAL, "磁盘空间不足"),
):
    logger.log(level, msg)
print(stream.getvalue(), end="")

print("\n== 按 level 过滤 ==")
for level_name in ("DEBUG", "INFO", "WARNING", "ERROR"):
    s = io.StringIO()
    h = logging.StreamHandler(s)
    h.setFormatter(logging.Formatter("%(levelname)s:%(message)s"))
    lg = logging.getLogger("filter_" + level_name)
    lg.handlers.clear(); lg.addHandler(h); lg.setLevel(getattr(logging, level_name))
    lg.propagate = False
    lg.debug("d"); lg.info("i"); lg.warning("w"); lg.error("e")
    print(f"  {level_name:<8} -> {s.getvalue().strip().split()}")

print("\n== 同时输出到终端与文件 ==")
import tempfile
from pathlib import Path
with tempfile.TemporaryDirectory() as tmp:
    logpath = Path(tmp) / "app.log"
    lg = logging.getLogger("dual")
    lg.handlers.clear(); lg.setLevel(logging.INFO); lg.propagate = False
    fmt = logging.Formatter("%(levelname)s %(message)s")
    sh = logging.StreamHandler(io.StringIO()); sh.setFormatter(fmt); sh.setLevel(logging.WARNING)
    fh = logging.FileHandler(logpath, encoding="utf-8"); fh.setFormatter(fmt); fh.setLevel(logging.INFO)
    lg.addHandler(sh); lg.addHandler(fh)
    lg.info("这条只进文件"); lg.warning("这条两端都有")
    fh.flush(); fh.close()
    print(f"  文件内容: {logpath.read_text('utf-8').strip().splitlines()}")
    print(f"  终端内容: {sh.stream.getvalue().strip().splitlines()}")

print("\n== 进度与日志的分工 ==")
for line in [
    "进度：高频、临时、面向人 -> \r 覆写同一行，不落盘",
    "日志：低频、持久、面向排查 -> 带时间戳/级别，落文件",
    "长任务每隔 N% 打一条 INFO 日志，进度条仍逐帧刷新",
    "CI / 非 TTY 环境应关闭进度覆写，改为每 10% 打一行日志",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 给进度条增加「当前处理对象名称」后缀，并保证超长名称不会撑破行宽。
# 2. 实现 should_render(i, total, is_tty)，非 TTY 时每 10% 输出一行普通文本。
# 3. 用 logging.Filter 给所有日志注入固定的 run_id 字段。
# 4. 思考：为什么 ETA 要用「已用时间 / 完成比例」而不是简单线性外推到最后一项？
