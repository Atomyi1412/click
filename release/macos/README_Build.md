# 鼠标连点器打包指南

本文档介绍如何将鼠标连点器项目打包成可执行文件。

## 📋 系统要求

### 通用要求
- Python 3.7 或更高版本
- PyInstaller 6.0 或更高版本
- 项目依赖：PyQt5, pynput, keyboard

### Windows 特定要求
- Windows 10 或更高版本
- Visual Studio Build Tools（可选，用于编译某些依赖）

### macOS 特定要求
- macOS 10.13 或更高版本
- Xcode Command Line Tools
- 开发者账户（可选，用于代码签名）

## 🚀 快速开始

### 1. 安装依赖

```bash
# 安装 PyInstaller
python3 -m pip install pyinstaller

# 安装项目依赖
python3 -m pip install -r requirements.txt
```

### 2. 执行打包

#### 方法一：使用通用打包脚本（推荐）

```bash
python3 build.py
```

这个脚本会：
- 自动检测当前平台
- 检查依赖是否完整
- 提供交互式选择打包方式
- 显示详细的打包结果

#### 方法二：使用平台特定脚本

**Windows:**
```bash
python3 build_windows.py
```

**macOS:**
```bash
python3 build_macos.py
```

#### 方法三：直接使用 PyInstaller

```bash
# 使用 spec 文件
python3 -m PyInstaller auto_clicker.spec

# 或者直接打包
python3 -m PyInstaller --onefile --windowed auto_clicker_native.py
```

## 📁 输出文件

打包完成后，文件将生成在以下位置：

```
project/
├── dist/                    # PyInstaller 输出目录
│   ├── 鼠标连点器.exe      # Windows 可执行文件
│   └── 鼠标连点器.app/     # macOS 应用包
├── release/                 # 发布包目录
│   ├── windows/            # Windows 发布包
│   │   ├── 鼠标连点器.exe
│   │   └── README.md
│   └── macos/              # macOS 发布包
│       ├── 鼠标连点器.app/
│       ├── 权限设置指南.md
│       └── README.md
└── build/                   # 临时构建文件（可删除）
```

## 🔧 自定义配置

### 修改应用信息

编辑 `auto_clicker.spec` 文件来自定义：

```python
# 应用名称
name='鼠标连点器'

# 图标文件
icon='icon.ico'  # Windows
icon='icon.icns' # macOS

# Bundle ID (macOS)
bundle_identifier='com.autoclicker.native'

# 版本信息
info_plist={
    'CFBundleVersion': '1.0.0',
    'CFBundleShortVersionString': '1.0.0',
    # ...
}
```

### 添加资源文件

在 `auto_clicker.spec` 的 `datas` 部分添加：

```python
datas=[
    ('config_native.json', '.'),
    ('icons/', 'icons/'),  # 添加图标目录
    ('docs/', 'docs/'),    # 添加文档目录
],
```

### 排除不需要的模块

在 `excludes` 部分添加要排除的模块以减小文件大小：

```python
excludes=[
    'tkinter',
    'matplotlib',
    'numpy',
    'scipy',
    # 添加其他不需要的模块
],
```

## 🐛 常见问题

### Windows 问题

**问题：缺少 DLL 文件**
```
解决：安装 Visual C++ Redistributable
下载地址：https://aka.ms/vs/17/release/vc_redist.x64.exe
```

**问题：杀毒软件误报**
```
解决：将生成的 exe 文件添加到杀毒软件的信任列表
```

**问题：打包文件过大**
```
解决：
1. 在 spec 文件中排除不需要的模块
2. 使用 UPX 压缩（在 spec 中设置 upx=True）
3. 考虑使用 --onedir 而不是 --onefile
```

### macOS 问题

**问题：应用无法启动**
```
解决：
1. 右键点击应用，选择 "打开"
2. 运行：xattr -cr 鼠标连点器.app
3. 检查是否有权限问题
```

**问题：热键不工作**
```
解决：
1. 设置辅助功能权限
2. 系统偏好设置 > 安全性与隐私 > 隐私 > 辅助功能
3. 添加应用到允许列表
```

**问题：代码签名警告**
```
解决：
1. 获取开发者证书
2. 使用 codesign 命令签名
3. 或者让用户手动信任应用
```

### 通用问题

**问题：导入错误**
```
解决：
1. 检查 hiddenimports 列表
2. 添加缺失的模块到 spec 文件
3. 使用 --collect-all 参数
```

**问题：配置文件丢失**
```
解决：
1. 确保配置文件在 datas 列表中
2. 检查文件路径是否正确
3. 使用相对路径而不是绝对路径
```

## 📝 打包检查清单

打包前请确认：

- [ ] 所有依赖已正确安装
- [ ] 主程序可以正常运行
- [ ] 配置文件路径正确
- [ ] 图标文件存在（可选）
- [ ] spec 文件配置正确

打包后请测试：

- [ ] 应用可以正常启动
- [ ] 界面显示正常
- [ ] 基本功能工作正常
- [ ] 热键功能正常（需要权限）
- [ ] 配置保存和加载正常
- [ ] 在干净的系统上测试

## 🔗 相关链接

- [PyInstaller 官方文档](https://pyinstaller.readthedocs.io/)
- [PyQt5 打包指南](https://doc.qt.io/qtforpython/deployment.html)
- [macOS 代码签名指南](https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution)
- [Windows 应用打包最佳实践](https://docs.microsoft.com/en-us/windows/win32/dlls/dynamic-link-library-best-practices)

## 📞 技术支持

如果在打包过程中遇到问题：

1. 检查本文档的常见问题部分
2. 查看 PyInstaller 的详细日志输出
3. 搜索相关错误信息
4. 在项目 Issues 中提交问题报告

---

**注意：** 打包后的应用文件较大是正常现象，因为包含了完整的 Python 运行时和所有依赖库。如果需要减小文件大小，可以考虑使用虚拟环境或排除不必要的模块。