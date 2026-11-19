# ===== 第1041课：代码风格与最佳实践-常量管理与魔法数字 =====
# 知识点：
#   - 魔法数字：代码里突然出现的裸数字，没人知道它为什么是 8
#   - 修法：提出来命名为全大写常量，写在模块顶部
#   - 常量分组注释：配送类、会员类各归各，方便查找
#   - 枚举值用命名常量：STATUS_PAID = "paid" 防止拼错字符串

# 案例一：魔法数字的痛 —— 修改时漏改一处就出 bug
# 烂：8、30 散落各处，改运费规则要全文搜索
# weight > 10 是什么意思？30 是什么？全靠猜
def fee_bad(weight, is_vip):
    f = 8 if weight <= 1 else 8 + (weight - 1) * 2
    if weight > 10:
        f = 30
    return f * 0.9 if is_vip else f

# 好：常量集中定义，改一处全生效
BASE_FEE = 8          # 首公斤基础运费
PER_KG_FEE = 2        # 续重每公斤加收
HEAVY_LIMIT_KG = 10   # 超重判定线（公斤）
HEAVY_FEE = 30        # 超重一口价
VIP_DISCOUNT = 0.9    # VIP 统一折扣

def fee_good(weight, is_vip):
    if weight > HEAVY_LIMIT_KG:
        fee = HEAVY_FEE
    elif weight > 1:
        fee = BASE_FEE + (weight - 1) * PER_KG_FEE
    else:
        fee = BASE_FEE
    return fee * VIP_DISCOUNT if is_vip else fee

print(f"对比：{fee_bad(12, False)} / {fee_good(12, False)}")

# 案例二：状态字符串常量 —— 防止拼写错误
# 烂：到处写 "paid"，哪天拼成 "paid " 或 "Paid" 就查不出来
# 好：定义一次，到处引用
STATUS_PENDING = "pending"
STATUS_PAID = "paid"
STATUS_SHIPPED = "shipped"

order = {"id": "A001", "status": STATUS_PAID}
if order["status"] == STATUS_PAID:
    print(f"订单 {order['id']} 已支付，可以发货")
print(f"合法状态：{STATUS_PENDING} / {STATUS_PAID} / {STATUS_SHIPPED}")

# 案例三：分组注释管理常量
# ---------- 会员等级 ----------
LEVEL_NORMAL = 0
LEVEL_VIP = 1
LEVEL_SVIP = 2
LEVEL_NAMES = {LEVEL_NORMAL: "普通会员", LEVEL_VIP: "VIP", LEVEL_SVIP: "超级VIP"}

# ---------- 系统限制 ----------
MAX_LOGIN_RETRY = 3   # 登录最多重试次数
MAX_CART_ITEMS = 50   # 购物车上限

def level_name(code):
    return LEVEL_NAMES.get(code, "未知等级")

print(f"等级 1：{level_name(LEVEL_VIP)}")

# 案例四：带单位/含义的后缀命名
# 光叫 timeout 没人说得清单位；后缀点明单位减少误会
TIMEOUT_SECONDS = 30
RETRY_INTERVAL_MS = 500
PAGE_SIZE = 20        # 每页条数（条数不用带单位）
print(f"超时 {TIMEOUT_SECONDS} 秒，重试间隔 {RETRY_INTERVAL_MS} 毫秒")

# ===== 练习题 =====
# 1. 把含魔法数字的折扣函数（score>=90 -> "A"、>=80 -> "B"、>=60 -> "C"）改为常量版本，常量全大写并带注释。
# 2. 定义订单状态常量组（待支付/已支付/已取消），写函数 status_text(code) 返回中文，用常量传入测试。
# 3. 找出这段代码里的魔法数字并重构：if age > 18 and score >= 60: print("成年且及格")（把 18、60 提为常量）。
