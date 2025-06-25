from __future__ import annotations
import sys, time
from pathlib import Path
from typing import List

from PySide6.QtCore import Qt, Slot, QPoint
from PySide6.QtWidgets import (
    QWidget, QListWidget, QListWidgetItem, QPushButton, QLineEdit, QSpinBox,
    QFileDialog, QPlainTextEdit, QFormLayout, QHBoxLayout, QVBoxLayout,
    QSplitter, QLabel, QInputDialog, QMenu, QMessageBox
)

sys.path.append(str(Path(__file__).resolve().parents[2]))

from Source.Logic.TargetEntry import TargetEntry
from Source.Logic.ConfigManager import ConfigManager
from Source.Logic.ExportWorker import ExportWorker


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PySentinel 加壳工具")
        self.ExportWorker: ExportWorker | None = None
        self.InitUi()
        self.LoadConfig()
        self.UpdateExportButtonState()

    # ---------- UI ----------
    def InitUi(self):
        # 左侧列表
        self.TargetList = QListWidget(self)
        self.TargetList.setDragDropMode(QListWidget.InternalMove)
        self.TargetList.setContextMenuPolicy(Qt.CustomContextMenu)
        self.TargetList.customContextMenuRequested.connect(self.ShowContextMenu)
        self.TargetList.itemSelectionChanged.connect(self.OnSelectTarget)
        self.TargetList.itemChanged.connect(self.OnItemRenamed)
        self.TargetList.model().rowsInserted.connect(lambda *_: self.UpdateExportButtonState())
        self.TargetList.model().rowsRemoved.connect(lambda *_: self.UpdateExportButtonState())

        self.BtnAdd = QPushButton("＋ 添加目标", self)
        self.BtnAdd.clicked.connect(self.AddTarget)

        leftLayout = QVBoxLayout()
        leftLayout.addWidget(self.TargetList, 1)
        leftLayout.addWidget(self.BtnAdd)
        leftWidget = QWidget(self)
        leftWidget.setLayout(leftLayout)

        # 右侧配置
        self.LineEditFile = QLineEdit(self)
        self.LineEditFile.setReadOnly(True)
        self.BtnBrowseFile = QPushButton("…", self)
        self.BtnBrowseFile.clicked.connect(self.BrowseFile)

        self.SpinMinutes = QSpinBox(self)
        self.SpinMinutes.setRange(1, 60 * 24)
        self.SpinMinutes.valueChanged.connect(self.OnMinutesChanged)

        form = QFormLayout()
        form.addRow("目标文件：", self.MakeRow(self.LineEditFile, self.BtnBrowseFile))
        form.addRow("激活码有效期（分钟）：", self.SpinMinutes)
        self.RightPanel = QWidget(self)
        self.RightPanel.setLayout(form)

        splitter = QSplitter(Qt.Horizontal, self)
        splitter.addWidget(leftWidget)
        splitter.addWidget(self.RightPanel)
        splitter.setStretchFactor(1, 1)

        # 中层：导出
        self.LineEditExport = QLineEdit(self)
        self.LineEditExport.setReadOnly(True)
        self.LineEditExport.textChanged.connect(self.UpdateExportButtonState)

        self.BtnBrowseExport = QPushButton("…", self)
        self.BtnBrowseExport.clicked.connect(self.BrowseExportDir)

        self.BtnExport = QPushButton("开始导出", self)
        self.BtnExport.clicked.connect(self.OnExportClicked)

        exportRow = self.MakeRow(self.LineEditExport, self.BtnBrowseExport)
        exportLayout = QFormLayout()
        exportLayout.addRow("导出目录：", exportRow)
        btnRow = QHBoxLayout()
        btnRow.addStretch()
        btnRow.addWidget(self.BtnExport)
        btnRow.addStretch()
        exportLayout.addRow(btnRow)
        exportWidget = QWidget(self)
        exportWidget.setLayout(exportLayout)

        # 底层：日志
        self.TextLog = QPlainTextEdit(self)
        self.TextLog.setReadOnly(True)

        vbox = QVBoxLayout(self)
        vbox.addWidget(splitter, 3)
        vbox.addWidget(exportWidget)
        vbox.addWidget(QLabel("日志：", self))
        vbox.addWidget(self.TextLog, 1)

        self.EnableRightPanel(False)   # ← 初始化禁用右侧控件

    # ---------- 列表辅助 ----------
    def MakeRow(self, *widgets):
        h = QHBoxLayout()
        for w in widgets:
            h.addWidget(w, 1 if isinstance(w, QLineEdit) else 0)
        container = QWidget(self)
        container.setLayout(h)
        return container

    # ---------- 目标列表 ----------
    @Slot()
    def AddTarget(self):
        name, ok = QInputDialog.getText(self, "新建目标", "名称：")
        if ok and name:
            item = QListWidgetItem(name, self.TargetList)
            item.setData(Qt.UserRole, TargetEntry(name))
            item.setFlags(item.flags() | Qt.ItemIsEditable | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled)
            self.TargetList.setCurrentItem(item)

    def OnItemRenamed(self, item: QListWidgetItem):
        entry: TargetEntry = item.data(Qt.UserRole)
        entry.Name = item.text()
        self.UpdateExportButtonState()

    def ShowContextMenu(self, pos: QPoint):
        item = self.TargetList.itemAt(pos)
        if not item:
            return
        menu = QMenu(self)
        actRename = menu.addAction("重命名")
        actDelete = menu.addAction("删除")
        action = menu.exec(self.TargetList.mapToGlobal(pos))
        if action == actRename:
            self.TargetList.editItem(item)
        elif action == actDelete:
            self.TargetList.takeItem(self.TargetList.row(item))
            self.EnableRightPanel(False)
            self.ClearRightPanel()
            self.UpdateExportButtonState()

    def OnSelectTarget(self):
        item = self.TargetList.currentItem()
        if not item:
            self.EnableRightPanel(False)
            self.ClearRightPanel()
            return
        entry: TargetEntry = item.data(Qt.UserRole)
        self.LineEditFile.setText(entry.Path)
        self.SpinMinutes.setValue(entry.Minutes)
        self.EnableRightPanel(True)

    # ---------- 右侧字段 ----------
    @Slot()
    def BrowseFile(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择要加壳的文件")
        if path:
            self.LineEditFile.setText(path)
            self.UpdateEntry("Path", path)

    @Slot(int)
    def OnMinutesChanged(self, minutes: int):
        self.UpdateEntry("Minutes", minutes)

    def UpdateEntry(self, field: str, value):
        item = self.TargetList.currentItem()
        if item:
            entry: TargetEntry = item.data(Qt.UserRole)
            setattr(entry, field, value)

    # ---------- 导出 ----------
    @Slot()
    def BrowseExportDir(self):
        path = QFileDialog.getExistingDirectory(self, "选择导出目录")
        if path:
            self.LineEditExport.setText(path)
            self.Log(f"导出目录设置为：{path}")

    def UpdateExportButtonState(self):
        if self.ExportWorker:            # 导出进行中
            self.BtnExport.setEnabled(True)
            return
        hasTargets = self.TargetList.count() > 0
        hasExport  = bool(self.LineEditExport.text().strip())
        self.BtnExport.setEnabled(hasTargets and hasExport)

    @Slot()
    def OnExportClicked(self):
        if self.ExportWorker:            # 打断导出
            self.ExportWorker.Interrupt()
            return
        exportDir = self.LineEditExport.text().strip()
        targets   = [self.TargetList.item(i).data(Qt.UserRole)
                     for i in range(self.TargetList.count())]
        self.BtnExport.setText("打断导出")
        self.ExportWorker = ExportWorker(targets, Path(exportDir), self.Log, self.ExportFinished)
        self.ExportWorker.start()

    def ExportFinished(self, interrupted: bool):
        self.BtnExport.setText("开始导出")
        self.ExportWorker = None
        self.UpdateExportButtonState()

    # ---------- 工具 ----------
    def EnableRightPanel(self, enabled: bool):
        """统一启用/禁用右侧所有输入控件"""
        for w in (self.LineEditFile, self.BtnBrowseFile, self.SpinMinutes):
            w.setEnabled(enabled)

    def ClearRightPanel(self):
        self.LineEditFile.clear()
        self.SpinMinutes.setValue(10)

    # ---------- 日志 ----------
    def Log(self, msg: str):
        self.TextLog.appendPlainText(msg)
        self.TextLog.verticalScrollBar().setValue(
            self.TextLog.verticalScrollBar().maximum())

    # ---------- 配置 ----------
    def LoadConfig(self):
        cfg = ConfigManager.Load()
        for t in cfg["targets"]:
            entry = TargetEntry.FromDict(t)
            item  = QListWidgetItem(entry.Name, self.TargetList)
            item.setData(Qt.UserRole, entry)
            item.setFlags(item.flags() | Qt.ItemIsEditable | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled)
        self.LineEditExport.setText(cfg.get("exportDir", ""))

    def SaveConfig(self):
        targets = [self.TargetList.item(i).data(Qt.UserRole)
                   for i in range(self.TargetList.count())]
        ConfigManager.Save(targets, self.LineEditExport.text().strip())

    def closeEvent(self, event):
        self.SaveConfig()
        super().closeEvent(event)
