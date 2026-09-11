"""Registry dashboard: native tabs and wrapping detail cards; no horizontal tables."""
import asyncio
import queue
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox
from .dashboard_state import (snapshot, tier_text, activity_text, model_text,
                              compression_text, COMPRESSION_HELP, QUALITY_HELP, CODEX_HELP)
from .models import TIERS, model_tier
from .routing import inventory, canonical


class RegistryDashboard:
    def __init__(self, root, config, store):
        from .widget import Visibility
        self.root, self.config, self.store = root, config, store
        self.commands = queue.Queue()
        self.visibility = Visibility(config.collapse_seconds)
        self.closed = False
        self.installed, self.rows, self.totals = None, [], []
        self.inventory_updates = queue.Queue()
        self.inventory_running, self.inventory_at = False, 0
        self.after_id = None
        self.details_open = False
        self.active_rows = []
        self.visible = False
        settings = store.checkpoint('widget-settings')
        defaults = dict(start_in_tray=True, keep_open=False, always_on_top=False,
                        popup_activity=False, popup_escalation=False, popup_failure=False)
        self.options = {k: tk.BooleanVar(root, value=settings.get(k, v)) for k, v in defaults.items()}
        self.pin = self.options['keep_open']
        self.delay = tk.IntVar(root, value=settings.get('collapse_seconds', config.collapse_seconds))
        self.cap = tk.StringVar(root, value=store.compute_cap(config.adaptive.default_cap))
        self.status, self.eligible_text, self.feedback = (tk.StringVar(root) for _ in range(3))
        root.title('LocalAgentBridge · Usage')
        # Font-relative initial geometry adapts to Tk/Windows DPI scaling.
        unit = max(1, float(root.tk.call('tk', 'scaling')) / 1.3333)
        width, height = min(int(700*unit), root.winfo_screenwidth()-60), min(int(660*unit), root.winfo_screenheight()-90)
        root.geometry(f'{width}x{height}')
        root.minsize(min(540, width), min(460, height))
        root.protocol('WM_DELETE_WINDOW', self.hide)
        shell = ttk.Frame(root, padding=12)
        shell.pack(fill='both', expand=True)
        controls = ttk.Frame(shell)
        controls.pack(fill='x')
        ttk.Label(controls, text='Local compute').pack(side='left', padx=(0, 10))
        for tier in TIERS:
            button = ttk.Radiobutton(controls, text=tier, value=tier, variable=self.cap, command=self.set_cap)
            button.pack(side='left')
            button.bind('<Button-3>', lambda event, t=tier: self.tier_help(t))
        ttk.Button(controls, text='Tier help', command=lambda: self.tier_help(self.cap.get())).pack(side='right')
        self.eligibility_label = ttk.Label(shell, textvariable=self.eligible_text, justify='left', wraplength=640)
        self.eligibility_label.pack(fill='x', pady=(8, 4))
        self.feedback_label = ttk.Label(shell, textvariable=self.feedback, foreground='#236546', wraplength=640)
        self.feedback_label.pack(fill='x')
        current = ttk.LabelFrame(shell, text='Current activity', padding=8)
        current.pack(fill='x', pady=6)
        self.activity_label = ttk.Label(current, textvariable=self.status, wraplength=620, justify='left')
        self.activity_label.pack(fill='x')
        ttk.Button(current, text='Why this model?', command=self.why_model).pack(anchor='e')
        self.tabs = ttk.Notebook(shell)
        self.tabs.pack(fill='both', expand=True)
        overview, models, activity, settings_tab = (ttk.Frame(self.tabs, padding=6) for _ in range(4))
        for frame, name in zip((overview, models, activity, settings_tab), ('Overview', 'Models', 'Activity', 'Settings')):
            self.tabs.add(frame, text=name)
        self.table = ttk.Treeview(overview, columns=('model', 'time', 'tokens'), show='headings', height=5)
        for key, title, width in [('model', 'Model', 290), ('time', 'Usage Time', 100), ('tokens', 'Total Tokens Used', 130)]:
            self.table.heading(key, text=title)
            self.table.column(key, width=width, minwidth=65, stretch=True, anchor='w' if key=='model' else 'e')
        scrollbar = ttk.Scrollbar(overview, command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        self.table.pack(fill='both', expand=True)
        ttk.Label(overview, text='● active   ○ available   ◌ unavailable / unknown   × disabled\nCap and task exclusions appear in Models.', wraplength=620).pack(anchor='w', pady=4)
        self.table.bind('<<TreeviewSelect>>', self.select_overview)
        self.model_choice = ttk.Combobox(models, state='readonly', values=[p.name for p in config.model_registry])
        self.model_choice.pack(fill='x')
        self.model_choice.bind('<<ComboboxSelected>>', lambda event: self.refresh_card())
        self.card = self.text_area(models)
        self.history = self.text_area(activity)
        for name, label in [('start_in_tray', 'Start in tray'), ('keep_open', 'Keep widget open'),
                            ('always_on_top', 'Always on top'), ('popup_activity', 'Popup on local activity'),
                            ('popup_escalation', 'Popup on escalation'), ('popup_failure', 'Popup on model failure')]:
            ttk.Checkbutton(settings_tab, text=label, variable=self.options[name], command=self.save_settings).pack(anchor='w')
        delay_row = ttk.Frame(settings_tab)
        delay_row.pack(fill='x', pady=4)
        ttk.Label(delay_row, text='Auto-hide delay (seconds)').pack(side='left')
        ttk.Spinbox(delay_row, from_=0, to=3600, width=6, textvariable=self.delay, command=self.save_settings).pack(side='left', padx=8)
        ttk.Button(delay_row, text='Apply', command=self.save_settings).pack(side='left')
        ttk.Button(settings_tab, text='Compression and quality help', command=self.metrics_help).pack(anchor='w', pady=4)
        ttk.Button(settings_tab, text='Codex token accounting', command=lambda: messagebox.showinfo('Codex accounting', CODEX_HELP, parent=root)).pack(anchor='w')
        ttk.Button(shell, text='Hide to tray', command=self.hide).pack(anchor='e', pady=(6, 0))
        root.bind('<Configure>', self.resize)
        self.apply_settings()
        self.update_eligibility()
        if self.options['start_in_tray'].get():
            root.withdraw()
        else:
            self.visible = True

    @staticmethod
    def text_area(parent):
        frame = ttk.Frame(parent)
        frame.pack(fill='both', expand=True, pady=6)
        text = tk.Text(frame, wrap='word', height=6, width=1, relief='flat', font=('Segoe UI', 10), padx=8, pady=8)
        bar = ttk.Scrollbar(frame, command=text.yview)
        text.configure(yscrollcommand=bar.set, state='disabled')
        bar.pack(side='right', fill='y')
        text.pack(fill='both', expand=True)
        return text

    @staticmethod
    def write(widget, content):
        if widget.get('1.0', 'end-1c') == content:
            return
        position = widget.yview()[0]
        widget.configure(state='normal')
        widget.delete('1.0', 'end')
        widget.insert('1.0', content)
        widget.configure(state='disabled')
        widget.yview_moveto(position)

    def resize(self, event):
        if event.widget == self.root:
            for label in (self.eligibility_label, self.activity_label, self.feedback_label):
                label.configure(wraplength=max(260, event.width-65))

    def update_eligibility(self):
        self.rows = snapshot(self.config, self.store, self.cap.get(), self.installed)
        active = {r['model'] for r in self.active_rows if r['source']=='local'}
        for row in self.rows:
            row['active'] = row['profile'].name in active
        self.eligible_text.set(tier_text(self.rows, self.cap.get(), self.config.adaptive))
        if hasattr(self, 'model_choice'):
            registered = {canonical(p.name) for p in self.config.model_registry}
            extras = sorted(name for name in (self.installed or {}) if name not in registered)
            self.model_choice.configure(values=[p.name for p in self.config.model_registry]+extras)
        self.refresh_card()

    def set_cap(self, value=None):
        before = {r['profile'].name for r in self.rows if r['eligible']}
        self.cap.set(self.store.compute_cap(value=value or self.cap.get()))
        self.update_eligibility()
        added = {r['profile'].name for r in self.rows if r['eligible']} - before
        self.feedback.set(f'Local compute changed to {self.cap.get().upper()}.' + (' Now eligible: '+', '.join(sorted(added)) if added else ' Eligibility refreshed.'))

    def tier_help(self, tier):
        rows = snapshot(self.config, self.store, tier, self.installed)
        text = tier_text(rows, tier, self.config.adaptive) + '\n\nAt most the configured attempt limit. Fixed consensus uses distinct role defaults and still obeys the cap.\n\n'
        text += '\n'.join(f"{r['profile'].name}: " + ('eligible for '+', '.join(r['tools']) if r['eligible'] else '; '.join(r['reasons'])) for r in rows)
        messagebox.showinfo(f'{tier} compute policy', text, parent=self.root)

    def why_model(self):
        facts = [r.get('selection_reason') or 'Fixed model or older record; selection facts unavailable.' for r in self.active_rows if r['source']=='local']
        if not facts:
            events = self.store.recent_routes(1)
            facts = [events[0].get('selection_reason') or events[0]['reason']] if events else ['No routing activity recorded yet.']
        messagebox.showinfo('Routing facts', '\n\n'.join(facts), parent=self.root)

    def metrics_help(self):
        messagebox.showinfo('Reading the metrics', COMPRESSION_HELP+'\n\n'+QUALITY_HELP+'\n\n'+compression_text(self.store.compression()), parent=self.root)

    def refresh_card(self):
        if not hasattr(self, 'model_choice'):
            return
        name = self.model_choice.get()
        if not name and self.rows:
            self.model_choice.set(self.rows[0]['profile'].name)
            name = self.model_choice.get()
        row = next((r for r in self.rows if r['profile'].name==name), None)
        if row:
            total = next((r for r in self.totals if r['kind']=='Local' and r['model']==name), {})
            self.write(self.card, model_text(row, total, self.store.compression(name)))
        elif name in (self.installed or {}):
            info = self.installed[name]
            remote = bool(info.get('remote_host') or info.get('remote_model'))
            details = info.get('details', {})
            self.write(self.card, f"{name}\n\nInstalled in Ollama: yes · Registered: no\nEnabled in bridge: no · Eligible: no\n\n"+
                ('Remote model: unsupported; only local weights may be used.' if remote else 'Add an explicit model_registry entry and supported roles to permit routing.')+
                f"\n\nOllama metadata: {details.get('parameter_size','unknown')} · {details.get('quantization_level','unknown')}\n"+
                f"Weight bytes: {info.get('size','unavailable')}\nArchitecture/active parameters: not registered; do not infer MoE fit from total size.")

    def select_overview(self, event=None):
        selected = self.table.selection()
        if not selected:
            return
        kind, name = selected[0].split(':', 1)
        if kind=='Local' and (any(p.name==name for p in self.config.model_registry) or name in (self.installed or {})):
            self.model_choice.set(name)
            self.refresh_card()
            self.tabs.select(1)
        elif kind=='Codex':
            row = next(r for r in self.totals if r['kind']==kind and r['model']==name)
            fields = '\n'.join(f"{k.replace('_', ' ').title()}: {row.get(k) if row.get(k) is not None else 'unavailable'}" for k in ('input_tokens','cached_input_tokens','output_tokens','reasoning_output_tokens','total_tokens'))
            messagebox.showinfo('CLOUD / CODEX · '+name, fields+'\n\n'+CODEX_HELP, parent=self.root)

    def toggle_details(self):
        self.details_open = not self.details_open
        self.tabs.select(1 if self.details_open else 0)
        self.refresh_card()

    def apply_settings(self):
        self.visibility.pinned = self.pin.get()
        self.visibility.delay = self.delay.get()
        self.root.attributes('-topmost', self.options['always_on_top'].get())

    def save_settings(self):
        try:
            delay = self.delay.get()
            if not 0 <= delay <= 3600:
                raise ValueError()
        except (ValueError, tk.TclError):
            self.feedback.set('Auto-hide delay must be 0–3600 seconds.')
            return
        self.apply_settings()
        self.store.checkpoint('widget-settings', {k:v.get() for k,v in self.options.items()} | {'collapse_seconds':delay})

    def set_pin(self):
        self.save_settings()

    def show(self, manual=False):
        self.visible = True
        if manual:
            self.pin.set(True)
            self.save_settings()
        # Windows ShowWindow(SW_SHOWNOACTIVATE) avoids keyboard focus theft.
        if not manual and self.root.tk.call('tk', 'windowingsystem') == 'win32':
            import ctypes
            self.root.update_idletasks()
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            ctypes.windll.user32.ShowWindow(hwnd, 4)
        else:
            self.root.deiconify()

    def hide(self):
        self.visible = False
        self.root.withdraw()
        self.pin.set(False)
        self.save_settings()

    def poll_inventory(self):
        if self.inventory_running or time.monotonic()-self.inventory_at < self.config.discover_seconds:
            return
        self.inventory_running = True
        self.inventory_at = time.monotonic()
        config, updates = self.config, self.inventory_updates
        def read():
            try:
                result = asyncio.run(inventory(config))
            except Exception:
                result = None
            updates.put(result)
        threading.Thread(target=read, daemon=True, name='lab-inventory').start()

    def refresh(self):
        from .widget import elapsed
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        while not self.commands.empty():
            command = self.commands.get_nowait()
            if command=='quit':
                self.closed = True
                self.root.quit()
                return
            if command.startswith('cap:'):
                self.set_cap(command[4:])
            else:
                self.show(manual=True)
        try:
            self.poll_inventory()
            while not self.inventory_updates.empty():
                self.installed = self.inventory_updates.get_nowait()
                self.inventory_running = False
                self.update_eligibility()
            cap = self.store.compute_cap(self.config.adaptive.default_cap)
            if cap != self.cap.get():
                self.cap.set(cap)
                self.update_eligibility()
            self.active_rows = self.store.active(self.config.stale_seconds)
            for row in self.active_rows:
                profile = next((p for p in self.config.model_registry if p.name==row['model']), None)
                if profile:
                    row['model_tier'] = model_tier(profile, self.config.adaptive)
            local = [r for r in self.active_rows if r['source']=='local']
            display = sorted(self.active_rows, key=lambda r: (r['source']!='local', r['started']))
            self.status.set('\n'.join(activity_text(r, time.time()) for r in display[:2]) or 'Idle · all-time collected usage')
            popup = local and (self.options['popup_activity'].get() or (self.options['popup_escalation'].get() and any(r.get('escalated_from') for r in local)))
            action = self.visibility.update(bool(popup), time.monotonic())
            events = self.store.recent_routes()
            latest = self.store.latest_local_failure()
            if hasattr(self, 'last_failure') and latest and latest != self.last_failure and self.options['popup_failure'].get():
                action = 'show'
                self.visibility.last_active = time.monotonic()
            self.last_failure = latest
            if action=='show':
                self.show()
            elif action=='hide':
                self.hide()
            # Metadata inventory is infrequent; large aggregate queries pause in tray.
            if self.visible or not getattr(self, 'rendered', False):
                self.rendered = True
                self.totals = self.store.totals()
                self.update_eligibility()
                rows = {(r['kind'], r['model']):r for r in self.totals}
                for p in self.config.model_registry:
                    rows.setdefault(('Local', p.name), dict(kind='Local', model=p.name, duration=0, total_tokens=0))
                registered = {canonical(p.name) for p in self.config.model_registry}
                for name in self.installed or {}:
                    if name not in registered:
                        rows.setdefault(('Local', name), dict(kind='Local', model=name, duration=0, total_tokens=0))
                states = {r['profile'].name:r for r in self.rows}
                active_names = {('Local' if r['source']=='local' else 'Codex', r['model']) for r in self.active_rows}
                wanted = set()
                for (kind, name), r in sorted(rows.items()):
                    key = kind+':'+name
                    wanted.add(key)
                    state = states.get(name, {})
                    if not state and name in (self.installed or {}):
                        info = self.installed[name]
                        state = dict(installed=not bool(info.get('remote_host') or info.get('remote_model')))
                    marker = '●' if (kind, name) in active_names else '×' if kind=='Local' and state.get('enabled') is False else '◌' if kind=='Local' and state.get('installed') is not True else '○'
                    values = (f"{marker} {'LOCAL' if kind=='Local' else 'CODEX'} · {name}", elapsed(r['duration']) if r.get('duration') is not None else 'unavailable', f"{r['total_tokens']:,}" if r.get('total_tokens') is not None else 'unavailable')
                    if self.table.exists(key):
                        self.table.item(key, values=values)
                    else:
                        self.table.insert('', 'end', iid=key, values=values)
                for key in self.table.get_children():
                    if key not in wanted:
                        self.table.delete(key)
                lines = [f"{time.strftime('%H:%M:%S', time.localtime(r['created']))} · " +
                         (f"{r['previous_model']} → " if r['previous_model'] else '') +
                         f"{r['selected_model']} · {r['tool'] or 'handoff'} · {r['outcome'] or r['reason']}\n{r['selection_reason'] or r['reason']}" for r in events]
                self.write(self.history, '\n\n'.join(lines) or 'No routing events yet. Only metadata is retained here.')
        except Exception:
            self.status.set('Usage data temporarily unavailable; retrying')
        if not self.closed:
            self.after_id = self.root.after(int(self.config.poll_seconds*1000), self.refresh)
