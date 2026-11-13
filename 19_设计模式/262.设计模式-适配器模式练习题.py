# ===== 第262课：设计模式-适配器模式 =====
# 知识点：
#   - 适配器：把“不兼容的接口”包装成调用方期待的样子
#   - 场景：老系统升级、第三方库接口统一、多数据源接入
#   - Python 常用组合（持有旧对象）实现，也可用继承
#   - 收益：调用方代码零改动，旧类也不用改


# ---- 旧系统：接口陈旧 ----
class OldPrinter:

    def print_old(self, text, copies=1):
        return f"[老式打印 x{copies}] {text}"


# ---- 新系统期待的接口 ----
class ModernMachine:

    def print(self, text):
        raise NotImplementedError


def client(machine: ModernMachine, text):
    """调用方只认新接口。"""
    return machine.print(text)


# ---- 适配器：把旧打印机“翻译”成新接口 ----
class PrinterAdapter(ModernMachine):

    def __init__(self, old_printer: OldPrinter):
        self.old = old_printer

    def print(self, text):
        return self.old.print_old(text)          # 内部翻译调用


print(client(PrinterAdapter(OldPrinter()), "期末成绩单"))


# ---- 实战版：统一多个第三方“支付渠道”的接口 ----
class AlipaySDK:                                  # 假想的第三方A：参数名不同
    def pay(self, subject, total_fee):
        return f"支付宝支付成功：{subject} ¥{total_fee}"


class WechatSDK:                                  # 假想的第三方B：方法名不同
    def unified_order(self, body, money_cents):
        return f"微信支付成功：{body} ¥{money_cents / 100}"


class PaymentGateway(ModernMachine):              # 统一网关接口

    def print(self, text):
        raise NotImplementedError


class AlipayAdapter(PaymentGateway):

    def __init__(self):
        self.sdk = AlipaySDK()

    def print(self, text):
        name, amount = text.split("|")
        return self.sdk.pay(name, float(amount))


class WechatAdapter(PaymentGateway):

    def __init__(self):
        self.sdk = WechatSDK()

    def print(self, text):
        name, amount = text.split("|")
        return self.sdk.unified_order(name, int(float(amount) * 100))


for gateway in (AlipayAdapter(), WechatAdapter()):
    print(client(gateway, "Python课程|199"))

# ===== 练习题 =====
# 1. 新增 UnionAdapter（模拟银联），接入同一个 client。
# 2. 给适配器加参数校验：金额为负时抛 ValueError。
# 3. 思考：适配器与第258课工厂结合：create_payment(kind) 返回适配器。
