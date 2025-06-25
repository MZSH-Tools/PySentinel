"""
生成稳定且跨平台的机器指纹（MAC + Hostname）
返回 64 字符 SHA256 Hex
"""
import hashlib, socket, uuid


def _GetMacAddress() -> str:
    mac = uuid.getnode()
    return "-".join(f"{(mac >> ele) & 0xFF:02X}" for ele in range(40, -8, -8))


def GetFingerprint() -> str:
    raw = f"{_GetMacAddress()}|{socket.gethostname().lower()}"
    return hashlib.sha256(raw.encode()).hexdigest()
