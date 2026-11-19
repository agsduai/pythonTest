# ===== 第1049课：日期与时间处理-时间戳转换 =====
# 知识点：
#   - 时间戳：从 1970-01-01 00:00 起的秒数，是跨系统通用的"时间语言"
#   - time.time() 取当前时间戳（float）；datetime.timestamp() 对象转时间戳
#   - datetime.fromtimestamp() 时间戳转回 datetime
#   - 实际场景：接口返回的时间戳、缓存过期判断、去重 ID

# 案例一：当前时间戳
import time
from datetime import datetime

ts = time.time()
print(f"当前时间戳：{ts}")  # 例如 1705287045.123
print(f"整数秒：{int(ts)}")

# 案例二：时间戳 <-> datetime 互转
# 场景：接口返回 1705287045，要显示成人类可读
api_ts = 1705287045
dt = datetime.fromtimestamp(api_ts)
print(f"接口时间戳 {api_ts} -> {dt.strftime('%Y-%m-%d %H:%M:%S')}")

# 反向：对象转时间戳
now = datetime.now()
back_ts = now.timestamp()
print(f"当前对象转回时间戳：{int(back_ts)}")

# 案例三：用时间戳算程序耗时
# 场景：统计一段代码跑了多久
start_ts = time.time()
total = sum(i * i for i in range(100_000))
cost = time.time() - start_ts
print(f"计算完成（总和 {total}），耗时 {cost:.4f} 秒")

# 案例四：缓存过期判断
# 场景：数据写入时记时间戳，超过 10 秒视为过期
cached_at = time.time() - 15  # 模拟 15 秒前写入的缓存
CACHE_TTL = 10  # 有效期 10 秒
age = time.time() - cached_at
if age > CACHE_TTL:
    print(f"缓存已过期（{age:.0f} 秒 > {CACHE_TTL} 秒），重新加载")
else:
    print(f"缓存有效（{age:.0f} 秒），直接使用")

# 案例五：时间戳做唯一标识
# 场景：生成不重复的流水号
order_no = f"ORD{int(time.time() * 1000)}"  # 毫秒级，同秒内也几乎不重
print(f"流水号：{order_no}")

# ===== 练习题 =====
# 1. 用 int(time.time()) 输出当前时间戳，再用 fromtimestamp 转回 datetime 并格式化打印。
# 2. 写函数 is_expired(ts, ttl)：ts 距今超过 ttl 秒返回 True，用"30 秒前 + ttl=10"和"5 秒前 + ttl=10"两组测试。
# 3. 已知时间戳 946684800（2000-01-01），打印它距离现在过去了多少天（用 (time.time() - ts) / 86400，保留 1 位小数）。
