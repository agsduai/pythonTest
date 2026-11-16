# ===== 第444课：可靠性设计-超时控制 =====
# 知识点：
#   - 没有超时的等待 = 永久挂起；每个外部调用都必须设上限
#   - 网络场景：socket timeout / HTTP 客户端 timeout（连接+读取分开设）
#   - 线程方案：future.result(timeout) 只能“不再等待”，线程仍在后台跑
#   - 进程方案：subprocess.run(timeout) 超时会杀掉子进程，真正止损
#   - 设计原则：超时时间要小于上游给你的时间预算（第443课重试总预算）
import socket
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError


# ---- 1. 线程超时：能返回，但线程不会停 ----
def slow_task(seconds):
    time.sleep(seconds)
    return f"完成（{seconds}s）"


print("== 线程超时（注意：后台线程仍在跑）==")
start = time.perf_counter()
pool = ThreadPoolExecutor(max_workers=1)
future = pool.submit(slow_task, 1.0)
try:
    result = future.result(timeout=0.2)
    print("  结果：", result)
except TimeoutError:
    print("  0.2s 未完成，上层得到 TimeoutError（线程仍在后台执行）")
    print("  说明：Python 线程无法被强制杀死，只能“不再等”")
pool.shutdown(wait=False, cancel_futures=True)
print(f"  主流程耗时 {time.perf_counter() - start:.2f}s（没有等满 1s）")

# ---- 2. 进程超时：真正杀掉，适合可隔离的任务 ----
print("\n== 子进程超时（会被杀掉）==")
start = time.perf_counter()
try:
    subprocess.run(
        [sys.executable, "-c", "import time; time.sleep(5)"],
        timeout=0.3,
        check=True,
    )
except subprocess.TimeoutExpired:
    print("  子进程 0.3s 未结束，已被强制终止")
print(f"  主流程耗时 {time.perf_counter() - start:.2f}s")

# ---- 3. socket 超时：网络调用的标准姿势 ----
print("\n== socket 超时 ==")
# 连接本机未监听的端口：设置 timeout 后不会无限等待
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(0.2)
start = time.perf_counter()
try:
    sock.connect(("127.0.0.1", 9))          # 通常无服务监听
except (socket.timeout, ConnectionRefusedError, OSError) as exc:
    print(f"  连接失败/超时（{type(exc).__name__}），耗时 {time.perf_counter() - start:.2f}s")
finally:
    sock.close()

# ---- 4. 超时预算的层级设计 ----
print("\n== 超时预算（示例）==")
BUDGET = {
    "上游给本服务": 3.0,
    "调用下游 A": 1.0,
    "调用下游 B": 0.8,
    "数据库查询": 0.5,
    "重试总时长": 2.0,     # 不能超过 3.0
}
for name, seconds in BUDGET.items():
    print(f"  {name}: {seconds}s")
print("  原则：下层超时之和 < 上层预算，留出处理和网络开销的余量")

# ---- 5. 超时后的清理 ----
print("\n== 超时后要做的三件事 ==")
for item in [
    "释放资源：关闭 socket/文件/连接（with 语句）",
    "记录日志：哪个依赖、等了多久、是否重试（第417课）",
    "向上返回明确错误：不要让调用方一直等",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 写 timeout_call(func, seconds)，用线程实现并返回 (结果, 是否超时)。
# 2. 给第410课的 HTTP 客户端加 2 秒超时。
# 3. 思考：为什么数据库连接池通常要同时设“连接超时”和“查询超时”？
