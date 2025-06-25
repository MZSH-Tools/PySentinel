"""
离线激活码 生成 / 验证
- Generate(...) 现在接受 bytes 私钥 (privPem)
- _PUBLIC_KEY_PEM 由 Builder 注入
"""
from __future__ import annotations
import base64, json, time
from typing import Tuple

from Crypto.PublicKey import RSA
from Crypto.Signature import pss
from Crypto.Hash import SHA256
from Crypto.Random import get_random_bytes

_PUBLIC_KEY_PEM = "__PUBLIC_KEY__"    # ← Builder 会替换

# ---------- 生成 ----------
def Generate(validMinutes: int, productId: str, privPem: bytes) -> Tuple[str, bytes]:
    """
    返回 (activationCode, seedBytes)
    """
    seed = get_random_bytes(32)
    payload = {
        "ts": int(time.time()) + validMinutes * 60,
        "seed": seed.hex(),
        "prod": productId
    }
    j = json.dumps(payload, separators=(",", ":")).encode()
    priv = RSA.import_key(privPem)
    sig  = pss.new(priv).sign(SHA256.new(j))
    code = base64.urlsafe_b64encode(j + sig).decode()
    return code, seed

# ---------- 验证 ----------
def Validate(codeStr: str, leeway: int = 60) -> Tuple[bytes, str]:
    """
    成功返回 (seedBytes, productId)
    """
    data = base64.urlsafe_b64decode(codeStr)
    pub  = RSA.import_key(_PUBLIC_KEY_PEM.encode())
    sigLen = pub.size_in_bytes()
    payloadBytes, signature = data[:-sigLen], data[-sigLen:]
    pss.new(pub).verify(SHA256.new(payloadBytes), signature)

    payload = json.loads(payloadBytes)
    if time.time() > payload["ts"] + leeway:
        raise ValueError("Activation code expired")
    return bytes.fromhex(payload["seed"]), payload["prod"]
