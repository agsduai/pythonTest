# ===== 第195课：并发编程-多线程基础 =====
# 知识点：
#   - threading.Thread(target=函数, args=(参数,)) 创建线程
#   - start() 启动线程，join() 等待线程结束
#   - 线程两种写法：函数 + Thread；继承 Thread 重写 run()
#   - daemon 守护线程：主程序退出时自动结束
#   - current_thread().name / enumerate() 查看线程信息

import threading
import time


def worker(task_id, duration=0.4):
    name = threading.current_thread().name
    print(f"[{name}] 开始任务 {task_id}")
    time.sleep(duration)
    print(f"[{name}] 完成任务 {task_id}")


# 写法一：函数 + Thread
t1 = threading.Thread(target=worker, args=(1,), name="线程A")
t2 = threading.Thread(
    target=worker, kwargs={"task_id": 2, "duration": 0.2}, name="线程B"
)
t1.start()          # 启动线程（直接调 worker() 只是普通函数调用）
t2.start()
t1.join()           # 主线程在这里等 t1 干完
print("t1 已结束，t2 可能还没跑完\n")


# 写法二：继承 Thread，重写 run()
class DownloadThread(threading.Thread):

    def __init__(self, filename):
        super().__init__()
        self.filename = filename

    def run(self):
        print(f"开始下载 {self.filename}")
        time.sleep(0.3)
        print(f"下载完成 {self.filename}")


DownloadThread("电影.mp4").start()
DownloadThread("剧集.mkv").start()


# 守护线程：主程序退出时被强制结束，适合心跳、监控类任务
daemon = threading.Thread(target=worker, args=(99, 5), daemon=True, name="守护线程")
daemon.start()
time.sleep(0.2)
print("主程序即将结束，守护线程被终止\n")

# 线程信息
time.sleep(0.6)     # 等前面的业务线程跑完，避免输出干扰
print("当前存活的线程：", [t.name for t in threading.enumerate()])
print("线程总数：", threading.active_count())

# ===== 练习题 =====
# 1. 创建 3 个线程分别打印 1~5、6~10、11~15，观察输出顺序是否固定。
# 2. 把 daemon=True 去掉再运行，观察守护线程是否会被等完。
# 3. 用继承 Thread 的方式写一个“计数线程”，run 里每隔 0.1 秒打印一次计数。
# 4. 思考：什么时候需要 join 等线程，什么时候不需要？
