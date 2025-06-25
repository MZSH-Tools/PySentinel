"""
运行加壳应用的壳入口
用法：pyinstaller -F PayloadRunner.py --add-data "Assets/encrypted_payload.dat;Assets"
"""
import base64, os, shutil, subprocess, sys, tempfile, traceback
from pathlib import Path

from Source.Logic.LicenseManager import VerifyAndGetKey, CreateLicense
from Source.Logic.ActivationCode import Validate
from Source.Logic.EncryptionUtils import DecryptBytes
from Source.Logic.Fingerprint import GetFingerprint

_ASSETS_DIR = Path(__file__).resolve().parent / "Assets"
_PAYLOAD_PATH = _ASSETS_DIR / "encrypted_payload.dat"


def _InputActivationLoop() -> bytes:
    """循环要求用户输入激活码，直至合法"""
    while True:
        try:
            code = input("请输入激活码：").strip()
            seed = Validate(code)
            CreateLicense(seed)
            print("✓ 激活成功，已生成本机 license")
            return seed
        except Exception as exc:
            print(f"× 激活码无效：{exc}")


def main():
    try:
        # 1) 取 UserKey（优先从 license.json）
        try:
            userKey = VerifyAndGetKey()
        except FileNotFoundError:
            print("首次启动，请输入激活码 …")
            seed = _InputActivationLoop()
            userKey = VerifyAndGetKey()   # 刚写好的 license
        except Exception as exc:
            print(f"License 校验失败：{exc}")
            sys.exit(1)

        # 2) 解密载荷
        enc = _PAYLOAD_PATH.read_bytes()
        payload = DecryptBytes(enc, userKey)

        # 3) 写入临时文件并运行
        tmpDir = Path(tempfile.mkdtemp())
        outFile = tmpDir / "payload.exe"   # 无论原始扩展名，按需自行判断
        outFile.write_bytes(payload)
        print(f"→ 已解密到 {outFile}")

        if os.name == "nt" and outFile.suffix.lower() == ".exe":
            subprocess.run([str(outFile)], check=False)
        else:
            # 作为 Python 脚本执行
            exec(payload, {"__name__": "__main__"})
    except Exception:
        traceback.print_exc()
        input("Press Enter to exit …")


if __name__ == "__main__":
    main()
