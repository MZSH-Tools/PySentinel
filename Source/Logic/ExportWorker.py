"""
批量加壳 & 打包单文件 exe（支持打断）
"""
import hashlib, shutil, subprocess, sys, tempfile, time, threading
from pathlib import Path
from typing import Callable, List

from Cryptodome.PublicKey import RSA

from .TargetEntry      import TargetEntry
from .EncryptionUtils  import EncryptFile, DeriveUserKey
from .ActivationCode   import Generate


RUNNER_TEMPLATE = Path("PayloadRunner.py")


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
        self._currentProc: subprocess.Popen | None = None   # 保存子进程

    # ---------- 打断 ----------
    def Interrupt(self):
        self.InterruptFlag = True
        if self._currentProc and self._currentProc.poll() is None:
            try:
                self._currentProc.terminate()
            except Exception:
                pass

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
                    continue
                src = Path(t.Path)
                if not src.exists():
                    self.Log(f"❌ 找不到文件：{src}")
                    continue

                productId = hashlib.sha256(f"{time.time_ns()}_{src}".encode()).hexdigest()[:12]
                rsaKey  = RSA.generate(2048)
                privPem = rsaKey.export_key()
                pubPem  = rsaKey.publickey().export_key()

                try:
                    activation, seed = Generate(t.Minutes, productId, privPem)
                except Exception as e:
                    self.Log(f"❌ 生成激活码失败：{e}")
                    continue

                encTmp = tmpRoot / "encrypted_payload.dat"
                EncryptFile(src, DeriveUserKey(seed), encTmp)

                runnerTmp = tmpRoot / f"Runner_{productId}.py"
                code = RUNNER_TEMPLATE.read_text(encoding="utf-8")
                code = code.replace("__PRODUCT_ID__", productId).replace(
                    "__PUBLIC_KEY__", pubPem.decode()
                )
                runnerTmp.write_text(code, encoding="utf-8")

                outExe = self.ExportDir / f"{t.Name}.exe"
                cmd = [
                    sys.executable, "-m", "PyInstaller", "-F", str(runnerTmp),
                    "--add-data", f"{encTmp};Assets",
                    "--name", outExe.stem,
                    "--distpath", str(self.ExportDir),
                    "--workpath",  str(tmpRoot / "build"),
                    "--specpath",  str(tmpRoot / "spec"),
                    "--noconsole",
                ]
                self.Log(f"🔧 正在打包 {t.Name} …")

                # ----- 改为 Popen -----
                self._currentProc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="ignore",
                )

                # 实时读取输出，支持中断
                for line in self._currentProc.stdout:
                    if self.InterruptFlag:
                        self._currentProc.terminate()
                        break
                self._currentProc.wait()
                if self.InterruptFlag:
                    interrupted = True
                    break
                if self._currentProc.returncode != 0:
                    self.Log("❌ 打包失败")
                    continue

                self.Log(f"✅ 完成 → {outExe}")
                self.Log(f"激活码：{activation}\n")

        finally:
            shutil.rmtree(tmpRoot, ignore_errors=True)
            self._currentProc = None
            self.OnFinished(interrupted)
            if interrupted:
                self.Log("⚠ 导出被用户中断")
            else:
                self.Log("全部任务完成")
