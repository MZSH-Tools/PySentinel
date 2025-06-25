"""
离线激活码 生成 / 验证
Generate() 仅在开发机用到
Validate() 未来运行时可调用
"""
import base64, json, time
from pathlib import Path
from typing import Tuple

from Crypto.PublicKey import RSA
from Crypto.Signature import pss
from Crypto.Hash import SHA256
from Crypto.Random import get_random_bytes

# ==== 路径与公钥 ====  (自行修改)
_PRIVATE_KEY_PATH = Path("private.pem")      # 开发机私钥
_PUBLIC_KEY_PEM = (                          # 硬编码公钥
    "-----BEGIN PUBLIC KEY-----\n"
    "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAwvOu5JPu...\n"
    "-----END PUBLIC KEY-----"
)

# === 生成 ===
def Generate(validMinutes: int) -> Tuple[str, bytes]:
    """
    返回 (activationCode, seedBytes)
    """
    seed = get_random_bytes(32)
    payload = {
        "ts": int(time.time()) + validMinutes * 60,
        "seed": seed.hex()
    }
    payloadBytes = json.dumps(payload, separators=(",", ":")).encode()

    privKey = RSA.import_key(_PRIVATE_KEY_PATH.read_bytes())
    signature = pss.new(privKey).sign(SHA256.new(payloadBytes))

    raw = payloadBytes + signature
    code = base64.urlsafe_b64encode(raw).decode()
    return code, seed


# === 验证（运行时用）===
def Validate(codeStr: str, leewaySeconds: int = 60) -> bytes:
    data = base64.urlsafe_b64decode(codeStr)
    pubKey = RSA.import_key(_PUBLIC_KEY_PEM.encode())
    sigLen = pubKey.size_in_bytes()
    payloadBytes, signature = data[:-sigLen], data[-sigLen:]

    pss.new(pubKey).verify(SHA256.new(payloadBytes), signature)  # 若失败抛异常

    payload = json.loads(payloadBytes)
    if int(time.time()) > payload["ts"] + leewaySeconds:
        raise ValueError("Activation code expired")

    return bytes.fromhex(payload["seed"])
