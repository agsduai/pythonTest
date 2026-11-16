# ===== 第825课：并发模式与并发容器-死锁检测与并发调试 =====
# 知识点：
#   - 死锁四条件：互斥、持有并等待、不可抢占、循环等待
#   - 预防：锁排序（始终按固定顺序获取多把锁）
#   - 检测：用「等待图」检测环，或用超时 + 重试
#   - Python 调试：threading.enumerate() 列出所有线程
#   - Lock.acquire(timeout=n) 超时获取，可检测是否死锁
#   - Livelock：线程不阻塞但永远无法前进（互相让步导致）
# 依赖：无（标准库）
import threading
import time
import random


print("== 死锁演示：锁顺序反转 ==")
lock_a = threading.Lock()
lock_b = threading.Lock()
deadlock_detected = [False]

def thread_1():
    with lock_a:
        import time; time.sleep(0.05)         # 确保对方也拿到 lock_a
        got_b = lock_b.acquire(timeout=1)     # 超时获取，不死锁
        if got_b:
            lock_b.release()
        else:
            deadlock_detected[0] = True

def thread_2():
    with lock_b:
        import time; time.sleep(0.05)
        got_a = lock_a.acquire(timeout=1)
        if got_a:
            lock_a.release()
        else:
            deadlock_detected[0] = True

t1 = threading.Thread(target=thread_1)
t2 = threading.Thread(target=thread_2)
t1.start(); t2.start()
t1.join(timeout=3); t2.join(timeout=3)
print(f"  检测到死锁: {deadlock_detected[0]}")
print("  T1 持 A 等 B，T2 持 B 等 A → 循环等待 → 死锁")
print("  用 timeout=1 获取而不是永久阻塞，可以检测到死锁")

print("\n== 预防：锁排序 ==")
lock_1 = threading.Lock()
lock_2 = threading.Lock()

def safe_transfer(from_lock, to_lock, amount):
    """始终按锁对象 ID 排序获取，避免死锁。"""
    locks = sorted([from_lock, to_lock], key=lambda l: id(l))
    with locks[0]:
        with locks[1]:
            print(f"    安全转账 {amount}（锁顺序: {id(locks[0]) % 10000}, {id(locks[1]) % 10000}）")

print("  锁排序方案:")
safe_transfer(lock_1, lock_2, 100)
safe_transfer(lock_2, lock_1, 50)
print("  两次调用都按相同顺序获取锁 → 不会死锁")

print("\n== 锁顺序实现：全局排序函数 ==")
LOCK_REGISTRY = {}
_registry_lock = threading.Lock()

def get_lock(name):
    with _registry_lock:
        if name not in LOCK_REGISTRY:
            LOCK_REGISTRY[name] = threading.Lock()
        return LOCK_REGISTRY[name]

def acquire_all(lock_names):
    """按名字排序获取所有锁（保证全局顺序一致）。"""
    sorted_names = sorted(lock_names)
    acquired = []
    for name in sorted_names:
        lock = get_lock(name)
        acquired.append(lock)
    for lock in acquired:
        lock.acquire()
    return acquired

def release_all(locks):
    for lock in reversed(locks):
        lock.release()

locks = acquire_all(["resource_b", "resource_a", "resource_c"])
print(f"  获取了 {len(locks)} 把锁（按名字排序）")
release_all(locks)
print("  释放完成")

print("\n== Livelock：互相让步导致无法前进 ==")
class LivelockExample:
    def __init__(self):
        self.lock = threading.Lock()
        self.done = False

    def worker(self, name, other_name):
        attempts = 0
        while not self.done and attempts < 5:
            if self.lock.acquire(timeout=0.1):
                # 检查对方是否也在尝试
                if attempts % 2 == 0:
                    self.lock.release()        # 让步
                    import time; time.sleep(0.01)
                else:
                    self.done = True           # 完成工作
                    self.lock.release()
                    return
                attempts += 1
            else:
                import time; time.sleep(0.01)
                attempts += 1

    def demo(self):
        t1 = threading.Thread(target=self.worker, args=("W1", "W2"))
        t2 = threading.Thread(target=self.worker, args=("W2", "W1"))
        t1.start(); t2.start()
        t1.join(timeout=3); t2.join(timeout=3)

ll = LivelockExample()
print("  Livelock 示例：两个 worker 互相让步，谁也无法完成")
print("  与死锁的区别：线程没有阻塞，但永远在做无用功")
print("  缓解：引入随机退避（像以太网 CSMA/CD）或让一方优先")

print("\n== 并发调试工具 ==")
print("  1. threading.enumerate(): 列出所有活跃线程")
threads = [threading.Thread(target=lambda: None, name=f"test-{i}") for i in range(3)]
for t in threads: t.start()
for t in threads: t.join()
print(f"  当前线程数: {threading.active_count()}")
for t in threading.enumerate():
    print(f"    {t.name} (daemon={t.daemon}, alive={t.is_alive()})")

print("\n  2. threading.current_thread(): 当前线程信息")
print(f"     当前线程: {threading.current_thread().name}")

print("\n  3. 锁超时检测死锁")
lock = threading.Lock()
lock.acquire()
got = lock.acquire(timeout=0.5)     # 同一线程用普通 Lock 会超时
print(f"     Lock.acquire(timeout=0.5) 二次获取 = {got}（可检测死锁）")
lock.release()

print("\n== 死锁预防检查清单 ==")
for line in [
    "  ✗ 避免嵌套锁：一次只持一把锁",
    "  ✗ 必须嵌套时：始终按全局排序获取",
    "  ✗ 持锁时不要调用未知代码（可能获取其他锁）",
    "  ✓ 用 timeout= 获取锁，失败就走降级/重试路径",
    "  ✓ 用 threading.RLock 替代 Lock（可重入，不会自锁）",
    "  ✓ 尽量用消息传递（第822课 Actor）或 CSP（第823课 Channel）消除锁",
]:
    print("  -", line)

print("\n== 并发调试技巧 ==")
for line in [
    "  faulthandler 模块：崩溃时打印所有线程的堆栈（import faulthandler; faulthandler.enable()）",
    "  threading.settrace()：给所有新线程设置 trace 函数",
    "  日志记录锁的获取/释放（用 logging + Lock 包装器）",
    "  最小复现：减少线程数和操作量，定位竞态条件的根本原因",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「死锁检测器」：用等待图（谁持有什么锁、在等什么锁）检测环。
# 2. 实现一个「并发测试框架」：随机化线程启动顺序，反复运行查找竞态条件。
# 3. 用 faulthandler.dump_traceback_later(timeout) 设置超时转储。
# 4. 思考：为什么「锁排序」能消除死锁？如果锁的集合是动态的呢？
