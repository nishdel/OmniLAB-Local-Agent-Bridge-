"""Compact Tk view/controller client. Scheduling lives in the independent process."""
import asyncio
import json
import os
import queue
import threading
import tkinter as tk
from tkinter import ttk

from .selection import discover, select_model


def reported_total(rows, field):
    values = [row.get(field) for row in rows]
    return sum(values) if values and all(v is not None for v in values) else None


def display(value):
    return 'unavailable' if value is None else f'{value:,}'


def job_usage(job):
    reported = (job.get('result') or {}).get('usage')
    if reported is not None:
        return reported
    state = job.get('contract_state') or {}
    if (state.get('evidence') or {}).get('usage_incomplete'):
        return {}
    receipts = (state.get('evidence') or {}).get('usage')
    if isinstance(receipts, list):
        return {field: reported_total(receipts, field) for field in
                ('input_tokens','output_tokens','cached_input_tokens')}
    return {}


def presentation(snapshot, run_id=None):
    runs = snapshot['runs']
    run = next((r for r in runs if r['id']==run_id), runs[0] if runs else None)
    if not run:
        return dict(title='No companion runs',details='Create and submit a run with the companion CLI.',active=None,run=None)
    jobs = [j for j in snapshot['jobs'] if j['run_id']==run['id']]
    events = [e for e in snapshot['events'] if e['run_id']==run['id']]
    active = next((j for j in jobs if j['state']=='running'),None)
    queued = sum(j['state']=='queued' for j in jobs)
    completed = sum(j['state'] in ('succeeded','failed','cancelled','interrupted') for j in jobs)
    usage = [job_usage(j) for j in jobs]
    model = active['request']['selection']['name'] if active else (jobs[-1]['request']['selection']['name'] if jobs else 'unselected')
    selected_job = active or (jobs[-1] if jobs else None)
    if selected_job and selected_job.get('contract_state',{}).get('lane')=='codex_direct':
        model = 'Codex supervisor'
    end = run['finalized'] if run['finalized'] is not None else snapshot['now']
    elapsed = max(0,end-run['created'])
    state = 'local_generation' if active else 'local_queued' if queued else run['state']
    if active and active.get('contract_state'):
        cs = active['contract_state']
        state = 'verifying' if cs['verification_status']=='running' else cs['execution_status']
    if selected_job and selected_job.get('contract_state') and selected_job['contract_state']['lane']!='codex_direct':
        model = selected_job['contract_state']['backend'] + '/' + model
    title = (f"{active['task_key'] if active else run['id'][:8]}  |  {model}  |  {state}\n"
             f"Local in {display(reported_total(usage,'input_tokens'))} / out {display(reported_total(usage,'output_tokens'))}  |  "
             f"{elapsed:.0f}s total  |  {queued} queued / {completed} finished local  |  {'queue paused' if snapshot['paused'] else 'queue enabled'}")
    lines = [f"Run: {run['id']}",f"Repository: {run['repository']}",f"Base: {run['base_revision']}",
             f"Codex session: {run['session_id'] or 'not initialized'}",'Local completion requires a separate review and validation.']
    for job in jobs:
        finish = job['ended'] if job['ended'] is not None else snapshot['now']
        waiting = (job['started'] if job['started'] is not None else finish)-job['created']
        inference = finish-job['started'] if job['started'] is not None else None
        lines += ['',f"{job['task_key']}  |  {job['id']}  |  {job['state']}",
                  f"Model: {job['request']['selection']['name']} ({job['request']['selection'].get('digest') or 'digest unavailable'})",
                  f"Queue wait: {waiting:.1f}s  |  local execution: {'unavailable' if inference is None else f'{inference:.1f}s'}"]
        if job.get('contract_state'):
            cs = job['contract_state']
            contract = job['request']['contract']
            children = [j for j in jobs if j.get('request',{}).get('contract',{}).get('parent_id')==contract['task_id']]
            finished = sum(j['state'] in ('succeeded','failed','cancelled','interrupted') for j in children)
            lines += [f"Lane: {cs['lane']}  |  backend: {cs['backend']}  |  role: {job['request']['role']}",
                      'Skills: ' + ', '.join(s['id']+'@'+s['version'] for s in job['request']['skills']),
                      'Routing: ' + job['request']['routing']['reason'],
                      f"Execution: {cs['execution_status']}  |  verification: {cs['verification_status']}  |  review: {cs['review_status']}  |  integration: {cs['integration_status']}",
                      f"Parent: {contract['parent_id'] or 'none'}  |  children finished: {finished}/{len(children)}",
                      'Dependencies: ' + ', '.join(contract['dependencies']),
                      'Candidate: ' + (cs['candidate_hash'] or 'unavailable')]
            actual_usage = job_usage(job)
            lines.append(f"Local reported tokens: in {display(actual_usage.get('input_tokens'))} / out {display(actual_usage.get('output_tokens'))}")
            for measurement in job.get('measurements', []):
                lines.append('Measurement ('+measurement['kind']+'): '+measurement['phase']+' '+json.dumps(measurement['metrics']))
            if cs['lane']=='codex_direct':
                lines.append('Model above is requested only; this lane makes no local inference call.')
        result = job.get('result') or {}
        workflow = result.get('answer',{}).get('workflow')
        if workflow:
            budget = workflow['budget']
            lines += [f"Workflow: {workflow['run_id']}  |  {workflow['state']}  |  next: {workflow['next_stage']}",
                      f"Profile: {workflow['project_profile']}  |  version: {workflow['version']}  |  path: {workflow.get('delegation',{}).get('path','explicit workflow')}",
                      f"Budget: {budget['attempts']}/{budget['limits']['max_attempts']} attempts; {budget['reserved_tokens']} reserved tokens; {budget['seconds']}s charged",
                      'Advance with companion workflow-next; trusted decisions use workflow-checkpoint.']
        if job['request'].get('model_pins'):
            lines.append('Pinned routing inventory: '+', '.join(job['request']['model_pins']))
        event = next((e for e in events if e['job_id']==job['id']),None)
        if event:
            review = (event['review_ended']-event['review_started']) if event['review_ended'] is not None and event['review_started'] is not None else None
            lines += [f"Review: {event['state']}  |  {event['decision'] or event['reason'] or 'pending'}",
                      f"Review elapsed: {'unavailable' if review is None else f'{review:.1f}s'}  |  event: {event['id']}",
                      'Codex reported usage: '+(event['review_usage'] or 'unavailable')]
        if job.get('error'):
            lines.append('Error: '+job['error'])
        if job.get('result'):
            lines.append(json.dumps(job['result']['answer'],indent=2,ensure_ascii=False))
    if run.get('summary'):
        lines.append('\nFinal report: '+run['summary'])
    if snapshot.get('inference_reservation'):
        lines.append('Inference reservation: ' + snapshot['inference_reservation']['state'])
    return dict(title=title,details='\n'.join(lines),active=active,run=run)


class CompanionDock:
    def __init__(self, root, config, store):
        self.root,self.config,self.store=root,config,store
        self.closed=False
        self.commands=queue.Queue()
        self.inventory=[]
        self.inventory_running=False
        self.current=None
        self.expanded=False
        self.pinned=tk.BooleanVar(root,value=bool(store.setting('dock_pinned')))
        self.message=tk.StringVar(root)
        self.status=tk.StringVar(root)
        root.title('LocalAgentBridge  |  Companion')
        root.geometry('780x220')
        root.minsize(540,200)
        root.protocol('WM_DELETE_WINDOW',self.hide)
        shell=ttk.Frame(root,padding=10)
        shell.pack(fill='both',expand=True)
        ttk.Label(shell,textvariable=self.status,wraplength=740).pack(fill='x')
        self.run_choice=ttk.Combobox(shell,state='readonly')
        self.run_choice.pack(fill='x',pady=4)
        models=ttk.Frame(shell)
        models.pack(fill='x')
        self.model_choice=ttk.Combobox(models,state='readonly')
        self.model_choice.pack(side='left',fill='x',expand=True)
        self.model_choice.bind('<<ComboboxSelected>>',lambda _:self.model_details())
        ttk.Button(models,text='Refresh models',command=self.refresh_models).pack(side='left')
        ttk.Button(models,text='Save default',command=self.select_default).pack(side='left')
        controls=ttk.Frame(shell)
        controls.pack(fill='x',pady=4)
        for label,handler in [('Details',self.toggle),('Cancel current job',self.cancel_job),('Cancel run',self.cancel_run),
                              ('Pause / resume queue',self.pause),('Evidence',self.evidence),('Hide',self.hide)]:
            ttk.Button(controls,text=label,command=handler).pack(side='left')
        ttk.Checkbutton(controls,text='Pin',variable=self.pinned,command=self.pin).pack(side='left')
        ttk.Label(shell,textvariable=self.message,wraplength=740).pack(fill='x')
        self.details=tk.Text(shell,height=18,wrap='word',state='disabled')
        self.pin()
        self.refresh_models()

    def pin(self):
        self.store.setting('dock_pinned',self.pinned.get())
        self.root.attributes('-topmost',self.pinned.get())

    def hide(self):
        self.root.withdraw()

    def toggle(self):
        self.expanded=not self.expanded
        if self.expanded:
            self.details.pack(fill='both',expand=True)
            self.root.geometry('780x620')
        else:
            self.details.pack_forget()
            self.root.geometry('780x220')

    def pause(self):
        self.store.setting('paused',not bool(self.store.setting('paused')))

    def cancel_job(self):
        if self.current and self.current['active']:
            job=self.current['active']
            self.store.cancel(job['run_id'],job['id'])
            self.message.set('Cancellation requested. A shared Ollama server may continue generating.')

    def cancel_run(self):
        if self.current and self.current['run']:
            self.store.cancel(self.current['run']['id'])
            self.message.set('Run cancellation requested; pending reviews are retained.')

    def evidence(self):
        if os.name=='nt':
            os.startfile(self.store.directory)

    def refresh_models(self):
        if self.inventory_running:
            return
        self.inventory_running=True
        def load():
            try:
                rows=asyncio.run(discover(self.config))
                self.commands.put(('inventory',self.store.annotate_inventory(rows,self.config.endpoint)))
            except Exception as error:
                self.commands.put(('inventory_error',type(error).__name__+': '+str(error)))
        threading.Thread(target=load,daemon=True).start()

    def select_default(self):
        try:
            selected=select_model(self.inventory,self.model_choice.get())
            self.store.setting('default_model',selected['name'])
            self.message.set('Default saved for future exact jobs. Routed/workflow jobs retain their configured roles and profiles.')
        except ValueError as error:
            self.message.set(str(error))

    def model_details(self):
        selected=next((r for r in self.inventory if r['name']==self.model_choice.get()),None)
        if selected:
            size=selected.get('size')
            size=f'{size/2**30:.2f} GiB' if isinstance(size,(int,float)) else 'size unavailable'
            details=selected.get('details') or {}
            self.message.set(f"{selected.get('backend','ollama')}  |  {size}  |  {details.get('quantization_level','quantization unavailable')}  |  "
                             f"{selected['validation']}  |  capabilities: {', '.join(selected.get('capabilities') or []) or 'unknown'}  |  {selected.get('reason') or ''}")

    def refresh(self):
        if self.closed:
            return
        try:
            while not self.commands.empty():
                kind,value=self.commands.get_nowait()
                if kind=='show':
                    self.root.deiconify()
                elif kind=='quit':
                    self.closed=True
                    self.root.quit()
                    return
                elif kind=='inventory':
                    self.inventory=value
                    self.inventory_running=False
                    self.model_choice['values']=[r['name'] for r in value]
                    self.model_choice.set(self.store.setting('default_model') or self.config.adaptive.preferred_model or self.config.model)
                    self.message.set(f'{len(value)} model choices. '+('Select a qualified choice; jobs revalidate identity on submission.' if value else 'Install a suitable Ollama model first.'))
                elif kind=='inventory_error':
                    self.inventory=[]
                    self.inventory_running=False
                    self.model_choice['values']=[]
                    self.message.set('Inventory unavailable / stale: '+value)
            snapshot=self.store.snapshot()
            self.run_choice['values']=[r['id'] for r in snapshot['runs']]
            self.current=presentation(snapshot,self.run_choice.get())
            self.status.set(self.current['title'])
            if self.current['run']:
                self.run_choice.set(self.current['run']['id'])
            self.details.configure(state='normal')
            self.details.delete('1.0','end')
            self.details.insert('1.0',self.current['details'])
            self.details.configure(state='disabled')
        except Exception as error:
            self.message.set('Controller state unavailable: '+str(error))
        self.root.after(1000,self.refresh)


def run_dock(config,store):
    import pystray
    from PIL import Image
    root=tk.Tk()
    dock=CompanionDock(root,config,store)
    icon=pystray.Icon('LocalAgentBridgeCompanion',Image.new('RGB',(32,32),'#397b69'),'LocalAgentBridge companion',
        menu=pystray.Menu(pystray.MenuItem('Show companion',lambda:dock.commands.put(('show',None)),default=True),
                          pystray.MenuItem('Quit dock',lambda:dock.commands.put(('quit',None)))))
    try:
        icon.run_detached()
        dock.refresh()
        root.mainloop()
    finally:
        dock.closed=True
        icon.stop()
        root.destroy()
