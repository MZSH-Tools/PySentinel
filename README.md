# PySentinel – 使用说明

> **一个离线激活 + 本机绑定的“一键加壳”解决方案**  
> 适合个人开发者：每次导出 → 自动生成密钥 → 打包独立 EXE + 激活码 → 私钥用完即删

---

## 0. 环境准备

```bash
# Python ≥3.9
pip install -r requirements.txt       # PySide6 + PyInstaller + pycryptodomex
```

## 1. 生成开发者 GUI（可选）

```bash
# 仅第一次或换电脑时操作
pyinstaller -F -w Main.py --name PySentinelBuilder --add-data "Source;Source"
# dist/PySentinelBuilder.exe 即是加壳工具
```

> 也可以直接 `python Main.py` 运行，不必打包。

## 2. 使用 Builder 导出

1. 运行 **PySentinelBuilder.exe**
2. 点击 **＋ 添加目标** → 选择待加壳文件 + 设置激活码分钟数
3. 选择 **导出目录**
4. 点击 **开始导出**
    - Builder 自动完成：
        - 内存生成 RSA 密钥对
        - 计算 ProductId（每个目标唯一）
        - 生成激活码 (包含 seed + ProductId)
        - AES-GCM 加密载荷
        - 动态写公钥 / ProductId → PayloadRunner 模板
        - PyInstaller -F 打包 → `导出目录/目标名.exe`
    - 日志最末行输出 **激活码**（约 270 字符）

> **输出文件**
> - `目标名.exe`：单文件壳，已内嵌密文载荷 + 公钥
> - （无私钥落盘，临时目录自动清理）

## 3. 交付给客户

- 发送 **目标名.exe** ＋ **激活码字符串**
- 每个 EXE 只能用对应激活码；不同软件/版本互不干扰

## 4. 客户首次激活

1. 双击 `目标名.exe` → 控制台提示“请输入激活码”
2. 粘贴激活码 → 成功后写入
   ```
   %APPDATA%\PySentinel\licenses\<ProductId>.json   (Windows)
   ~/.PySentinel/licenses/<ProductId>.json            (macOS/Linux)
   ```  
3. 之后同机离线使用，无需再输入

## 5. 复制/换机行为

- EXE + 激活码拷到其他电脑 → 指纹不符，license 解密失败 → 程序退出
- 若用户丢失激活码或换机：**重新导出新的 EXE + 激活码** 再发给对方

## 6. 项目结构回顾

```
PySentinel/
├─ Main.py                # Builder GUI
├─ PayloadRunner.py       # 壳模板（带占位符）
├─ Source/
│   ├─ UI/…               # 界面层
│   └─ Logic/…            # 加密/激活/许可证/指纹
└─ requirements.txt
```

---

### 常见问题

| 问题 | 解决 |
|------|------|
|EXE 体积大？|客户侧壳 ~30 MB；Builder.exe 含 PySide6 ~80 MB|
|杀软误报？|`--noconsole` 或 `--upx-dir` 压缩后对 EXE 进行代码签名|
|换图标/版本信息？|在 PyInstaller 命令中加 `--icon` `--version-file` 参数|

---

> **记忆口诀**
> - **导出** = “选择文件 + 点按钮”
> - **发货** = “EXE + 激活码”
> - **激活** = “首次输入 → 永久本机”
> - **私钥** = “只在内存，用完即删”
