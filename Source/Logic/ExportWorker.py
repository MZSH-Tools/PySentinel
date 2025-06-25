"""
批量加壳 & 单文件 exe（全自动密钥，公钥写进壳）
"""
import hashlib, shutil, subprocess, sys, tempfile, time, threading
from pathlib import Path
from typing import Callable, List

from Crypto.PublicKey import RSA

from .TargetEntry import TargetEntry
from .EncryptionUtils import EncryptFile, DeriveUserKey
from .ActivationCode import Generate

RUNNER_TEMPLATE = Path("PayloadRunner.py")   # 模板

class ExportWorker(threading.Thread):
    def __init__(self,
                 targets: List[TargetEntry],
                 exportDir: Path,
                 logFunc: Callable[[str], None],
                 finishedCb: Callable[[bool], None]):
        super().__init__(daemon=True)
        self.Targets = targets
        self.ExportDir = exportDir
        self.Log = logFunc
        self.OnFinished = finishedCb
        self.InterruptFlag = False

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

                # 1. 生成 ProductId
                productId = hashlib.sha256(f"{src.stat().st_mtime_ns}{time.time_ns()}".encode()).hexdigest()[:12]

                # 2. 动态密钥对
                rsaKey  = RSA.generate(2048)
                privPem = rsaKey.export_key()
                pubPem  = rsaKey.publickey().export_key()

                # 3. 激活码
                try:
                    activation, seed = Generate(t.Minutes, productId, privPem)
                except Exception as e:
                    self.Log(f"❌ 生成激活码失败：{e}")
                    continue

                # 4. 加密载荷
                encTmp = tmpRoot / "encrypted_payload.dat"
                EncryptFile(src, DeriveUserKey(seed), encTmp)

                # 5. 生成 Runner 源码（注入 ProductId + 公钥）
                runnerTmp = tmpRoot / f"Runner_{productId}.py"
                code = RUNNER_TEMPLATE.read_text(encoding="utf-8")
                code = code.replace("__PRODUCT_ID__", productId)
                code = code.replace("__PUBLIC_KEY__", pubPem.decode())
                runnerTmp.write_text(code, encoding="utf-8")

                # 6. PyInstaller 单文件
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
                self.Log(f"🔧 正在打包 {t.Name} …")
                proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                if proc.returncode != 0:
                    self.Log(f"❌ 打包失败：\n{proc.stdout}")
                    continue

                self.Log(f"✅ 完成 → {outExe}")
                self.Log(f"激活码：{activation}\n")

        finally:
            shutil.rmtree(tmpRoot, ignore_errors=True)

        self.Log("⚠ 导出被用户中断" if interrupted else "全部任务完成")
        self.OnFinished(interrupted)

    def Interrupt(self):
        self.InterruptFlag = True
