"""Exercise actual Windows Tk widgets and tray creation; no screenshot scraping."""
import os
import time
import pytest


@pytest.mark.skipif(os.name != "nt", reason="Windows native UI smoke")
@pytest.mark.parametrize("with_roles", [False, True], ids=["v01", "v02"])
def test_native_dashboard_and_tray(tmp_path, with_roles):
    import tkinter as tk
    import pystray
    from PIL import Image
    from localagentbridge.config import Config
    from localagentbridge.telemetry import Store
    from localagentbridge.widget import Dashboard
    root = tk.Tk()
    config = Config(data_dir=tmp_path, otel_port=0, roles={"general": "qwen3:4b", "coding": "qwen2.5-coder:7b", "reasoning": "phi4-mini"} if with_roles else {})
    store = Store(tmp_path)
    now = time.time()
    store.usage(id="test", source="local", session_id="test", model="qwen-test", started=now,
                input_tokens=100, output_tokens=20, total_tokens=120, duration=2, source_bytes=1000, output_bytes=200)
    store.activity("test", "local", "test", "qwen-test", now, now, "generating", output_tokens=20)
    dashboard = Dashboard(root, config, store)
    # Keep test window withdrawn; check its actual widget state.
    dashboard.visibility.had_activity = True
    icon = pystray.Icon("LocalAgentBridgeTest", Image.new("RGB", (16, 16), "green"), "LocalAgentBridge test")
    try:
        icon.run_detached()
        dashboard.refresh()
        root.update_idletasks()
        expected = ("model", "time", "tokens", "calls", "compression") if with_roles else ("model", "time", "tokens")
        assert tuple(dashboard.table["columns"]) == expected
        row = dashboard.table.item("Local:qwen-test")["values"]
        assert str(row[2]) == "120"
        if with_roles:
            assert str(row[3]) == "1" and row[4] == "80%"
        assert "~20 output tokens" in dashboard.status.get()
        assert root.state() == "withdrawn"
        dashboard.commands.put("show")
        dashboard.refresh()
        root.update_idletasks()
        assert dashboard.visibility.pinned
        dashboard.hide()
        assert root.state() == "withdrawn"
    finally:
        dashboard.closed = True
        icon.stop()
        root.destroy()
