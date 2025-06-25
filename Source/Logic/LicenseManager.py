"""
首次激活生成 license.json
后续启动校验并取回 UserKey
"""
from __future__ import annotations
import base64, json, time
from pathlib import Path
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.Random import get_random_bytes

from .Fingerprint import GetFingerprint
from .EncryptionUtils import DeriveUserKey


_LIC_DIR = Path.home() / ".PySentinel"
_LIC_PATH = _LIC_DIR / "license.json"
_AES_NONCE_LEN = 16   # EAX 16-byte Nonce


def _AesEncrypt(data: bytes, key16: bytes) -> str:
    cipher = AES.new(key16, AES.MODE_EAX, nonce=get_random_bytes(_AES_NONCE_LEN))
    ct, tag = cipher.encrypt_and_digest(data)
    return base64.b64encode(cipher.nonce + tag + ct).decode()


def _AesDecrypt(b64: str, key16: bytes) -> bytes:
    blob = base64.b64decode(b64)
    nonce, tag, ct = blob[:_AES_NONCE_LEN], blob[_AES_NONCE_LEN:_AES_NONCE_LEN + 16], blob[_AES_NONCE_LEN + 16:]
    cipher = AES.new(key16, AES.MODE_EAX, nonce=nonce)
    return cipher.decrypt_and_verify(ct, tag)


# ---------- Public API ----------
def CreateLicense(seed: bytes) -> None:
    fp = GetFingerprint()
    key = SHA256.new(fp.encode()).digest()[:16]          # 128-bit key
    encSeed = _AesEncrypt(seed, key)

    _LIC_DIR.mkdir(exist_ok=True, parents=True)
    data = {
        "fp": fp,
        "ek": encSeed,
        "first_activated": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    _LIC_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def VerifyAndGetKey() -> bytes:
    data = json.loads(_LIC_PATH.read_text(encoding="utf-8"))
    fpSaved = data["fp"]
    fpNow = GetFingerprint()
    if fpSaved != fpNow:
        raise RuntimeError("Fingerprint mismatch – license copied to another machine")

    key = SHA256.new(fpNow.encode()).digest()[:16]
    seed = _AesDecrypt(data["ek"], key)
    return DeriveUserKey(seed)          # ← 供解密载荷使用
