import threading, time
from pathlib import Path
from typing import Callable, List
from .TargetEntry import TargetEntry

class ExportWorker(threading.Thread):
    """
    模拟“加壳 + 生成激活码”流程
    日志通过回调 onLog 输出；完成/中断时通过 onFinished 通知
    """
    def __init__(
            self,
            targets: List[TargetEntry],
            exportDir: Path,
            onLog: Callable[[str], None],
            onFinished: Callable[[bool], None],
    ):
        super().__init__(daemon=True)
        self.Targets = targets
        self.ExportDir = exportDir
        self.OnLog = onLog
        self.OnFinished = onFinished
        self.InterruptFlag = False

    def run(self):
        interrupted = False
        for t in self.Targets:
            if self.InterruptFlag:
                interrupted = True
                break
            self.OnLog(f"开始处理：{t.Name}")
            time.sleep(1.0)  # TODO: 替换为真实加壳
            outFile = self.ExportDir / f"{Path(t.Path).stem}_wrapped.dat"
            try:
                outFile.write_text("ENCRYPTED_DATA")
            except Exception as exc:
                self.OnLog(f"❌ 写入失败：{exc}")
                continue
            activation = f"ACTIVATION_{int(time.time())}"
            self.OnLog(f"✅ 完成 → {outFile}")
            self.OnLog(f"激活码：{activation}")
        if interrupted:
            self.OnLog("⚠ 已被用户中断")
        else:
            self.OnLog("全部任务完成")
        self.OnFinished(interrupted)

    def Interrupt(self):
        self.InterruptFlag = True
