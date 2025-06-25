import sys, traceback, tempfile, subprocess, base64, importlib.resources
from pathlib import Path

from Source.Logic import ActivationCode
from Source.Logic.EncryptionUtils import DecryptBytes
from Source.Logic.LicenseManager  import VerifyAndGetKey, CreateLicense

PRODUCT_ID      = "__PRODUCT_ID__"
PUBLIC_KEY_PEM  = """__PUBLIC_KEY__"""
ActivationCode._PUBLIC_KEY_PEM = PUBLIC_KEY_PEM


def prompt_activation_code() -> str | None:
    """优先用控制台；无控制台时弹 TK 对话框"""
    # 1) 尝试 stdin
    try:
        if sys.stdin and sys.stdin.isatty():
            return input("请输入激活码：").strip()
    except Exception:
        pass

    # 2) 弹窗（tkinter）
    try:
        import tkinter as tk
        from tkinter import simpledialog
        root = tk.Tk()
        root.withdraw()
        code = simpledialog.askstring("激活", "请输入激活码：")
        root.destroy()
        return code.strip() if code else None
    except Exception:
        return None


def _first_activation():
    """首激活循环；用户可取消退出"""
    while True:
        code = prompt_activation_code()
        if code is None:                 # ← 用户点关闭/取消
            sys.exit(0)

        if not code.strip():             # ← 空输入重来
            continue

        try:
            seed, prod = ActivationCode.Validate(code.strip())
            if prod != PRODUCT_ID:
                raise ValueError("激活码与本软件不匹配")
            CreateLicense(seed, PRODUCT_ID)
            return                       # 成功后回到 main
        except Exception as e:
            try:
                import tkinter.messagebox as mb
                mb.showerror("激活失败", str(e))
            except Exception:
                print("×", e)


def main():
    try:
        try:
            userKey = VerifyAndGetKey(PRODUCT_ID)
        except FileNotFoundError:
            _first_activation()
            userKey = VerifyAndGetKey(PRODUCT_ID)

        blob = importlib.resources.read_binary(__package__ or "Assets", "encrypted_payload.dat")
        payload = DecryptBytes(blob, userKey)

        tmpDir = Path(tempfile.mkdtemp())
        ext = ".exe" if payload[:2] == b"MZ" else ".py"
        outFile = tmpDir / f"payload{ext}"
        outFile.write_bytes(payload)

        if ext == ".exe":
            subprocess.run([str(outFile)], check=False)
        else:
            subprocess.run([sys.executable, str(outFile)], check=False)

    except Exception:
        traceback.print_exc()
        try:
            import tkinter.messagebox as mb
            mb.showerror("错误", traceback.format_exc())
        except Exception:
            input("Press <Enter> to exit …")


if __name__ == "__main__":
    main()
