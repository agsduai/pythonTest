# ===== 第1033课：面向对象综合实战-魔术方法str与eq =====
# 知识点：
#   - __str__：print(对象) 时显示的内容，给人看的
#   - __repr__：调试时显示的内容，给开发者看的（终端里直接敲对象名）
#   - __eq__：定义 == 的比较规则；定义后对象可以放进集合判重
#   - __len__ / __getitem__：让自定义对象支持 len() 和下标访问

# 案例一：没有 __str__ 的对象 print 出来很难看
class Point:
    def __init__(self, x, y):
        self.x, self.y = x, y

p = Point(3, 5)
print(f"没定义 __str__：{p}")  # 输出内存地址，毫无信息量

# 案例二：加上 __str__ 和 __repr__
class GoodPoint:
    def __init__(self, x, y):
        self.x, self.y = x, y

    def __str__(self):  # print 时调用
        return f"点({self.x}, {self.y})"

    def __repr__(self):  # 调试/容器里显示时调用
        return f"GoodPoint({self.x}, {self.y})"

g = GoodPoint(3, 5)
print(f"print 输出：{g}")
print(f"调试显示：{g!r}")  # !r 强制用 repr
print(f"容器里：{[GoodPoint(1, 1), GoodPoint(2, 2)]}")  # 列表内用 repr

# 案例三：__eq__ —— 让 == 按内容比较
# 场景：两个会员信息一样就算同一个会员
class Member:
    def __init__(self, name, phone):
        self.name = name
        self.phone = phone

    def __eq__(self, other):
        if not isinstance(other, Member):
            return False
        return self.phone == other.phone  # 手机号相同就算同一人

m1 = Member("小张", "13800138000")
m2 = Member("张三", "13800138000")
print(f"m1 == m2：{m1 == m2}")  # True，不看姓名只看手机号
# 注意：一旦定义 __eq__，对象默认不可哈希，直接放 set 会报 TypeError
try:
    len({m1, m2})
except TypeError:
    print("定义 __eq__ 后不能直接进集合，还要补 __hash__")
class HashMember(Member):
    def __hash__(self):
        return hash(self.phone)

print(f"可哈希去重：{len({HashMember('a', '1'), HashMember('b', '1')})}")  # 1

# 案例四：__len__ 和 __getitem__ —— 对象像列表一样用
class Playlist:
    def __init__(self, songs):
        self.songs = songs

    def __len__(self):  # 支持 len()
        return len(self.songs)

    def __getitem__(self, index):  # 支持 [] 下标
        return self.songs[index]

pl = Playlist(["晴天", "七里香", "稻香"])
print(f"歌单数量：{len(pl)}")      # 调 __len__
print(f"第一首歌：{pl[0]}")        # 调 __getitem__
print(f"切片：{pl[1:]}")           # 切片也自动走 __getitem__

# ===== 练习题 =====
# 1. 给 Book 类（title, price）定义 __str__，print 时输出 "《书名》 定价 xx 元"。
# 2. 给 Money 类（amount）定义 __eq__：金额相等即相等；创建 100 和 100.0 两个实例验证相等。
# 3. 给 TodoList 类定义 __len__ 和 __getitem__，支持 len(todo) 返回条数、todo[0] 取第一条。
