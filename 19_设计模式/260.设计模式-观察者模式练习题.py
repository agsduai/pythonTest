# ===== 第260课：设计模式-观察者模式 =====
# 知识点：
#   - 观察者：一对多依赖 —— 状态变化自动通知所有订阅者
#   - 发布/订阅、事件总线、回调都是它的变体
#   - 解耦：被观察者不需要知道观察者是谁、有多少个
#   - Python 里用“事件名 → 回调列表”的字典就能实现


class EventBus:
    """极简事件总线：订阅 + 发布。"""

    def __init__(self):
        self.subscribers = {}          # 事件名 -> [回调函数]

    def subscribe(self, event, callback):
        self.subscribers.setdefault(event, []).append(callback)

    def publish(self, event, data):
        for callback in self.subscribers.get(event, []):
            callback(data)


bus = EventBus()

# 三个“观察者”各干各的，互不知道对方存在
bus.subscribe("order_paid", lambda d: print(f"发短信：{d['user']} 已支付 {d['amount']} 元"))
bus.subscribe("order_paid", lambda d: print(f"加积分：+{int(d['amount'])} 分"))
bus.subscribe("order_paid", lambda d: print(f"开发票：订单 {d['order_id']}"))


# 稍复杂一点的观察者：写成函数或类都可以
def stock_deduct(data):
    print(f"扣库存：商品 {data['order_id']} 减一")


bus.subscribe("order_paid", stock_deduct)

bus.publish("order_paid", {"user": "小明", "amount": 99, "order_id": "A001"})

print("---")

# 新增观察者：业务方只需 subscribe，发布方一行不改
bus.subscribe("order_paid", lambda d: print(f"发优惠券：给 {d['user']}"))
bus.publish("order_paid", {"user": "小红", "amount": 50, "order_id": "A002"})

# 取消订阅演示
bus.subscribers["order_paid"].remove(stock_deduct)
print("--- 移除库存观察者后再发布（不再扣库存）---")
bus.publish("order_paid", {"user": "小刚", "amount": 10, "order_id": "A003"})

# ===== 练习题 =====
# 1. 新增事件 user_registered（欢迎邮件/初始化积分/发新人券）。
# 2. 给 subscribe 加去重：同一个回调重复订阅时只保留一份。
# 3. 给 publish 加异常隔离：某个观察者出错，不影响其他观察者（提示：try/except）。
# 4. 思考：观察者与第202课“as_completed 收结果”在解耦思想上有什么不同？
