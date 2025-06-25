"""
批量加壳 & 打包单文件 exe（含 ProductId、激活码）
"""
import hashlib, shutil, subprocess, sys, tempfile, time, threading
from pathlib import Path
from typing import Callable, List

from .TargetEntry import TargetEntry
from .EncryptionUtils import EncryptFile, DeriveUserKey
from .ActivationCode import Generate

# ------------------------------ #
RUNNER_TEMPLATE = Path("PayloadRunner.py")   # 固定模板
# ------------------------------ #

class ExportWorker(threading.Thread):
    def __init__(
            self,
            targets: List[TargetEntry],
            exportDir: Path,
            logFunc: Callable[[str], None],
            finishedCb: Callable[[bool], None],
    ):
        super().__init__(daemon=True)
        self.Targets = targets
        self.ExportDir = exportDir
        self.Log = logFunc
        self.OnFinished = finishedCb
        self.InterruptFlag = False

    # ---------- 主流程 ----------
    def run(self):
        interrupted = False
        tmpRoot = Path(tempfile.mkdtemp(prefix="psentinel_"))
        try:
            for t in self.Targets:
                if self.InterruptFlag:
                    interrupted = True
                    break
                if not t.Path:
                    self.Log(f"⛔ 跳过 {t.Name}（未设置文件）")
                    continue
                src = Path(t.Path)
                if not src.exists():
                    self.Log(f"❌ 找不到文件：{src}")
                    continue

                # 1) 生成 ProductId（12 hex）
                productId = hashlib.sha256(
                    f"{src.stat().st_mtime_ns}{time.time_ns()}".encode()
                ).hexdigest()[:12]

                # 2) 生成激活码 & seed
                try:
                    activation, seed = Generate(t.Minutes, productId)
                except Exception as e:
                    self.Log(f"❌ 生成激活码失败：{e}")
                    continue

                # 3) AES-GCM 加密载荷 -> tmp/encrypted_payload.dat
                encTmp = tmpRoot / "encrypted_payload.dat"
                EncryptFile(src, DeriveUserKey(seed), encTmp)

                # 4) 复制 Runner 模板 & 注入 ProductId
                runnerTmp = tmpRoot / f"Runner_{productId}.py"
                runnerCode = RUNNER_TEMPLATE.read_text(encoding="utf-8")
                runnerCode = runnerCode.replace("__PRODUCT_ID__", productId)
                runnerTmp.write_text(runnerCode, encoding="utf-8")

                # 5) PyInstaller 单文件
                outExe = self.ExportDir / f"{t.Name}.exe"
                cmd = [
                    sys.executable, "-m", "PyInstaller", "-F", str(runnerTmp),
                    "--add-data", f"{encTmp};Assets",
                    "--name", outExe.stem,
                    "--distpath", str(self.ExportDir),
                    "--workpath", str(tmpRoot / "build"),
                    "--specpath", str(tmpRoot / "spec"),
                    "--noconsole"
                ]
                self.Log(f"🔧 PyInstaller {t.Name} …")
                proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                if proc.returncode != 0:
                    self.Log(f"❌ 打包失败：\n{proc.stdout}")
                    continue

                self.Log(f"✅ 完成 → {outExe}")
                self.Log(f"激活码：{activation}\n")

        finally:
            shutil.rmtree(tmpRoot, ignore_errors=True)

        if interrupted:
            self.Log("⚠ 导出被用户中断")
        else:
            self.Log("全部任务完成")
        self.OnFinished(interrupted)

    def Interrupt(self):
        self.InterruptFlag = True
