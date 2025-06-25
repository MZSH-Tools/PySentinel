"""
用户侧可执行文件 —— 单文件壳

⚠ Builder 会把字符串 "__PRODUCT_ID__" 替换成真实 ProductId
"""
import base64, importlib.resources, os, subprocess, sys, tempfile, traceback
from pathlib import Path

from Source.Logic.LicenseManager import VerifyAndGetKey, CreateLicense
from Source.Logic.ActivationCode import Validate
from Source.Logic.EncryptionUtils import DecryptBytes

PRODUCT_ID = "__PRODUCT_ID__"     # ← Builder 覆盖

def _InputLoop() -> bytes:
    while True:
        try:
            code = input("请输入激活码：").strip()
            seed, prod = Validate(code)
            if prod != PRODUCT_ID:
                print("× 激活码不匹配此软件")
                continue
            CreateLicense(seed, PRODUCT_ID)
            print("✓ 激活成功")
            return seed
        except Exception as e:
            print(f"× {e}")

def main():
    try:
        try:
            userKey = VerifyAndGetKey(PRODUCT_ID)
        except FileNotFoundError:
            seed = _InputLoop()
            userKey = VerifyAndGetKey(PRODUCT_ID)
        # 读取内嵌 encrypted_payload.dat
        payloadData = importlib.resources.read_binary(__package__ or "Assets", "encrypted_payload.dat")
        code = DecryptBytes(payloadData, userKey)

        tmp = Path(tempfile.mkdtemp()) / "payload.exe"
        tmp.write_bytes(code)
        subprocess.run([str(tmp)], check=False)
    except Exception:
        traceback.print_exc()
        input("Press Enter to exit …")

if __name__ == "__main__":
    main()
