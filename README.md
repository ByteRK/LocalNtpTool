# Local NTP Test Tool / 本地 NTP 授时测试工具

## 中文说明

这是一个使用 Python 实现的本地 NTP 授时工具，面向同一网络环境下的嵌入式设备测试。它支持图形界面、命令行启动、固定时间/偏移时间/倍率推进、客户端回环测试、访问日志记录与导出。

### 主要能力

- 提供局域网内可访问的 UDP NTP/SNTP 授时服务，默认端口为 `123`
- 支持固定时间、冻结时间、自定义起点连续走时
- 支持基于本机时间的偏移授时
- 支持时间倍率，例如 `2x`、`60x`、`3600x`
- GUI 支持本地时间与 `UTC` 输入/显示切换
- GUI 支持日期控件和文本两种时间输入方式
- 内置 NTP 客户端测试，可测试本地服务、局域网 IP 或域名目标
- 记录服务请求日志和客户端测试日志，并支持导出为 `CSV`
- 配置默认保存在程序目录，也可切换到用户目录或自定义目录
- 提供 CLI 模式，便于无界面运行或脚本化启动

### 运行要求

- Python `3.10+`
- 建议先创建虚拟环境

### 安装依赖

```bash
pip install -r requirements.txt
```

### 启动图形界面

```bash
python run_ntp_tool.py
```

### 启动命令行模式

```bash
python run_ntp_tool.py --cli --host 0.0.0.0 --port 123
```

### CLI 示例

固定时间并连续走时：

```bash
python run_ntp_tool.py --cli --mode fixed --progress-mode running --target-datetime 2026-06-15T12:00:00+00:00 --rate 1.0
```

固定时间并冻结：

```bash
python run_ntp_tool.py --cli --mode fixed --progress-mode frozen --target-datetime 2026-06-15T23:59:50+00:00
```

查询某个 NTP 服务：

```bash
python run_ntp_tool.py --cli --query 192.168.1.10:123
python run_ntp_tool.py --cli --query ntp.example.com:123
```

### 打包 Windows 可执行程序

```powershell
./build.ps1
```

首次打包会在当前环境安装 `PyInstaller`，产物默认输出到 `dist/LocalNtpTool/`。

### 注意事项

- 使用 `123/UDP` 在部分系统上可能需要管理员权限
- 如果端口被占用，程序会直接报错并等待你手动修改端口
- 当前实现优先支持 `IPv4`，并为后续 `IPv6` 扩展预留了代码结构
- 当前实现使用标准 NTP 基础响应字段，适合大多数嵌入式 SNTP/NTP 获取时间测试

### 自动化测试

```bash
python -m unittest discover -s tests -v
```

## English Notes

This project is a Python-based local NTP test tool for LAN devices. It provides a Tkinter GUI, a CLI mode, configurable fixed or offset time serving, time-rate acceleration, client-side query testing, and CSV log export.

### Features

- LAN-accessible UDP NTP/SNTP server with default `123/UDP`
- Fixed time with frozen or continuously running behavior
- Offset time based on the local system clock
- Time rate multiplier support such as `2x`, `60x`, or `3600x`
- Local-time and `UTC` input/display switching
- Date picker and text input for target time
- Built-in NTP client tester for localhost, IPs, and hostnames
- Service request logs and client test logs with CSV export
- Config persistence with program-directory default and user/custom directory options
- GUI plus headless CLI mode

### Install

```bash
pip install -r requirements.txt
```

### Run GUI

```bash
python run_ntp_tool.py
```

### Run CLI

```bash
python run_ntp_tool.py --cli --host 0.0.0.0 --port 123
```

### Tests

```bash
python -m unittest discover -s tests -v
```
