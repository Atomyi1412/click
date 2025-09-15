# GitHub Actions 自动构建说明

本项目已配置 GitHub Actions 自动构建系统，可以在 GitHub 上自动构建 Windows 兼容版本。

## 🚀 自动构建工作流

### 1. 构建工作流 (build-windows.yml)
**触发条件**：
- 手动触发 (workflow_dispatch)
- 推送到 main/master 分支且包含 Python 文件变更

**构建内容**：
- **兼容版本**：使用 `build_windows_compatible.py` 构建真正的 64 位 Windows 可执行文件
- **传统版本**：使用 `build_windows.py` 构建单文件版本

### 2. 发布工作流 (release.yml)
**触发条件**：
- 手动触发并指定版本号
- 推送 Git 标签 (如 v1.0.0)

**发布内容**：
- 自动创建 GitHub Release
- 上传兼容版本和传统版本的压缩包
- 生成详细的发布说明

## 📦 使用方法

### 方法一：手动触发构建
1. 进入 GitHub 仓库页面
2. 点击 "Actions" 标签
3. 选择 "Build Windows Compatible EXE" 工作流
4. 点击 "Run workflow" 按钮
5. 等待构建完成，下载 Artifacts

### 方法二：手动创建发布版本
1. 进入 GitHub 仓库页面
2. 点击 "Actions" 标签
3. 选择 "Create Release" 工作流
4. 点击 "Run workflow" 按钮
5. 输入版本号 (如 v1.2.0)
6. 选择是否为预发布版本
7. 点击 "Run workflow" 开始构建
8. 构建完成后会自动创建 Release 并上传文件

### 方法三：通过 Git 标签自动发布
```bash
# 创建并推送标签
git tag v1.2.0
git push origin v1.2.0
```

## 📋 构建产物说明

### 兼容版本 (推荐)
- **文件名**：`MouseClicker_Win11_Compatible_Portable.zip`
- **特点**：
  - 真正的 64 位 Windows 可执行文件
  - 解决 "此应用无法在你的电脑上运行" 问题
  - 使用目录模式，包含所有依赖
  - 免安装，解压即用

### 传统版本 (备用)
- **文件名**：`MouseClicker_Win11_Legacy.zip`
- **特点**：
  - 单文件模式
  - 体积较小
  - 如果兼容版本无法使用可尝试此版本

## 🔧 技术细节

### 构建环境
- **操作系统**：Windows Latest (GitHub Actions)
- **Python 版本**：3.11
- **架构**：x64
- **PyInstaller 版本**：6.13.0

### 兼容版本构建参数
- `--onedir`：目录模式，提高兼容性
- `--windowed`：无控制台窗口
- `--noupx`：不使用 UPX 压缩，避免兼容性问题
- `--optimize=2`：Python 字节码优化
- `--strip`：去除调试信息

### 传统版本构建参数
- `--onefile`：单文件模式
- `--windowed`：无控制台窗口
- 包含图标和配置文件

## ⚠️ 注意事项

1. **构建环境**：必须在 Windows 环境下构建才能生成真正的 Windows 可执行文件
2. **权限要求**：GitHub Actions 需要有创建 Release 的权限
3. **文件大小**：兼容版本由于包含所有依赖，文件较大但兼容性更好
4. **首次运行**：用户首次运行时可能需要允许 Windows Defender 警告

## 🐛 故障排除

### 构建失败
1. 检查 Python 依赖是否正确
2. 查看 Actions 日志中的错误信息
3. 确认 PyInstaller 版本兼容性

### 发布失败
1. 检查是否有创建 Release 的权限
2. 确认标签格式正确 (v开头)
3. 检查 GITHUB_TOKEN 权限

### 运行时问题
1. 下载兼容版本而非传统版本
2. 以管理员权限运行
3. 添加到 Windows Defender 排除列表

---

通过 GitHub Actions，用户可以直接从 GitHub 下载到真正兼容 Windows 11 的可执行文件，无需本地构建环境。