"""Tkinter dashboard + native tray. No browser engine or web dashboard."""
import argparse
import queue
import time
import tkinter as tk
from tkinter import ttk
from .collector import Collector
from .config import load_config
from .telemetry import configure_logging
from .models import TIERS


def elapsed(seconds):
    seconds = max(0, int(seconds or 0))
    return f"{seconds // 3600:02}:{seconds // 60 % 60:02}:{seconds % 60:02}"


class Visibility:
    """Pure state for predictable tray/show/collapse behavior."""
    def __init__(self, delay):
        self.delay, self.had_activity, self.last_active, self.pinned = delay, False, None, False

    def update(self, active, now):
        action = None
        if active:
            if not self.had_activity:
                action = "show"
            self.last_active = now
        elif self.last_active is not None and now - self.last_active >= self.delay and not self.pinned:
            self.last_active = None
            action = "hide"
        self.had_activity = bool(active)
        return action


class LegacyDashboard:
    def __init__(self, root, config, store):
        self.root, self.config, self.store = root, config, store
        self.commands = queue.Queue()
        self.visibility = Visibility(config.collapse_seconds)
        self.closed = False
        self.root.title("LocalAgentBridge · Usage")
        self.root.geometry("620x320")
        if config.roles and not config.model_registry:
            self.root.geometry("850x340")
        self.root.minsize(500, 260)
        self.root.configure(background="#101820")
        self.root.protocol("WM_DELETE_WINDOW", self.hide)
        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure("Treeview", background="#17232e", foreground="#edf4fb", fieldbackground="#17232e", rowheight=30)
        style.configure("Treeview.Heading", background="#243747", foreground="#edf4fb", font=("Segoe UI", 10, "bold"))
        tk.Label(root, text="MODEL ACTIVITY", background="#101820", foreground="#9bd5c4",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=16, pady=(14, 6))
        self.cap = tk.StringVar(value=store.compute_cap(config.adaptive.default_cap))
        self.details_open = False
        if config.model_registry:
            controls = tk.Frame(root, background="#101820")
            controls.pack(fill="x", padx=16, pady=(0, 8))
            tk.Label(controls, text="LOCAL COMPUTE", background="#101820", foreground="#9bd5c4").pack(side="left", padx=(0, 10))
            for tier in TIERS:
                tk.Radiobutton(controls, text=tier, value=tier, variable=self.cap, command=self.set_cap,
                    background="#101820", foreground="#edf4fb", selectcolor="#243747").pack(side="left")
        self.status = tk.StringVar(value="Idle · waiting for model activity")
        tk.Label(root, textvariable=self.status, background="#101820", foreground="#edf4fb",
                 justify="left", wraplength=580, font=("Segoe UI", 10)).pack(anchor="w", padx=16, pady=(0, 10))
        self.table = ttk.Treeview(root, columns=("model", "time", "tokens"), show="headings", height=5)
        for key, title, width in (("model", "Model", 310), ("time", "Usage Time", 120), ("tokens", "Total Tokens Used", 150)):
            self.table.heading(key, text=title)
            self.table.column(key, width=width, anchor="w" if key == "model" else "e")
        if config.roles and not config.model_registry:
            self.table.configure(columns=("model", "time", "tokens", "calls", "compression"))
            for key, title, width in (("calls", "Calls", 65), ("compression", "Local compression*", 150)):
                self.table.heading(key, text=title)
                self.table.column(key, width=width, anchor="e")
        self.table.pack(fill="both", expand=True, padx=16)
        self.details = ttk.Frame(root)
        self.detail_table = ttk.Treeview(self.details, columns=("model", "arch", "params", "quant", "calls", "tokens", "latency", "speed", "grades", "compression"), show="headings", height=6)
        headings = (("model", "Model", 280), ("arch", "Architecture", 85), ("params", "Active / total B", 105),
                    ("quant", "Quantization", 100), ("calls", "Calls", 55), ("tokens", "Tokens", 95),
                    ("latency", "Avg latency", 85), ("speed", "Gen tok/s", 80), ("grades", "A / C / R*", 95),
                    ("compression", "Local compression*", 125))
        for key, title, width in headings:
            self.detail_table.heading(key, text=title)
            self.detail_table.column(key, width=width, stretch=False)
        scroll = ttk.Scrollbar(self.details, orient="horizontal", command=self.detail_table.xview)
        self.detail_table.configure(xscrollcommand=scroll.set)
        self.detail_table.pack(fill="both", expand=True)
        scroll.pack(fill="x")
        if config.roles:
            tk.Label(root, text="* A/C/R = reviewed outcomes. Byte reduction is not measured cloud-token savings.",
                     background="#101820", foreground="#aab9c6", font=("Segoe UI", 9)).pack(anchor="w", padx=16, pady=(5, 0))
        footer = tk.Frame(root, background="#101820")
        footer.pack(fill="x", padx=16, pady=10)
        self.pin = tk.BooleanVar(value=False)
        tk.Checkbutton(footer, text="Keep open", variable=self.pin, command=self.set_pin,
                       background="#101820", foreground="#aab9c6", selectcolor="#243747").pack(side="left")
        tk.Button(footer, text="Hide to tray", command=self.hide).pack(side="right")
        if config.model_registry:
            tk.Button(footer, text="Model details", command=self.toggle_details).pack(side="right", padx=8)
        self.root.withdraw()

    def set_cap(self, value=None):
        self.cap.set(self.store.compute_cap(value=value or self.cap.get()))

    def toggle_details(self):
        self.details_open = not self.details_open
        if self.details_open:
            self.details.pack(fill="both", expand=True, padx=16, pady=8, after=self.table)
            self.root.geometry("920x580")
        else:
            self.details.pack_forget()
            self.root.geometry("620x340")

    def refresh_details(self, totals):
        rows = {r['model']:r for r in totals if r['kind']=='Local'}
        for profile in self.config.model_registry:
            metrics = self.store.model_metrics(profile.name)
            row = rows.get(profile.name, {})
            active = f"{profile.active_parameters_b:g}" if profile.active_parameters_b is not None else "?"
            compression, speed, latency = row.get('compression_estimate'), metrics['tokens_per_second'], metrics['average_latency']
            values = (profile.name + (" [disabled]" if not profile.enabled else ""), profile.architecture,
                      f"{active} / {profile.total_parameters_b:g}", profile.quantization,
                      metrics['calls'], "unavailable" if row and row.get('total_tokens') is None else f"{row.get('total_tokens') or 0:,}", f"{latency:.1f}s" if latency is not None else "—",
                      f"{speed:.1f}" if speed is not None else "—",
                      " / ".join(str(metrics[k] or 0) for k in ('accepted','corrected','rejected')),
                      f"{compression:.0%}" if compression is not None else "—")
            if self.detail_table.exists(profile.name):
                self.detail_table.item(profile.name, values=values)
            else:
                self.detail_table.insert("", "end", iid=profile.name, values=values)

    def set_pin(self):
        self.visibility.pinned = self.pin.get()

    def show(self, manual=False):
        if manual:
            self.pin.set(True)
            self.set_pin()
        self.root.deiconify()
        self.root.lift()  # Do not steal keyboard focus.

    def hide(self):
        self.root.withdraw()
        self.pin.set(False)
        self.set_pin()

    def refresh(self):
        while not self.commands.empty():
            command = self.commands.get_nowait()
            if command == "quit":
                self.closed = True
                self.root.quit()
                return
            if command.startswith("cap:"):
                self.set_cap(command[4:])
                continue
            self.show(manual=True)
        try:
            self.cap.set(self.store.compute_cap(self.config.adaptive.default_cap))
            active = self.store.active(self.config.stale_seconds)
            lines = []
            now = time.time()
            for row in active:
                local = row["source"] == "local"
                kind = "Local" if local else "Codex"
                duration = now - row["started"]
                tokens = row["output_tokens"]
                suffix = "loading / evaluating prompt" if row["status"] == "loading" else "active"
                if tokens is not None:
                    suffix = f"{'~' if local else ''}{tokens:,} output tokens"
                    if local and duration > 0:
                        suffix += f" · ~{tokens / duration:.1f} tok/s"
                line = f"{kind} · {row['model']} · {elapsed(duration)} · {suffix}"
                if row.get('role'):
                    line += f" · Role: {row['role']}"
                if row.get('escalated_from'):
                    line += f"\nEscalated from: {row['escalated_from']} · {row.get('escalation_reason') or 'requested'}"
                elif row.get('escalation_reason'):
                    line += f" · {row['escalation_reason']}"
                lines.append(line)
            self.status.set("\n".join(lines[:3]) or "Idle · totals reflect collected local history")
            totals = self.store.totals()
            wanted = set()
            for row in totals:
                key = row["kind"] + ":" + row["model"]
                wanted.add(key)
                values = (f"{row['kind']} · {row['model']}", elapsed(row["duration"]) if row["duration"] is not None else "unavailable",
                          f"{row['total_tokens']:,}" if row["total_tokens"] is not None else "unavailable")
                if self.config.roles and not self.config.model_registry:
                    compression = row.get("compression_estimate")
                    values += (f"{row['requests']:,}", f"{compression:.0%}" if compression is not None else "—")
                if self.table.exists(key):
                    self.table.item(key, values=values)
                else:
                    self.table.insert("", "end", iid=key, values=values)
            for key in self.table.get_children():
                if key not in wanted:
                    self.table.delete(key)
            # No extra registry queries while collapsed or idle in the tray.
            if self.details_open:
                self.refresh_details(totals)
            action = self.visibility.update(active, time.monotonic())
            if action == "show":
                self.show()
            elif action == "hide":
                self.hide()
        except Exception:
            self.status.set("Usage database temporarily unavailable; retrying")
        if not self.closed:
            self.root.after(int(self.config.poll_seconds * 1000), self.refresh)


def Dashboard(root, config, store):
    if config.model_registry:
        from .dashboard import RegistryDashboard
        return RegistryDashboard(root, config, store)
    return LegacyDashboard(root, config, store)


def run_widget(config):
    import pystray
    from PIL import Image, ImageDraw
    collector = Collector(config)
    collector.start()
    root = tk.Tk()
    dashboard = Dashboard(root, config, collector.store)
    icon_image = Image.new("RGB", (64, 64), "#101820")
    draw = ImageDraw.Draw(icon_image)
    draw.rounded_rectangle((8, 8, 56, 56), radius=12, fill="#76d9b0")
    draw.rectangle((20, 19, 26, 44), fill="#101820")
    draw.rectangle((26, 38, 44, 44), fill="#101820")
    items = [pystray.MenuItem("Show usage", lambda: dashboard.commands.put("show"), default=True)]
    if config.model_registry:
        def cap_item(tier):
            return pystray.MenuItem(tier, lambda: dashboard.commands.put("cap:"+tier), radio=True,
                checked=lambda item: collector.store.compute_cap(config.adaptive.default_cap)==tier)
        items.append(pystray.MenuItem("Local compute cap", pystray.Menu(*(cap_item(t) for t in TIERS))))
    items.append(pystray.MenuItem("Quit", lambda: dashboard.commands.put("quit")))
    icon = pystray.Icon("LocalAgentBridge", icon_image, "LocalAgentBridge · Usage", menu=pystray.Menu(*items))
    try:
        icon.run_detached()
        dashboard.refresh()
        root.mainloop()
    finally:
        icon.stop()
        collector.close()
        root.destroy()


def main():
    parser = argparse.ArgumentParser(description="LocalAgentBridge Windows tray monitor")
    parser.add_argument("--config")
    args = parser.parse_args()
    config = load_config(args.config)
    configure_logging(config)
    run_widget(config)
