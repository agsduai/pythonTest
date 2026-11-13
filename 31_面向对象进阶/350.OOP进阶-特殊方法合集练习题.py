# ===== 第350课：OOP进阶-特殊方法合集 =====
# 知识点：
#   - 双下划线方法 = 与 Python 语法挂钩的“钩子”
#   - __repr__ 调试显示 / __eq__ 相等 / __len__ len() / __getitem__ 下标与 for
#   - __contains__ in 判断 / __call__ 实例像函数一样调用
#   - 实现了 __getitem__ 就自动可迭代、可切片（协议的力量，对照第351课）
class Playlist:

    def __init__(self, name, songs=()):
        self.name = name
        self._songs = list(songs)

    def add(self, song):
        self._songs.append(song)

    def __len__(self):                          # len(pl)
        return len(self._songs)

    def __getitem__(self, index):               # pl[1]、切片、for 遍历
        return self._songs[index]

    def __contains__(self, song):               # song in pl
        return song in self._songs

    def __repr__(self):                         # print(pl) 调试友好
        return f"Playlist({self.name!r}, 共{len(self)}首)"

    def __eq__(self, other):                    # pl == other
        return isinstance(other, Playlist) and self._songs == other._songs


pl = Playlist("通勤歌单", ["晴天", "稻香"])
pl.add("夜曲")
print(pl)
print("len：", len(pl), "| 下标：", pl[1], "| 切片：", pl[:2])
print("in 判断：", "稻香" in pl, "| for：", " / ".join(pl))
print("相等：", pl == Playlist("副本", ["晴天", "稻香", "夜曲"]))


# __call__：实例可以像函数一样被调用
class Greeter:

    def __init__(self, greeting):
        self.greeting = greeting

    def __call__(self, name):
        return f"{self.greeting}，{name}！"


hi = Greeter("你好")
print(hi("小明"), "| callable：", callable(hi))

# 运算符重载一句话：__add__ 支持 +、__lt__ 支持 <（排序）、__enter__/__exit__ 支持 with

# ===== 练习题 =====
# 1. 给 Playlist 加 __add__：pl1 + pl2 合并成新歌单。
# 2. 实现 __lt__，让歌单能按歌曲数 sorted 排序。
# 3. 思考：for 为什么没有 __iter__ 也能遍历了？（__getitem__ 旧协议兜底）
