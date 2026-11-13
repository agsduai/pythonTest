# ===== 第282课：实用脚本-日志与异常兜底 =====
# 知识点：
#   - 脚本健壮性三件套：logging 留现场（第216课）+ 异常兜底 + 明确退出码
#   - 单项任务失败不拖垮整体：try 包住每项，失败记录后继续
#   - 退出码约定：0 成功，非 0 失败 —— 供任务计划/CI 判断
#   - finally：无论成败都执行的收尾（关文件、删临时目录）

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    force=True,
)
log = logging.getLogger("demo_script")


def risky_task(n):
    log.info("开始处理 %s", n)
    if n < 0:
        raise ValueError("数量不能为负")
    return n * 2


def main():
    results, failures = [], []
    for n in (1, -5, 3):
        try:
            results.append(risky_task(n))
        except ValueError as exc:
            log.error("处理 %s 失败：%s", n, exc)     # 记录现场，继续下一项
            failures.append(n)
    log.info("成功 %d 项：%s", len(results), results)
    if failures:
        log.warning("失败 %d 项：%s", len(failures), failures)
    return 0 if not failures else 1


exit_code = main()
print("模拟退出码：", exit_code, "（真实脚本用 sys.exit(exit_code)）")

# 兜底模板（可直接抄进脚本）：
#   def main():
#       ...
#   if __name__ == "__main__":
#       try:
#           sys.exit(main())
#       except KeyboardInterrupt:
#           log.warning("用户中断")
#           sys.exit(130)
#       except Exception:
#           log.exception("未预期的错误")     # exception() 自动带上堆栈
#           sys.exit(1)

# ===== 练习题 =====
# 1. 把第278课备份脚本套上本课兜底模板。
# 2. 用 log.exception 故意触发一个未捕获异常，观察堆栈输出。
# 3. 思考：哪些错误该“记录后继续”，哪些该“立即终止”？
