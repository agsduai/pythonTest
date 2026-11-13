# ===== 第216课：测试与工程化-logging日志 =====
# 知识点：
#   - logging 比 print 强：分级、时间戳、可输出到文件、可整体开关
#   - 五个级别：DEBUG < INFO < WARNING < ERROR < CRITICAL
#   - basicConfig 设定级别与格式；默认只显示 WARNING 及以上
#   - 模块内用 getLogger(__name__) 获取独立 logger，便于定位来源
#   - 项目里“排查问题的现场证据”靠日志，不靠回忆

import logging
import os

# 全局配置：级别、格式（一般放在程序入口执行一次）
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

# 模块级 logger，name 通常是模块名，便于定位日志来源
logger = logging.getLogger(__name__)


def process_order(order_id, amount):
    logger.debug("处理订单 %s，金额 %.2f", order_id, amount)     # 调试细节
    if amount <= 0:
        logger.warning("订单 %s 金额异常：%.2f", order_id, amount)
        return False
    logger.info("订单 %s 处理成功", order_id)
    return True


process_order("A001", 99.5)
process_order("A002", -1)

# 输出到文件：加 filename 参数（force=True 覆盖之前的控制台配置，演示用）
logging.basicConfig(
    filename="app_216.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    force=True,
)
logger2 = logging.getLogger("file-demo")
logger2.info("这条日志写进了文件 app_216.log")
logger2.error("错误级别示例：数据库连接失败")
print("控制台没有上面两条日志 —— 打开 app_216.log 检查内容")

logging.shutdown()           # 关闭所有日志句柄（否则 Windows 上删除文件会报错）
os.remove("app_216.log")     # 清理演示文件

# ===== 练习题 =====
# 1. 把 level 改成 logging.WARNING，观察 debug/info 是否消失。
# 2. 给第210课学生管理系统的 add/delete 操作加上日志。
# 3. 用 FileHandler + StreamHandler 让日志同时输出到控制台和文件。
# 4. 思考：什么信息该记 INFO，什么该记 ERROR？
