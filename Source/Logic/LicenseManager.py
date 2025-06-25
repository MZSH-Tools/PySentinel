"""
按 ProductId 管理独立 license
"""
from __future__ import annotations
import base64, json, time
from pathlib import Path
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.Random import get_random_bytes

from .Fingerprint import GetFingerprint
from .EncryptionUtils import DeriveUserKey

_LIC_ROOT = Path.home() / ".PySentinel" / "licenses"
_NONCE_LEN = 16   # EAX

# ---------- 内部工具 ---------- #
def _LicPath(pid: str) -> Path:
    return _LIC_ROOT / f"{pid}.json"


def _Enc(data: bytes, key16: bytes) -> str:
    cipher = AES.new(key16, AES.MODE_EAX, nonce=get_random_bytes(_NONCE_LEN))
    ct, tag = cipher.encrypt_and_digest(data)
    return base64.b64encode(cipher.nonce + tag + ct).decode()


def _Dec(b64: str, key16: bytes) -> bytes:
    blob = base64.b64decode(b64)
    nonce, tag, ct = blob[:_NONCE_LEN], blob[_NONCE_LEN:_NONCE_LEN+16], blob[_NONCE_LEN+16:]
    cipher = AES.new(key16, AES.MODE_EAX, nonce=nonce)
    return cipher.decrypt_and_verify(ct, tag)

# ---------- Public API ---------- #
def CreateLicense(seed: bytes, productId: str) -> None:
    fp = GetFingerprint()
    key16 = SHA256.new(fp.encode()).digest()[:16]
    ek = _Enc(seed, key16)

    _LIC_ROOT.mkdir(parents=True, exist_ok=True)
    data = {
        "fp": fp,
        "ek": ek,
        "first_activated": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    _LicPath(productId).write_text(json.dumps(data, indent=2), encoding="utf-8")


def VerifyAndGetKey(productId: str) -> bytes:
    licFile = _LicPath(productId)
    data = json.loads(licFile.read_text(encoding="utf-8"))
    if data["fp"] != GetFingerprint():
        raise RuntimeError("Fingerprint mismatch; license copied to another machine")
    key16 = SHA256.new(data["fp"].encode()).digest()[:16]
    seed = _Dec(data["ek"], key16)
    return DeriveUserKey(seed)
