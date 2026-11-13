# ===== 第373课：测试进阶-综合案例-订单服务测试 =====
# 知识点：
#   - 综合运用：Mock 单元测试（368-370）+ 集成测试（372）+ 异常路径全覆盖
#   - 被测：OrderService 依赖“数据库”和“支付网关”
#   - 单元测试：两个依赖全 mock，只测业务规则
#   - 集成测试：真 sqlite + 假网关，走通完整流程
import sqlite3
import unittest
from unittest.mock import Mock


class PaymentError(Exception): ...
class OutOfStock(PaymentError): ...
class AlreadyPaid(PaymentError): ...


class OrderService:
    """业务规则：有库存、未支付过、网关扣款成功，才算支付成功。"""

    def __init__(self, db, payment_gateway):
        self.db, self.gateway = db, payment_gateway

    def pay(self, order_id, amount, stock=1):
        if stock <= 0:
            raise OutOfStock("库存不足")
        if self.db.get_paid(order_id):
            raise AlreadyPaid("重复支付")
        if not self.gateway.charge(amount):
            raise PaymentError("支付失败")
        self.db.mark_paid(order_id)
        return "支付成功"


# ---------- 单元测试：依赖全 mock，毫秒级 ----------
class TestOrderServiceUnit(unittest.TestCase):

    def setUp(self):
        self.db = Mock()
        self.db.get_paid.return_value = False
        self.gateway = Mock()
        self.gateway.charge.return_value = True
        self.svc = OrderService(self.db, self.gateway)

    def test_success_marks_paid(self):
        self.assertEqual(self.svc.pay("A1", 99), "支付成功")
        self.db.mark_paid.assert_called_once_with("A1")     # 关键协作被验证

    def test_out_of_stock_short_circuits(self):
        with self.assertRaises(OutOfStock):
            self.svc.pay("A1", 99, stock=0)
        self.gateway.charge.assert_not_called()             # 没库存不该扣款
        self.db.mark_paid.assert_not_called()

    def test_duplicate_payment(self):
        self.db.get_paid.return_value = True
        with self.assertRaises(AlreadyPaid):
            self.svc.pay("A1", 99)

    def test_gateway_failure(self):
        self.gateway.charge.return_value = False
        with self.assertRaises(PaymentError):
            self.svc.pay("A1", 99)
        self.db.mark_paid.assert_not_called()               # 失败不落库


# ---------- 集成测试：真 sqlite + 假网关，走通全流程 ----------
class FakeGateway:
    def charge(self, amount):
        return amount > 0


class TestOrderServiceIntegration(unittest.TestCase):

    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.execute("CREATE TABLE orders (order_id TEXT PRIMARY KEY, paid INT DEFAULT 0)")
        self.conn.commit()

        class SqliteDB:
            def get_paid(self, oid):
                row = self.conn.execute(
                    "SELECT paid FROM orders WHERE order_id = ?", (oid,)
                ).fetchone()
                return bool(row and row[0])

            def mark_paid(self, oid):
                self.conn.execute(
                    "INSERT INTO orders (order_id, paid) VALUES (?, 1) "
                    "ON CONFLICT(order_id) DO UPDATE SET paid = 1", (oid,))
                self.conn.commit()

        db = SqliteDB()
        db.conn = self.conn                                  # 注入连接
        self.svc = OrderService(db, FakeGateway())

    def tearDown(self):
        self.conn.close()

    def test_full_flow_and_duplicate(self):
        self.assertEqual(self.svc.pay("A1", 99), "支付成功")
        with self.assertRaises(AlreadyPaid):                 # 再付一次被拦
            self.svc.pay("A1", 99)

    def test_invalid_amount(self):
        with self.assertRaises(PaymentError):
            self.svc.pay("A2", -1)


if __name__ == "__main__":
    unittest.main(verbosity=2)

# ===== 练习题 =====
# 1. 补一个单元测试：库存充足但网关抛异常，验证异常原样上抛。
# 2. 给集成测试加“支付前库存检查”（真实表 + 字段）。
# 3. 思考：单元测试与集成测试各抓住了哪类 bug？举一个对方抓不到的例子。
