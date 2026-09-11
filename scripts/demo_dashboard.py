"""Synthetic dashboard only; never loads personal config, rollouts or Ollama.

Screenshots capture this program's own HWND, never the Codex UI or desktop.
"""
import argparse
import ctypes
import json
from pathlib import Path
import tempfile
import time
import tkinter as tk
from localagentbridge.config import Config
from localagentbridge.models import ModelProfile, AdaptiveConfig
from localagentbridge.telemetry import Store
from localagentbridge.dashboard import RegistryDashboard


def run(args):
    with tempfile.TemporaryDirectory(prefix='lab-demo-') as directory:
        config=Config(data_dir=Path(directory),otel_port=0,model_registry=[
            ModelProfile('demo-general:4b','dense',4,['general'],weight_gb=2.3,enabled=True,min_tier='Light'),
            ModelProfile('demo-coder:7b','dense',7,['coding'],weight_gb=4.4,enabled=True,min_tier='Medium'),
            ModelProfile('demo-reasoner:14b','dense',14,['coding','reasoning'],weight_gb=8.4,enabled=True,min_tier='Large'),
            ModelProfile('demo-retired:16b','moe',16,['coding'],active_parameters_b=2.4,weight_gb=8.3,
                         disabled_reason='Historical demonstration: 2 accepted / 4 corrected / 5 rejected.')],
            adaptive=AdaptiveConfig(memory_budget_gb=12))
        store=Store(config.data_dir)
        now=time.time()
        for i,(model,outcome) in enumerate([('demo-general:4b','accepted'),('demo-coder:7b','corrected'),('demo-reasoner:14b','accepted')]):
            store.usage(id=f'demo-{i}',session_id=f'demo-{i}',source='local',model=model,started=now-90+i,
                        input_tokens=1000,output_tokens=200,total_tokens=1200,duration=30,generation_seconds=20,
                        source_bytes=10000,output_bytes=1800,logical_id=f'task-{i}',tool='review_diff')
            store.report([dict(request_id=f'demo-{i}',outcome=outcome)])
            store.route_result(f'task-{i}',10000,2200,False,'local_result_requires_verification')
            store.route_event(f'task-{i}',None,model,'smallest_capable','Large',tool='review_diff',role='coding',selection_reason='Demonstration selection facts; no inference performed.')
        store.usage(id='codex-demo',session_id='codex-demo',source='rollout',model='Codex demo model',started=now-600,
                    input_tokens=10000,cached_input_tokens=7000,output_tokens=2000,reasoning_output_tokens=800,total_tokens=12000)
        store.activity('codex-demo','rollout','codex-demo','Codex demo model',now-600,now-100,status='done')
        store.activity('active-demo','local','active-demo','demo-reasoner:14b',now-42,now,status='generating',
                       output_tokens=200,role='coding',tool='review_diff',route_cap='Large',escalated_from='demo-coder:7b',
                       escalation_reason='contradictory_evidence',selection_reason='Role coding; Large cap; explicit reviewed follow-up; smallest remaining eligible strength.')
        root=tk.Tk()
        root.tk.call('tk','scaling',args.scale*1.3333)
        ui=RegistryDashboard(root,config,store)
        root.title('LocalAgentBridge · DEMO DATA')
        ui.poll_inventory=lambda:None
        ui.installed={p.name:{} for p in config.model_registry}
        ui.set_cap('Large')
        ui.show(manual=True)
        ui.refresh()
        root.update()
        if args.screenshots:
            from PIL import ImageGrab
            output=Path(args.screenshots)
            output.mkdir(parents=True,exist_ok=True)
            hwnd=ctypes.windll.user32.GetParent(root.winfo_id())
            for tab,name in [(0,'overview'),(1,'models'),(2,'activity'),(3,'settings')]:
                ui.tabs.select(tab)
                ui.model_choice.set('demo-reasoner:14b')
                ui.refresh_card()
                root.update()
                ImageGrab.grab(window=hwnd).save(output/f'{name}-{int(args.scale*100)}.png')
                if name=='models':
                    ui.card.yview(ui.card.search('Reviewed results:', '1.0'))
                    root.update()
                    ImageGrab.grab(window=hwnd).save(output/f'quality-{int(args.scale*100)}.png')
                    ui.card.yview_moveto(1)
                    root.update()
                    ImageGrab.grab(window=hwnd).save(output/f'quality-compression-{int(args.scale*100)}.png')
        if args.measure:
            import psutil
            process=psutil.Process()
            ui.hide()
            # Keep normal polling enabled; demonstration avoids production history.
            before=time.monotonic()
            cpu=process.cpu_times()
            def finish():
                after=process.cpu_times()
                seconds=time.monotonic()-before
                value=dict(seconds=seconds,cpu_seconds=after.user+after.system-cpu.user-cpu.system,
                           rss_mib=process.memory_info().rss/2**20,
                           note='Synthetic widget, polling every 2s; no collector, model or screen scraping.')
                value['one_core_cpu_percent']=value['cpu_seconds']/seconds*100
                Path(args.measure).write_text(json.dumps(value,indent=2))
                root.quit()
            root.after(20000,finish)
            root.mainloop()
        elif not args.screenshots:
            root.mainloop()
        ui.closed=True
        root.destroy()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--screenshots')
    parser.add_argument('--scale',type=float,default=1)
    parser.add_argument('--measure')
    run(parser.parse_args())
