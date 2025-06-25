"""
AES-GCM 加/解工具
"""
from pathlib import Path
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Hash import SHA256

_NONCE_LEN = 12      # 推荐 12 字节
_TAG_LEN = 16        # GCM 默认 16 字节


def DeriveUserKey(seed: bytes, fingerprintBytes: bytes = b"") -> bytes:
    """
    默认仍然 **只用 seed**，但保留 fingerprintBytes 扩展口
    若将来想真正把指纹混进去，加一句 hasher.update(fingerprintBytes)
    """
    hasher = SHA256.new()
    hasher.update(seed)
    # if fingerprintBytes: hasher.update(fingerprintBytes)
    return hasher.digest()


def EncryptFile(inPath: Path, userKey: bytes, outPath: Path) -> None:
    cipher = AES.new(userKey, AES.MODE_GCM, nonce=get_random_bytes(_NONCE_LEN))
    with inPath.open("rb") as f:
        plaintext = f.read()
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)

    outPath.write_bytes(cipher.nonce + tag + ciphertext)


def DecryptBytes(data: bytes, userKey: bytes) -> bytes:
    nonce = data[:_NONCE_LEN]
    tag = data[_NONCE_LEN:_NONCE_LEN + _TAG_LEN]
    ciphertext = data[_NONCE_LEN + _TAG_LEN:]
    cipher = AES.new(userKey, AES.MODE_GCM, nonce=nonce)
    return cipher.decrypt_and_verify(ciphertext, tag)
