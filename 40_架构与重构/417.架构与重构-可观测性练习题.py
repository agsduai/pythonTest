# ===== 第417课：架构与重构-可观测性 =====
# 知识点：
#   - 可观测性三件套：日志（发生了什么）、指标（发生多少）、追踪（一次请求走了哪）
#   - 结构化日志：JSON 输出，方便 ELK/Loki 检索（不是给人“读”，是给机器“查”）
#   - correlation id：一次请求全链路用同一个 ID，串起所有日志
#   - 指标：计数器（次数）、计时（耗时），用 Counter/字典聚合
#   - 装饰器统一埋点，业务代码零侵入（第187课）
import contextvars
import json
import logging
import time
import uuid
from collections import Counter
from functools import wraps

request_id = contextvars.ContextVar("request_id", default="-")
METRICS = Counter()
TIMING: dict[str, float] = {}


class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "req_id": request_id.get(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


logger = logging.getLogger("observability")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logger.addHandler(handler)
logger.propagate = False          # 避免 root logger 重复输出


def observed(func):
    """统一埋点：成功/失败计数 + 耗时统计。"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            METRICS[f"{func.__name__}.ok"] += 1
            return result
        except Exception:
            METRICS[f"{func.__name__}.error"] += 1
            logger.exception("处理失败")        # exception() 自动带堆栈
            raise
        finally:
            cost_ms = (time.perf_counter() - start) * 1000
            TIMING[func.__name__] = TIMING.get(func.__name__, 0) + cost_ms

    return wrapper


@observed
def handle_request(path: str):
    if path == "/ok":
        time.sleep(0.01)
        return {"status": 200}
    if path == "/slow":
        time.sleep(0.05)
        return {"status": 200}
    raise ValueError(f"未知路径 {path}")


def serve(path: str):
    """模拟一次请求：设置 correlation id，记录开始/结束。"""
    token = request_id.set(uuid.uuid4().hex[:8])
    try:
        logger.info("开始处理 %s", path)
        result = handle_request(path)
        logger.info("处理完成 %s → %s", path, result["status"])
        return result
    except Exception as exc:
        logger.error("处理异常 %s：%s", path, exc)
        return {"status": 500}
    finally:
        request_id.reset(token)


print("== 处理 4 个请求（日志为 JSON 行）==")
for path in ("/ok", "/slow", "/missing", "/ok"):
    serve(path)

print("\n== 指标汇总 ==")
for key, value in sorted(METRICS.items()):
    print(f"  {key:20s} = {value}")
print("\n== 平均耗时 ==")
for name, total in TIMING.items():
    count = METRICS[f"{name}.ok"] + METRICS[f"{name}.error"]
    print(f"  {name}: {total / count:.2f} ms/次（{count} 次）")

# 落地建议：
#   日志 → 文件/标准输出，由采集器统一收集
#   指标 → Counter/摘要，定期上报（Prometheus 格式）
#   追踪 → 每个请求生成 trace_id，跨服务透传（HTTP Header）
#   告警 → 错误率/耗时 P99 超阈值时触发（第403课配置中心）

# ===== 练习题 =====
# 1. 给 METRICS 增加耗时分位数（P50/P95）统计。
# 2. 让 correlation id 从 HTTP Header 读取（有则复用，无则新建）。
# 3. 用 JSON 日志文件 + 第227课正则，统计每个接口的调用次数。
# 4. 思考：日志太多和日志太少，各会带来什么问题？
