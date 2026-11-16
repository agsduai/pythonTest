# ===== 第390课：设计模式进阶-命令模式 =====
# 知识点：
#   - 命令：把“一次操作”封装成对象，调用者不需要知道具体怎么执行
#   - 每个命令实现 execute() / undo()，天然支持撤销/重做
#   - 撤销栈 + 重做栈：新命令入撤销栈，撤销时互换，重做再换回来
#   - 与第260课观察者、第261课模板方法的区别：命令关注“操作本身可存档”
from abc import ABC, abstractmethod


class Command(ABC):

    @abstractmethod
    def execute(self): ...

    @abstractmethod
    def undo(self): ...

    def __repr__(self):
        return self.__class__.__name__


class TextEditor:

    def __init__(self):
        self.text = ""

    def __str__(self):
        return repr(self.text)


class InsertCommand(Command):

    def __init__(self, editor: TextEditor, pos: int, content: str):
        self.editor, self.pos, self.content = editor, pos, content

    def execute(self):
        e = self.editor
        e.text = e.text[:self.pos] + self.content + e.text[self.pos:]

    def undo(self):
        e = self.editor
        e.text = e.text[:self.pos] + e.text[self.pos + len(self.content):]


class DeleteCommand(Command):

    def __init__(self, editor: TextEditor, pos: int, length: int):
        self.editor, self.pos, self.length = editor, pos, length
        self.deleted = ""                 # 执行时保存被删内容，撤销要放回去

    def execute(self):
        e = self.editor
        self.deleted = e.text[self.pos:self.pos + self.length]
        e.text = e.text[:self.pos] + e.text[self.pos + self.length:]

    def undo(self):
        e = self.editor
        e.text = e.text[:self.pos] + self.deleted + e.text[self.pos:]


class CommandManager:

    def __init__(self):
        self.undo_stack: list[Command] = []
        self.redo_stack: list[Command] = []

    def execute(self, cmd: Command):
        cmd.execute()
        self.undo_stack.append(cmd)
        self.redo_stack.clear()          # 新操作让“重做线”失效
        print(f"  执行 {cmd!r} → {self._editor_text(cmd)}")

    def undo(self):
        if not self.undo_stack:
            print("  没有可撤销的操作")
            return
        cmd = self.undo_stack.pop()
        cmd.undo()
        self.redo_stack.append(cmd)
        print(f"  撤销 {cmd!r} → {self._editor_text(cmd)}")

    def redo(self):
        if not self.redo_stack:
            print("  没有可重做的操作")
            return
        cmd = self.redo_stack.pop()
        cmd.execute()
        self.undo_stack.append(cmd)
        print(f"  重做 {cmd!r} → {self._editor_text(cmd)}")

    @staticmethod
    def _editor_text(cmd: Command):
        return getattr(cmd.editor, "text", "")


editor = TextEditor()
manager = CommandManager()

print("== 编辑序列 ==")
manager.execute(InsertCommand(editor, 0, "你好"))
manager.execute(InsertCommand(editor, 2, "，世界"))
manager.execute(InsertCommand(editor, 5, "！"))
print("当前文本：", editor)

print("\n== 撤销三次 ==")
manager.undo()
manager.undo()
manager.undo()

print("\n== 重做两次 ==")
manager.redo()
manager.redo()

print("\n== 删除 + 撤销 ==")
manager.execute(DeleteCommand(editor, 0, 2))
manager.undo()
print("最终文本：", editor)
print("撤销栈：", manager.undo_stack)
print("重做栈：", manager.redo_stack)

# ===== 练习题 =====
# 1. 实现 ReplaceCommand（把 pos 起的一段替换成新内容），支持撤销。
# 2. 给 CommandManager 加批量撤销（一次撤 3 步）。
# 3. 思考：命令模式与“直接调用函数”相比，多出来的价值是什么？
