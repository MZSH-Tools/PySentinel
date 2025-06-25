"""
真正加壳工作线程
"""
import threading
from pathlib import Path
from typing import Callable, List

from Crypto.Hash import SHA256

from .TargetEntry import TargetEntry
from .EncryptionUtils import DeriveUserKey, EncryptFile
from .ActivationCode import Generate


class ExportWorker(threading.Thread):
    def __init__(
            self,
            targets: List[TargetEntry],
            exportDir: Path,
            logFunc: Callable[[str], None],
            finishedCallback: Callable[[bool], None],
    ):
        super().__init__(daemon=True)
        self.Targets = targets
        self.ExportDir = exportDir
        self.Log = logFunc
        self.OnFinished = finishedCallback
        self.InterruptFlag = False

    def run(self):
        interrupted = False
        for t in self.Targets:
            if self.InterruptFlag:
                interrupted = True
                break
            if not t.Path:
                self.Log(f"⛔ 跳过 {t.Name}（未选择文件）")
                continue

            srcPath = Path(t.Path)
            if not srcPath.exists():
                self.Log(f"❌ 找不到文件：{srcPath}")
                continue

            self.Log(f"开始加壳：{t.Name}")
            # 1. 生成激活码 (含随机 seed)
            try:
                activationCode, seed = Generate(t.Minutes)
            except Exception as exc:
                self.Log(f"❌ 生成激活码失败：{exc}")
                continue

            # 2. 推导 UserKey 并加密
            userKey = DeriveUserKey(seed)               # 目前仅 seed，未加 Fingerprint
            outFile = self.ExportDir / f"{srcPath.stem}_encrypted.dat"
            try:
                EncryptFile(srcPath, userKey, outFile)
            except Exception as exc:
                self.Log(f"❌ 加密失败：{exc}")
                continue

            self.Log(f"✅ 完成 → {outFile}")
            self.Log(f"激活码：{activationCode}\n")

        if interrupted:
            self.Log("⚠ 导出被用户中断")
        else:
            self.Log("全部任务完成")
        self.OnFinished(interrupted)

    def Interrupt(self):
        self.InterruptFlag = True
