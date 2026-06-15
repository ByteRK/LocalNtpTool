from __future__ import annotations

import datetime as dt
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from tkcalendar import DateEntry

from .client import NtpClient
from .config import default_program_storage_dir, default_user_storage_dir, load_state, save_state
from .constants import CLIENT_LOG_FILE_NAME, CONFIG_FILE_NAME, DEFAULT_LOG_EXPORT_PREFIX, SERVER_LOG_FILE_NAME
from .logging_store import LogStore
from .models import AppPaths, BaseTimeMode, PersistedState, ProgressMode, TimeProfile, TimezoneDisplay
from .network import list_ipv4_addresses
from .server import NtpServer
from .time_engine import TimeEngine


DATETIME_TEXT_FORMAT = "%Y-%m-%d %H:%M:%S"
DATETIME_TEXT_FORMAT_MS = "%Y-%m-%d %H:%M:%S.%f"


def launch_gui(config_path: Path | None = None) -> None:
    app = NtpToolApp(config_path)
    app.run()


class NtpToolApp:
    def __init__(self, config_path: Path | None = None) -> None:
        self.state = load_state(config_path)
        if self.state.paths is None:
            default_dir = default_program_storage_dir()
            self.state.paths = AppPaths(default_dir, default_dir / CONFIG_FILE_NAME)

        self.logs = LogStore()
        self.time_engine = TimeEngine(self.state.time_profile)
        self.server = NtpServer(self.time_engine, self.logs, self._queue_status_message)
        self.client = NtpClient(self.logs)
        self.pending_status_messages: list[str] = []

        self.root = tk.Tk()
        self.root.title("本地NTP授时测试工具")
        self.root.geometry("1280x860")
        self.root.minsize(1100, 760)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.host_var = tk.StringVar(value=self.state.server.host)
        self.port_var = tk.StringVar(value=str(self.state.server.port))
        self.auto_start_var = tk.BooleanVar(value=self.state.server.auto_start)
        self.base_mode_var = tk.StringVar(value=self.state.time_profile.base_mode.value)
        self.progress_mode_var = tk.StringVar(value=self.state.time_profile.progress_mode.value)
        self.timezone_var = tk.StringVar(value=self.state.time_profile.timezone_display.value)
        self.offset_var = tk.StringVar(value=f"{self.state.time_profile.offset_seconds}")
        self.rate_var = tk.StringVar(value=f"{self.state.time_profile.rate_multiplier}")
        self.fixed_text_var = tk.StringVar(value=self._format_profile_datetime(self.state.time_profile))
        self.fixed_time_var = tk.StringVar(value=self._format_time_of_day(self.state.time_profile))
        self.current_service_time_var = tk.StringVar()
        self.server_status_var = tk.StringVar(value="未启动")
        self.service_mode_var = tk.StringVar(value=self.time_engine.describe())
        self.path_mode_var = tk.StringVar(
            value="program" if self._is_program_storage_selected() else "custom"
        )
        self.storage_dir_var = tk.StringVar(value=str(self.state.paths.storage_dir))
        self.config_file_var = tk.StringVar(value=str(self.state.paths.config_path))
        self.client_host_var = tk.StringVar(value=self.state.client.host)
        self.client_port_var = tk.StringVar(value=str(self.state.client.port))
        self.client_timeout_var = tk.StringVar(value=str(self.state.client.timeout_seconds))
        self.client_result_var = tk.StringVar(value="等待测试")

        self.ip_addresses = list_ipv4_addresses()

        self._build_ui()
        self._refresh_ui_from_profile()
        self._schedule_periodic_refresh()

        if self.state.server.auto_start:
            self.root.after(250, self.start_server)

    def run(self) -> None:
        self.root.mainloop()

    def _build_ui(self) -> None:
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        server_tab = ttk.Frame(notebook, padding=12)
        client_tab = ttk.Frame(notebook, padding=12)
        log_tab = ttk.Frame(notebook, padding=12)
        notebook.add(server_tab, text="授时服务")
        notebook.add(client_tab, text="客户端测试")
        notebook.add(log_tab, text="日志与导出")

        self._build_server_tab(server_tab)
        self._build_client_tab(client_tab)
        self._build_log_tab(log_tab)

    def _build_server_tab(self, parent: ttk.Frame) -> None:
        network_frame = ttk.LabelFrame(parent, text="网络与启动", padding=12)
        network_frame.pack(fill=tk.X, pady=(0, 10))

        host_values = ["0.0.0.0"] + [ip for ip in self.ip_addresses if ip != "0.0.0.0"]
        ttk.Label(network_frame, text="监听地址").grid(row=0, column=0, sticky=tk.W, padx=(0, 8), pady=4)
        self.host_combo = ttk.Combobox(network_frame, textvariable=self.host_var, values=host_values, width=28)
        self.host_combo.grid(row=0, column=1, sticky=tk.W, pady=4)

        ttk.Label(network_frame, text="端口").grid(row=0, column=2, sticky=tk.W, padx=(18, 8), pady=4)
        ttk.Entry(network_frame, textvariable=self.port_var, width=10).grid(row=0, column=3, sticky=tk.W, pady=4)

        ttk.Checkbutton(network_frame, text="启动时自动运行服务", variable=self.auto_start_var).grid(
            row=0, column=4, sticky=tk.W, padx=(18, 8), pady=4
        )
        ttk.Button(network_frame, text="启动服务", command=self.start_server).grid(row=0, column=5, padx=6, pady=4)
        ttk.Button(network_frame, text="停止服务", command=self.stop_server).grid(row=0, column=6, padx=6, pady=4)

        ttk.Label(network_frame, text="本机IPv4").grid(row=1, column=0, sticky=tk.NW, padx=(0, 8), pady=4)
        ttk.Label(
            network_frame,
            text=", ".join(self.ip_addresses),
            justify=tk.LEFT,
            wraplength=850,
        ).grid(row=1, column=1, columnspan=6, sticky=tk.W, pady=4)

        status_frame = ttk.LabelFrame(parent, text="服务状态", padding=12)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(status_frame, text="服务状态").grid(row=0, column=0, sticky=tk.W, padx=(0, 8), pady=4)
        ttk.Label(status_frame, textvariable=self.server_status_var).grid(row=0, column=1, sticky=tk.W, pady=4)
        ttk.Label(status_frame, text="当前授时模式").grid(row=1, column=0, sticky=tk.W, padx=(0, 8), pady=4)
        ttk.Label(status_frame, textvariable=self.service_mode_var).grid(row=1, column=1, sticky=tk.W, pady=4)
        ttk.Label(status_frame, text="当前授时时间").grid(row=2, column=0, sticky=tk.W, padx=(0, 8), pady=4)
        ttk.Label(status_frame, textvariable=self.current_service_time_var).grid(row=2, column=1, sticky=tk.W, pady=4)

        time_frame = ttk.LabelFrame(parent, text="时间策略", padding=12)
        time_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(time_frame, text="基准模式").grid(row=0, column=0, sticky=tk.W, padx=(0, 8), pady=4)
        ttk.Radiobutton(time_frame, text="本机时间", variable=self.base_mode_var, value=BaseTimeMode.SYSTEM.value).grid(
            row=0, column=1, sticky=tk.W, pady=4
        )
        ttk.Radiobutton(time_frame, text="自定义时间", variable=self.base_mode_var, value=BaseTimeMode.FIXED.value).grid(
            row=0, column=2, sticky=tk.W, pady=4
        )

        ttk.Label(time_frame, text="推进模式").grid(row=1, column=0, sticky=tk.W, padx=(0, 8), pady=4)
        ttk.Radiobutton(
            time_frame,
            text="连续走时",
            variable=self.progress_mode_var,
            value=ProgressMode.RUNNING.value,
        ).grid(row=1, column=1, sticky=tk.W, pady=4)
        ttk.Radiobutton(
            time_frame,
            text="冻结时间",
            variable=self.progress_mode_var,
            value=ProgressMode.FROZEN.value,
        ).grid(row=1, column=2, sticky=tk.W, pady=4)

        ttk.Label(time_frame, text="界面时区").grid(row=2, column=0, sticky=tk.W, padx=(0, 8), pady=4)
        ttk.Radiobutton(time_frame, text="本地时间", variable=self.timezone_var, value=TimezoneDisplay.LOCAL.value).grid(
            row=2, column=1, sticky=tk.W, pady=4
        )
        ttk.Radiobutton(time_frame, text="UTC", variable=self.timezone_var, value=TimezoneDisplay.UTC.value).grid(
            row=2, column=2, sticky=tk.W, pady=4
        )

        ttk.Label(time_frame, text="日期控件").grid(row=3, column=0, sticky=tk.W, padx=(0, 8), pady=4)
        initial_date = self._picker_date_from_profile()
        self.date_picker = DateEntry(time_frame, width=14, date_pattern="yyyy-mm-dd")
        self.date_picker.set_date(initial_date)
        self.date_picker.grid(row=3, column=1, sticky=tk.W, pady=4)

        ttk.Label(time_frame, text="时间输入").grid(row=3, column=2, sticky=tk.W, padx=(18, 8), pady=4)
        ttk.Entry(time_frame, textvariable=self.fixed_time_var, width=16).grid(row=3, column=3, sticky=tk.W, pady=4)
        ttk.Button(time_frame, text="使用日期控件填充文本", command=self.apply_picker_to_text).grid(
            row=3, column=4, padx=6, pady=4
        )

        ttk.Label(time_frame, text="完整时间文本").grid(row=4, column=0, sticky=tk.W, padx=(0, 8), pady=4)
        ttk.Entry(time_frame, textvariable=self.fixed_text_var, width=34).grid(
            row=4, column=1, columnspan=2, sticky=tk.W, pady=4
        )
        ttk.Label(time_frame, text="支持格式: YYYY-MM-DD HH:MM:SS[.mmm]").grid(
            row=4, column=3, columnspan=2, sticky=tk.W, pady=4
        )

        ttk.Label(time_frame, text="时间偏移(秒)").grid(row=5, column=0, sticky=tk.W, padx=(0, 8), pady=4)
        ttk.Entry(time_frame, textvariable=self.offset_var, width=16).grid(row=5, column=1, sticky=tk.W, pady=4)
        ttk.Label(time_frame, text="时间倍率").grid(row=5, column=2, sticky=tk.W, padx=(18, 8), pady=4)
        ttk.Entry(time_frame, textvariable=self.rate_var, width=16).grid(row=5, column=3, sticky=tk.W, pady=4)

        ttk.Button(time_frame, text="应用时间策略", command=self.apply_time_profile).grid(
            row=6, column=0, padx=0, pady=(12, 4), sticky=tk.W
        )
        ttk.Button(time_frame, text="使用当前时间", command=self.set_fixed_text_to_now).grid(
            row=6, column=1, padx=6, pady=(12, 4), sticky=tk.W
        )
        ttk.Button(time_frame, text="保存配置", command=self.save_current_state).grid(
            row=6, column=2, padx=6, pady=(12, 4), sticky=tk.W
        )

        path_frame = ttk.LabelFrame(parent, text="配置与存储", padding=12)
        path_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Label(path_frame, text="存储目录").grid(row=0, column=0, sticky=tk.W, padx=(0, 8), pady=4)
        ttk.Entry(path_frame, textvariable=self.storage_dir_var, width=72).grid(row=0, column=1, columnspan=3, sticky=tk.W, pady=4)
        ttk.Button(path_frame, text="选择目录", command=self.choose_storage_dir).grid(row=0, column=4, padx=6, pady=4)
        ttk.Button(path_frame, text="切回程序目录", command=self.use_program_storage).grid(row=0, column=5, padx=6, pady=4)
        ttk.Button(path_frame, text="切到用户目录", command=self.use_user_storage).grid(row=0, column=6, padx=6, pady=4)
        ttk.Label(path_frame, text="配置文件").grid(row=1, column=0, sticky=tk.W, padx=(0, 8), pady=4)
        ttk.Entry(path_frame, textvariable=self.config_file_var, width=72).grid(row=1, column=1, columnspan=3, sticky=tk.W, pady=4)

    def _build_client_tab(self, parent: ttk.Frame) -> None:
        query_frame = ttk.LabelFrame(parent, text="客户端查询", padding=12)
        query_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(query_frame, text="目标IP/域名").grid(row=0, column=0, sticky=tk.W, padx=(0, 8), pady=4)
        ttk.Entry(query_frame, textvariable=self.client_host_var, width=36).grid(row=0, column=1, sticky=tk.W, pady=4)
        ttk.Label(query_frame, text="端口").grid(row=0, column=2, sticky=tk.W, padx=(18, 8), pady=4)
        ttk.Entry(query_frame, textvariable=self.client_port_var, width=10).grid(row=0, column=3, sticky=tk.W, pady=4)
        ttk.Label(query_frame, text="超时(秒)").grid(row=0, column=4, sticky=tk.W, padx=(18, 8), pady=4)
        ttk.Entry(query_frame, textvariable=self.client_timeout_var, width=10).grid(row=0, column=5, sticky=tk.W, pady=4)
        ttk.Button(query_frame, text="测试指定目标", command=self.run_client_query).grid(row=0, column=6, padx=6, pady=4)
        ttk.Button(query_frame, text="测试本地服务", command=self.run_local_query).grid(row=0, column=7, padx=6, pady=4)

        result_frame = ttk.LabelFrame(parent, text="测试结果", padding=12)
        result_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(result_frame, textvariable=self.client_result_var, justify=tk.LEFT, wraplength=1100).pack(anchor=tk.W)

        self.client_tree = ttk.Treeview(
            parent,
            columns=("target", "success", "server_time", "delta", "rtt", "reference"),
            show="headings",
            height=16,
        )
        headings = {
            "target": "目标",
            "success": "成功",
            "server_time": "返回时间",
            "delta": "与本地差值(秒)",
            "rtt": "往返耗时(ms)",
            "reference": "原始响应摘要",
        }
        for key, title in headings.items():
            self.client_tree.heading(key, text=title)
            self.client_tree.column(key, width=170, anchor=tk.W)
        self.client_tree.pack(fill=tk.BOTH, expand=True)

    def _build_log_tab(self, parent: ttk.Frame) -> None:
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(button_frame, text="刷新日志", command=self.refresh_logs).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(button_frame, text="导出服务请求日志", command=self.export_service_logs).pack(side=tk.LEFT, padx=6)
        ttk.Button(button_frame, text="导出客户端测试日志", command=self.export_client_logs).pack(side=tk.LEFT, padx=6)

        split = ttk.Panedwindow(parent, orient=tk.VERTICAL)
        split.pack(fill=tk.BOTH, expand=True)

        service_frame = ttk.Labelframe(split, text="服务端访问记录", padding=12)
        client_frame = ttk.Labelframe(split, text="客户端测试记录", padding=12)
        split.add(service_frame, weight=1)
        split.add(client_frame, weight=1)

        self.service_log_tree = ttk.Treeview(
            service_frame,
            columns=("time", "ip", "port", "returned", "mode", "success", "message"),
            show="headings",
            height=12,
        )
        service_headings = {
            "time": "请求时间",
            "ip": "客户端IP",
            "port": "客户端端口",
            "returned": "返回时间",
            "mode": "授时模式",
            "success": "成功",
            "message": "消息",
        }
        for key, title in service_headings.items():
            self.service_log_tree.heading(key, text=title)
            self.service_log_tree.column(key, width=150, anchor=tk.W)
        self.service_log_tree.pack(fill=tk.BOTH, expand=True)

        self.client_log_tree = ttk.Treeview(
            client_frame,
            columns=("time", "target", "server_time", "delta", "rtt", "success", "message"),
            show="headings",
            height=12,
        )
        client_headings = {
            "time": "测试时间",
            "target": "目标",
            "server_time": "返回时间",
            "delta": "差值(秒)",
            "rtt": "往返耗时(ms)",
            "success": "成功",
            "message": "消息",
        }
        for key, title in client_headings.items():
            self.client_log_tree.heading(key, text=title)
            self.client_log_tree.column(key, width=150, anchor=tk.W)
        self.client_log_tree.pack(fill=tk.BOTH, expand=True)

    def apply_picker_to_text(self) -> None:
        date_value = self.date_picker.get_date()
        time_text = self.fixed_time_var.get().strip() or "00:00:00"
        self.fixed_text_var.set(f"{date_value.strftime('%Y-%m-%d')} {time_text}")

    def set_fixed_text_to_now(self) -> None:
        timezone_display = TimezoneDisplay(self.timezone_var.get())
        now = dt.datetime.now().astimezone() if timezone_display == TimezoneDisplay.LOCAL else dt.datetime.now(dt.timezone.utc)
        self.fixed_text_var.set(now.strftime(DATETIME_TEXT_FORMAT))
        self.fixed_time_var.set(now.strftime("%H:%M:%S"))
        self.date_picker.set_date(now.date())

    def apply_time_profile(self) -> None:
        try:
            profile = self._collect_time_profile_from_ui()
            self.time_engine.apply_profile(profile)
            self.state.time_profile = profile
            self.service_mode_var.set(self.time_engine.describe())
            self._refresh_ui_from_profile()
            self.logs.add("server", "time_profile_applied", description=self.time_engine.describe())
            self.server_status_var.set("时间策略已应用")
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("时间策略错误", str(exc))

    def start_server(self) -> None:
        try:
            self.apply_time_profile()
            host = self.host_var.get().strip() or "0.0.0.0"
            port = int(self.port_var.get().strip())
            self.server.start(host, port)
            self.state.server.host = host
            self.state.server.port = port
            self.state.server.auto_start = self.auto_start_var.get()
            self.server_status_var.set(f"运行中: {self.server.endpoint[0]}:{self.server.endpoint[1]}")
            self.save_current_state(show_message=False)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("启动失败", str(exc))

    def stop_server(self) -> None:
        try:
            if self.server.is_running:
                self.server.stop()
            self.server_status_var.set("未启动")
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("停止失败", str(exc))

    def run_client_query(self) -> None:
        try:
            host = self.client_host_var.get().strip()
            port = int(self.client_port_var.get().strip())
            timeout = float(self.client_timeout_var.get().strip())
            result = self.client.query(host, port, timeout)
            self.state.client.host = host
            self.state.client.port = port
            self.state.client.timeout_seconds = timeout
            self.client_result_var.set(self._format_client_result(result))
            self.client_tree.insert(
                "",
                0,
                values=(
                    result["target"],
                    "是",
                    self._format_datetime_for_display(result["server_time_utc"]),
                    f"{result['delta_seconds']:.6f}",
                    f"{result['rtt_ms']:.3f}",
                    self._format_response_summary(result),
                ),
            )
            self.refresh_logs()
            self.save_current_state(show_message=False)
        except Exception as exc:  # noqa: BLE001
            self.logs.add("client_test", "client_query_failed", target=self.client_host_var.get().strip(), success=False, error=str(exc))
            messagebox.showerror("客户端测试失败", str(exc))

    def run_local_query(self) -> None:
        host = self.server.endpoint[0] if self.server.is_running else "127.0.0.1"
        if host == "0.0.0.0":
            host = "127.0.0.1"
        self.client_host_var.set(host)
        if self.server.endpoint[1]:
            self.client_port_var.set(str(self.server.endpoint[1]))
        self.run_client_query()

    def refresh_logs(self) -> None:
        self._clear_tree(self.service_log_tree)
        self._clear_tree(self.client_log_tree)
        service_entries = self.logs.list_entries("service_request")
        client_entries = self.logs.list_entries("client_test")
        for entry in reversed(service_entries):
            self.service_log_tree.insert(
                "",
                0,
                values=(
                    self._format_datetime_for_display(entry.timestamp),
                    entry.details.get("client_ip", ""),
                    entry.details.get("client_port", ""),
                    entry.details.get("returned_time", ""),
                    entry.details.get("time_mode", ""),
                    "是" if entry.details.get("success") else "否",
                    entry.message,
                ),
            )
        for entry in reversed(client_entries):
            self.client_log_tree.insert(
                "",
                0,
                values=(
                    self._format_datetime_for_display(entry.timestamp),
                    entry.details.get("target", ""),
                    entry.details.get("server_time", ""),
                    entry.details.get("delta_seconds", ""),
                    entry.details.get("rtt_ms", ""),
                    "是" if entry.details.get("success") else "否",
                    entry.message,
                ),
            )

    def export_service_logs(self) -> None:
        self._export_logs("service_request", SERVER_LOG_FILE_NAME)

    def export_client_logs(self) -> None:
        self._export_logs("client_test", CLIENT_LOG_FILE_NAME)

    def _export_logs(self, category: str, default_name: str) -> None:
        initial_dir = self.state.paths.storage_dir if self.state.paths else default_program_storage_dir()
        path = filedialog.asksaveasfilename(
            title="导出日志",
            initialdir=str(initial_dir),
            initialfile=f"{DEFAULT_LOG_EXPORT_PREFIX}_{default_name}",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not path:
            return
        self.logs.export_csv(Path(path), self.logs.list_entries(category))
        self.server_status_var.set(f"日志已导出: {path}")

    def choose_storage_dir(self) -> None:
        current = self.storage_dir_var.get().strip() or str(default_program_storage_dir())
        selected = filedialog.askdirectory(initialdir=current, title="选择配置与日志目录")
        if selected:
            self._update_paths(Path(selected))

    def use_program_storage(self) -> None:
        self._update_paths(default_program_storage_dir())

    def use_user_storage(self) -> None:
        self._update_paths(default_user_storage_dir())

    def save_current_state(self, show_message: bool = True) -> None:
        try:
            self.state.server.host = self.host_var.get().strip() or "0.0.0.0"
            self.state.server.port = int(self.port_var.get().strip())
            self.state.server.auto_start = self.auto_start_var.get()
            self.state.client.host = self.client_host_var.get().strip()
            self.state.client.port = int(self.client_port_var.get().strip())
            self.state.client.timeout_seconds = float(self.client_timeout_var.get().strip())
            self.state.time_profile = self._collect_time_profile_from_ui()
            save_state(self.state)
            if show_message:
                messagebox.showinfo("保存成功", f"配置已保存到:\n{self.state.paths.config_path}")
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("保存失败", str(exc))

    def on_close(self) -> None:
        if self.server.is_running:
            self.server.stop()
        try:
            self.save_current_state(show_message=False)
        finally:
            self.root.destroy()

    def _collect_time_profile_from_ui(self) -> TimeProfile:
        base_mode = BaseTimeMode(self.base_mode_var.get())
        progress_mode = ProgressMode(self.progress_mode_var.get())
        timezone_display = TimezoneDisplay(self.timezone_var.get())
        offset_seconds = float(self.offset_var.get().strip() or "0")
        rate_multiplier = float(self.rate_var.get().strip() or "1")
        if rate_multiplier <= 0:
            raise ValueError("时间倍率必须大于 0")
        target_time_utc = None
        if base_mode == BaseTimeMode.FIXED:
            target_time_utc = self._parse_display_datetime(self.fixed_text_var.get().strip(), timezone_display)
        return TimeProfile(
            base_mode=base_mode,
            progress_mode=progress_mode,
            timezone_display=timezone_display,
            target_time_utc=target_time_utc,
            offset_seconds=offset_seconds,
            rate_multiplier=rate_multiplier,
        )

    def _parse_display_datetime(self, value: str, timezone_display: TimezoneDisplay) -> dt.datetime:
        if not value:
            raise ValueError("请输入自定义时间")
        parsed = None
        for fmt in (DATETIME_TEXT_FORMAT_MS, DATETIME_TEXT_FORMAT):
            try:
                parsed = dt.datetime.strptime(value, fmt)
                break
            except ValueError:
                continue
        if parsed is None:
            raise ValueError("时间格式错误，请使用 YYYY-MM-DD HH:MM:SS 或 YYYY-MM-DD HH:MM:SS.mmm")
        if timezone_display == TimezoneDisplay.UTC:
            return parsed.replace(tzinfo=dt.timezone.utc)
        local_tz = dt.datetime.now().astimezone().tzinfo or dt.timezone.utc
        return parsed.replace(tzinfo=local_tz).astimezone(dt.timezone.utc)

    def _format_profile_datetime(self, profile: TimeProfile) -> str:
        if profile.target_time_utc is None:
            current = dt.datetime.now().astimezone()
        else:
            current = profile.target_time_utc
            if profile.timezone_display == TimezoneDisplay.LOCAL:
                current = current.astimezone()
        return current.strftime(DATETIME_TEXT_FORMAT)

    def _format_time_of_day(self, profile: TimeProfile) -> str:
        if profile.target_time_utc is None:
            current = dt.datetime.now().astimezone()
        else:
            current = profile.target_time_utc
            if profile.timezone_display == TimezoneDisplay.LOCAL:
                current = current.astimezone()
        return current.strftime("%H:%M:%S")

    def _picker_date_from_profile(self) -> dt.date:
        if self.state.time_profile.target_time_utc is None:
            return dt.datetime.now().date()
        value = self.state.time_profile.target_time_utc
        if self.state.time_profile.timezone_display == TimezoneDisplay.LOCAL:
            value = value.astimezone()
        return value.date()

    def _refresh_ui_from_profile(self) -> None:
        current = self.time_engine.now_utc()
        self.current_service_time_var.set(self._format_datetime_for_display(current))
        self.service_mode_var.set(self.time_engine.describe())
        self.refresh_logs()
        while self.pending_status_messages:
            self.server_status_var.set(self.pending_status_messages.pop(0))

    def _schedule_periodic_refresh(self) -> None:
        self._refresh_ui_from_profile()
        self.root.after(1000, self._schedule_periodic_refresh)

    def _format_datetime_for_display(self, value: dt.datetime) -> str:
        timezone_display = TimezoneDisplay(self.timezone_var.get())
        if timezone_display == TimezoneDisplay.LOCAL:
            display_value = value.astimezone()
            suffix = "本地"
        else:
            display_value = value.astimezone(dt.timezone.utc)
            suffix = "UTC"
        return display_value.strftime(DATETIME_TEXT_FORMAT_MS)[:-3] + f" ({suffix})"

    def _format_client_result(self, result: dict[str, object]) -> str:
        return (
            f"目标: {result['target']} | 成功: 是 | 返回时间: "
            f"{self._format_datetime_for_display(result['server_time_utc'])} | "
            f"与本地差值: {result['delta_seconds']:.6f}s | 往返耗时: {result['rtt_ms']:.3f}ms | "
            f"摘要: {self._format_response_summary(result)}"
        )

    def _format_response_summary(self, result: dict[str, object]) -> str:
        return (
            f"reference={self._format_datetime_for_display(result['reference_time_utc'])}, "
            f"receive={self._format_datetime_for_display(result['receive_time_utc'])}"
        )

    def _queue_status_message(self, message: str) -> None:
        self.pending_status_messages.append(message)

    def _update_paths(self, storage_dir: Path) -> None:
        storage_dir = Path(storage_dir)
        self.state.paths = AppPaths(storage_dir=storage_dir, config_path=storage_dir / CONFIG_FILE_NAME)
        self.storage_dir_var.set(str(storage_dir))
        self.config_file_var.set(str(self.state.paths.config_path))

    def _is_program_storage_selected(self) -> bool:
        return self.state.paths is not None and self.state.paths.storage_dir == default_program_storage_dir()

    @staticmethod
    def _clear_tree(tree: ttk.Treeview) -> None:
        for item in tree.get_children():
            tree.delete(item)
