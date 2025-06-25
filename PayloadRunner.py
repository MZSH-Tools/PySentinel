"""
终端用户执行壳  (单文件)
__PRODUCT_ID__  和  __PUBLIC_KEY__  均由 Builder 替换
"""
import base64, importlib.resources, subprocess, tempfile, traceback
from pathlib import Path

from Source.Logic import ActivationCode  # 动态覆盖其公钥
from Source.Logic.LicenseManager  import VerifyAndGetKey, CreateLicense
from Source.Logic.EncryptionUtils import DecryptBytes

PRODUCT_ID      = "__PRODUCT_ID__"
PUBLIC_KEY_PEM  = """__PUBLIC_KEY__"""

# 覆盖 ActivationCode 中的公钥
ActivationCode._PUBLIC_KEY_PEM = PUBLIC_KEY_PEM

def _InputLoop():
    while True:
        try:
            code = input("请输入激活码：").strip()
            seed, prod = ActivationCode.Validate(code)
            if prod != PRODUCT_ID:
                print("× 激活码不匹配此软件")
                continue
            CreateLicense(seed, PRODUCT_ID)
            print("✓ 激活成功")
            return
        except Exception as e:
            print(f"× {e}")

def main():
    try:
        try:
            userKey = VerifyAndGetKey(PRODUCT_ID)
        except FileNotFoundError:
            _InputLoop()
            userKey = VerifyAndGetKey(PRODUCT_ID)

        data = importlib.resources.read_binary(__package__ or "Assets", "encrypted_payload.dat")
        payload = DecryptBytes(data, userKey)

        tmpExe = Path(tempfile.mkdtemp()) / "payload.exe"
        tmpExe.write_bytes(payload)
        subprocess.run([str(tmpExe)], check=False)

    except Exception:
        traceback.print_exc()
        input("Press Enter to exit …")

if __name__ == "__main__":
    main()
