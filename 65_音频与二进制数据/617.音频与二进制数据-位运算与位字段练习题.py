# ===== 第617课：音频与二进制数据-位运算与位字段 =====
# 知识点：
#   - & 取位 / | 置位 / ^ 翻转 / ~ 取反 / << >> 移位；注意 ~ 在 Python 里是无限位补码
#   - 权限位（flags）：一个整数存多个 bool，用 1 << n 定义常量
#   - 位图 bitmap：每 bit 表示一个对象的状态，空间是 bool 列表的 1/8
#   - 位字段打包：把多个小整数塞进一个 int（如 RGB565、音视频头里的标志位）
#   - 常用技巧：x & (x-1) 清最低置位、x & -x 取最低置位、n & 1 判奇偶
#   - 位运算优先级低于比较，表达式里务必加括号
# 依赖：无（标准库）

print("== 基础位运算 ==")
a, b = 0b1100, 0b1010
print(f"  a     = {a:04b}")
print(f"  b     = {b:04b}")
print(f"  a & b = {a & b:04b}  a | b = {a | b:04b}  a ^ b = {a ^ b:04b}")
print(f"  ~a    = {~a & 0xF:04b}（用 & 0xF 截成 4 位看）")
print(f"  a<<2  = {a << 2:06b}  a>>1 = {a >> 1:04b}")

print("\n== 常用位技巧 ==")
for x in (0b101100, 0b100000, 0b1111):
    print(f"  x={x:06b}  x&(x-1)={x & (x - 1):06b}  x&-x={x & -x:06b}  置位数={x.bit_count()}")
print("  判奇偶:", [(n, n & 1 == 0) for n in (2, 3, 8)])
print("  int.bit_length():", [(n, n.bit_length()) for n in (1, 7, 8, 255, 256)])

print("\n== 权限位 flags ==")
READ, WRITE, EXEC, DELETE = (1 << i for i in range(4))
NAMES = {READ: "读", WRITE: "写", EXEC: "执行", DELETE: "删除"}

def describe(flags: int) -> str:
    return "|".join(name for bit, name in NAMES.items() if flags & bit) or "无权限"

user = READ | WRITE
print(f"  user  = {user:04b} -> {describe(user)}")
print(f"  加执行: {describe(user | EXEC)}")
print(f"  去写  : {describe(user & ~WRITE)}")
print(f"  翻转  : {describe(user ^ WRITE)}")
print(f"  有删除: {bool(user & DELETE)}")

print("\n== 位图 bitmap（每 bit 一个席位）==")
class Bitmap:
    def __init__(self, size: int):
        self.size = size
        self.bits = bytearray((size + 7) // 8)

    def set(self, i: int, value: bool = True):
        if not 0 <= i < self.size:
            raise IndexError(i)
        if value:
            self.bits[i >> 3] |= 1 << (i & 7)
        else:
            self.bits[i >> 3] &= ~(1 << (i & 7)) & 0xFF

    def get(self, i: int) -> bool:
        return bool(self.bits[i >> 3] & (1 << (i & 7)))

    def count(self) -> int:
        return sum(byte.bit_count() for byte in self.bits)

bm = Bitmap(40)
for i in (0, 5, 7, 8, 39):
    bm.set(i)
print("  置位索引:", [i for i in range(40) if bm.get(i)])
print(f"  已用 {len(bm.bits)} 字节存 40 个状态；置位数={bm.count()}")
print(f"  若用 bool 列表约需 40 字节，位图省 {40 / len(bm.bits):.0f} 倍")
bm.set(5, False)
print("  取消 5 后:", [i for i in range(40) if bm.get(i)])

print("\n== 位字段打包：RGB565（5+6+5=16 位）==")
def pack_rgb565(r: int, g: int, b: int) -> int:
    return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)

def unpack_rgb565(v: int):
    r = (v >> 11) & 0x1F
    g = (v >> 5) & 0x3F
    b = v & 0x1F
    return (r << 3 | r >> 2, g << 2 | g >> 4, b << 3 | b >> 2)

for color in ((255, 128, 64), (0, 255, 0), (31, 63, 31)):
    packed = pack_rgb565(*color)
    print(f"  {color} -> 0x{packed:04X} ({packed:016b}) -> {unpack_rgb565(packed)}")

print("\n== 位字段：一个字节存 4 个开关 + 一个 4 位音量 ==")
def pack_flags(mute, echo, loop, mono, volume: int) -> int:
    flags = (int(mute) << 3) | (int(echo) << 2) | (int(loop) << 1) | int(mono)
    return (flags << 4) | (volume & 0x0F)

def unpack_flags(v: int):
    return {
        "mute": bool(v & (1 << 7)), "echo": bool(v & (1 << 6)),
        "loop": bool(v & (1 << 5)), "mono": bool(v & (1 << 4)),
        "volume": v & 0x0F,
    }

cfg = pack_flags(mute=False, echo=True, loop=False, mono=True, volume=11)
print(f"  打包: 0x{cfg:02X} = {cfg:08b} -> {unpack_flags(cfg)}")

print("\n== 优先级坑 ==")
x = 0b0100
print("  x & 0b0100 == 0 会被解析成 x & (0b0100 == 0) ->", x & 0b0100 == 0)
print("  正确写法 (x & 0b0100) == 0 ->", (x & 0b0100) == 0)

# ===== 练习题 =====
# 1. 用位运算实现「统计一个 32 位整数里有多少个 1」的三种写法并对比。
# 2. 给 Bitmap 增加 union / intersection 方法（按字节 | / &）。
# 3. 设计一个 16 位音频帧头：3 位版本 + 1 位加密 + 4 位声道 + 8 位采样率索引。
# 4. 思考：位图适合「稠密且取值布尔」的场景，稀疏场景为什么反而不划算？
