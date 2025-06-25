from PySide6.QtWidgets import QListWidget, QListWidgetItem
from PySide6.QtCore    import Qt


class SafeDragList(QListWidget):
    """
    只能在本控件内部拖放；目标行永不被覆盖。
    拖放成功后自动调用父窗口 SaveConfig()。
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setDragDropMode(QListWidget.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setDragDropOverwriteMode(False)      # <— 彻底禁用覆盖

    # 保证拖出控件时取消
    def dragLeaveEvent(self, event):
        event.ignore()

    def dropEvent(self, event):
        if event.source() is not self:
            event.ignore()
            return

        # 获取拖拽源 & 目标索引
        srcRow = self.currentRow()
        destRow = self.indexAt(event.position().toPoint()).row()
        if destRow == -1:
            destRow = self.count() - 1

        if destRow != srcRow:
            item = self.takeItem(srcRow)
            self.insertItem(destRow, item)
            self.setCurrentItem(item)

        if hasattr(self.parent(), "SaveConfig"):
            self.parent().SaveConfig()
