# ===== 第1064课：异常处理进阶-异常在函数间传递 =====
# 知识点：
#   - 函数里抛的异常会沿"调用链"向外传：A 调 B，B 抛错没接住就传到 A
#   - 每一层都可以选择：接住处理 / 记录后再抛 / 完全不管
#   - 在"最合适的一层"处理：底层不知道怎么处理，上层才知道
#   - Traceback 会打印整条调用链，从下往上读就是传递路径

# 案例一：异常沿调用链向上冒泡
def inner():
    raise ValueError("inner 出错了")

def middle():
    inner()  # 不捕获，异常继续往上跑
    print("middle 不会执行到这里")

def outer():
    try:
        middle()
    except ValueError as e:  # 在最上层接住
        print(f"outer 接住：{e}")

outer()

# 案例二：中间层转换异常类型
# 场景：底层报技术错误，中间层翻译成业务异常
class PaymentError(Exception):
    pass

def low_level_pay():
    raise ConnectionError("网络中断")

def business_pay():
    try:
        low_level_pay()
    except ConnectionError as e:
        raise PaymentError(f"支付失败：{e}") from e  # 转换类型并保留原因

try:
    business_pay()
except PaymentError as e:
    print(f"上层处理：{e}")

# 案例三：批量任务 —— 单个失败不影响整体
# 场景：发通知给三个人，一个人号码错误不影响其他人
def send_sms(phone):
    if "x" in phone:
        raise ValueError(f"号码 {phone} 无效")

contacts = ["13800000001", "x138000", "13800000003"]
sent, failed = 0, []
for phone in contacts:
    try:
        send_sms(phone)
        sent += 1
    except ValueError as e:
        failed.append(str(e))
print(f"发送成功 {sent} 条，失败 {len(failed)} 条：{failed}")

# 案例四：默认参数陷阱 —— 错误发生在调用时
# 默认值在定义时求值，而异常发生在函数体执行时
def add_item(item, items=None):
    if items is None:
        items = []  # 正确做法：用 None 占位
    items.append(item)
    return items

print(f"第一次：{add_item('苹果')}")
print(f"第二次：{add_item('牛奶')}")  # 两次结果独立，没有被共享污染

# ===== 练习题 =====
# 1. 写三层调用：layer1() raise ValueError -> layer2() 调 layer1 不捕获 -> layer3() try 捕获并打印，运行验证异常穿透两层。
# 2. 写函数 safe_call(fn, *args)：调用传入的函数并捕获所有 Exception 返回 "ERROR: 类型:信息"，成功返回结果；用 lambda x: 1/x 分别传 2 和 0 测试。
# 3. 批量解析 ["5", "abc", "7"] 每项调用 int()：用 try 在循环里接住并统计成功/失败数，最后打印总成绩和（成功项之和）。
