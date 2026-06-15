# 本地 NTP 授时测试工具

English version: [README.en.md](README.en.md)

这是一个使用 Python 实现的本地 NTP 授时工具，面向同一网络环境下的嵌入式设备测试。它支持图形界面、命令行模式、可控时间策略、客户端回环测试，以及日志记录与导出。

## 主要能力

- 提供局域网可访问的 UDP NTP/SNTP 授时服务，默认端口为 `123`
- 支持固定时间、冻结时间、连续走时、基于本机时间的偏移授时
- 支持时间倍率推进，便于验证跨天等时间逻辑
- 支持本地时间与 `UTC` 输入/显示切换
- 内置 NTP 客户端测试，可测试本地服务、局域网 IP 或域名目标
- 支持服务请求日志、客户端测试结果查看与 `CSV` 导出
- 提供 GUI 和 CLI 两种运行方式

## 运行要求

- Python `3.10+`
- 建议使用项目虚拟环境 `.venv`

## 安装

先创建虚拟环境：

```bash
python -m venv .venv
```

安装依赖：

Windows:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

macOS / Linux:

```bash
./.venv/bin/python -m pip install -r requirements.txt
```

## 启动

GUI:

Windows PowerShell:

```powershell
./start.ps1
```

Windows CMD:

```bat
start.bat
```

macOS / Linux:

```bash
./start.sh
```

CLI 示例：

```powershell
./start.ps1 --cli --host 0.0.0.0 --port 123
./start.ps1 --cli --query 192.168.1.10:123
```

这些启动脚本会优先使用项目根目录下的 `.venv`，只有在 `.venv` 不存在时才回退到系统 Python。

## 打包

Windows:

```powershell
./build.ps1
```

macOS / Linux:

```bash
./build.sh
```

打包脚本同样会优先使用项目 `.venv`。

## 测试

Windows:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

macOS / Linux:

```bash
./.venv/bin/python -m unittest discover -s tests -v
```

## GitHub Tag 自动打包

仓库包含 GitHub Actions 工作流 [build-release-on-tag.yml](.github/workflows/build-release-on-tag.yml)。

推送标签后，例如：

```bash
git tag v0.1.0
git push origin v0.1.0
```

工作流会在 `Windows / Ubuntu / macOS` 上构建程序，上传构建产物，并附加到对应 tag 的 GitHub Release。

## 注意事项

- 使用 `123/UDP` 在部分系统上可能需要管理员权限
- 如果端口被占用，程序会直接报错，需要手动修改端口后重试
- 当前实现优先支持 `IPv4`
