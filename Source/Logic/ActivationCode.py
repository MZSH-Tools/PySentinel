"""
离线激活码 生成 / 验证   —— 现已携带 ProductId
"""
from __future__ import annotations
import base64, json, time
from typing import Tuple

from Crypto.PublicKey import RSA
from Crypto.Signature import pss
from Crypto.Hash import SHA256
from Crypto.Random import get_random_bytes

# ========= 替换为你自己的密钥 ========= #
_PRIVATE_KEY_PATH = "private.pem"        # 仅开发机用
_PUBLIC_KEY_PEM = (
    "-----BEGIN PUBLIC KEY-----\n"
    "MIIBIjANBgkq…你的Base64…AQAB\n"
    "-----END PUBLIC KEY-----"
)
# ==================================== #

# ---------- 生成 ---------- #
def Generate(validMinutes: int, productId: str) -> Tuple[str, bytes]:
    """
    返回 (activationCode, seedBytes)
    """
    seed = get_random_bytes(32)
    payload = {
        "ts": int(time.time()) + validMinutes * 60,
        "seed": seed.hex(),
        "prod": productId           # 新增字段
    }
    j = json.dumps(payload, separators=(",", ":")).encode()
    priv = RSA.import_key(open(_PRIVATE_KEY_PATH, "rb").read())
    sig = pss.new(priv).sign(SHA256.new(j))
    code = base64.urlsafe_b64encode(j + sig).decode()
    return code, seed


# ---------- 验证 ---------- #
def Validate(codeStr: str, leeway: int = 60) -> Tuple[bytes, str]:
    """
    成功返回 (seedBytes, productId)
    """
    data = base64.urlsafe_b64decode(codeStr)
    pub = RSA.import_key(_PUBLIC_KEY_PEM.encode())
    sigLen = pub.size_in_bytes()
    payloadBytes, signature = data[:-sigLen], data[-sigLen:]
    pss.new(pub).verify(SHA256.new(payloadBytes), signature)   # 失败抛异常

    payload = json.loads(payloadBytes)
    if time.time() > payload["ts"] + leeway:
        raise ValueError("Activation code expired")
    return bytes.fromhex(payload["seed"]), payload["prod"]
