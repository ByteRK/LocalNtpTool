# Local NTP Test Tool

中文说明: [README.md](README.md)

This project is a Python-based local NTP test tool for LAN devices. It provides a GUI, a CLI mode, configurable time behavior, built-in client-side verification, and log export for time-related testing.

## Features

- LAN-accessible UDP NTP/SNTP server with default `123/UDP`
- Fixed time, frozen time, continuously running time, and offset time based on the local system clock
- Time rate multiplier support for fast cross-day and time-flow testing
- Local-time and `UTC` input/display switching
- Built-in NTP client tester for localhost, LAN IPs, and hostnames
- Service request logs, client test result viewing, and `CSV` export
- Both GUI and CLI launch modes

## Requirements

- Python `3.10+`
- A project virtual environment `.venv` is recommended

## Install

Create a virtual environment first:

```bash
python -m venv .venv
```

Install dependencies:

Windows:

```powershell
./.venv/Scripts/python.exe -m pip install -r requirements.txt
```

macOS / Linux:

```bash
./.venv/bin/python -m pip install -r requirements.txt
```

## Run

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

CLI examples:

```powershell
./start.ps1 --cli --host 0.0.0.0 --port 123
./start.ps1 --cli --query 192.168.1.10:123
```

These launcher scripts prefer the project `.venv` when it exists, and only fall back to a system Python interpreter when no project virtual environment is available.

## Build

Windows:

```powershell
./build.ps1
```

macOS / Linux:

```bash
./build.sh
```

The build scripts also prefer the project `.venv`.

## Tests

Windows:

```powershell
./.venv/Scripts/python.exe -m unittest discover -s tests -v
```

macOS / Linux:

```bash
./.venv/bin/python -m unittest discover -s tests -v
```

## GitHub Tag Build

The repository includes the GitHub Actions workflow [build-release-on-tag.yml](.github/workflows/build-release-on-tag.yml).

After pushing a tag, for example:

```bash
git tag v0.1.0
git push origin v0.1.0
```

The workflow builds the application on `Windows / Ubuntu / macOS`, uploads the build artifacts, and attaches them to the GitHub Release for that tag.

## Notes

- Binding `123/UDP` may require administrator privileges on some systems
- If the port is already in use, the tool reports an error and requires a manual port change
- The current implementation primarily targets `IPv4`
