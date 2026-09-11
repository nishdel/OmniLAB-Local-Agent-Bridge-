"""Small, testable presentation of the same gates used by the router."""
from .models import TIERS, model_tier, task_eligibility
from .routing import canonical

QUALITY_HELP = ('Accepted: useful without substantive correction. Corrected: useful but needed correction. '
                'Rejected: materially unreliable or unusable. These are reviewed LocalAgentBridge results '
                'from this machine/workload, not universal model scores. Counts include older protocols; '
                'routing gates use per-tool benchmark reviews. Confidence is not correctness.')
COMPRESSION_HELP = ('Local compression compares input bytes with returned result bytes. '
                    'Potential context avoided — not measured Codex token savings. '
                    'Measured Codex token reduction: not available (no comparable experiment).')
CODEX_HELP = ('Codex total = recorded input + output; cached input is a subset of input, reasoning is a subset '
              'of output. Repeated context can be counted on successive requests. Cumulative rollout counters '
              'are differenced; overlapping OTel/rollout streams are deduplicated per session/model. '
              'Activity time is observed session activity, not GPU inference time. Missing counters stay unavailable.')


def snapshot(config, store, cap, installed=None):
    rows = []
    grouped = store.registry_metrics()
    empty = dict(calls=0,average_latency=None,tokens_per_second=None,accepted=None,corrected=None,rejected=None,
                 reviewed_cases=0,accepted_rate=None,rejected_rate=None)
    for p in config.model_registry:
        info = None if installed is None else installed.get(canonical(p.name))
        found = None if installed is None else info is not None and not info.get('remote_host') and not info.get('remote_model')
        metrics = grouped.get((p.name,None), empty)
        allowed_tools, blocks = [], {}
        for tool, role in config.routes.items():
            if role not in p.roles:
                continue
            task_metrics = grouped.get((p.name,tool), metrics | dict(reviewed_cases=0,accepted_rate=None,rejected_rate=None))
            allowed, reason = task_eligibility(p, config.adaptive, cap, task_metrics, tool)
            if allowed:
                allowed_tools.append(tool)
            else:
                blocks[tool] = reason
        reasons = []
        if not p.enabled:
            reasons.append('Disabled: ' + (p.disabled_reason or 'disabled in configuration'))
        if found is False:
            reasons.append('Not installed; run: ollama pull ' + p.name)
        if found is None:
            reasons.append('Installation unknown: Ollama inventory unavailable or pending')
        if not p.roles:
            reasons.append('No MCP analysis role registered; capability metadata only')
        if blocks:
            reasons.extend(f'{tool}: {reason}' for tool, reason in blocks.items())
        rows.append(dict(profile=p, installed=found, enabled=p.enabled,
                         eligible=p.enabled and found is True and bool(allowed_tools),
                         permitted=p.enabled and bool(allowed_tools), tools=allowed_tools, blocked=blocks,
                         reasons=reasons, tier=model_tier(p, config.adaptive), metrics=metrics))
    return rows


def tier_text(rows, cap, policy=None):
    eligible = [r for r in rows if r['eligible']]
    names = '; '.join(f"{r['profile'].name} ({', '.join(r['profile'].roles)})" for r in eligible) or 'none'
    highest = max(eligible, key=lambda r: (TIERS.index(r['tier']), r['profile'].strength), default=None)
    large = sum(TIERS.index(r['tier']) >= TIERS.index('Large') for r in eligible)
    experimental = sum(r['profile'].experimental for r in eligible)
    maximum = f"{highest['tier']} / {highest['profile'].name}" if highest else 'none'
    selection = 'Smallest eligible capability first; higher caps permit escalation.'
    if policy and policy.preferred_model:
        threshold = policy.maximum_trivial_max_chars if cap == 'Maximum' else policy.trivial_max_chars
        selection = (f'Simple discovery/summary up to {threshold} input characters: {policy.lightweight_model} only. '
                     f'Substantive work: prefer {policy.preferred_model} when eligible; otherwise use the lowest eligible '
                     'strength above the lightweight model. No qualifying model: Codex.')
        if cap == 'Light':
            selection = f'Simple discovery/summary within input limits: {policy.lightweight_model} only. Other work requires a higher eligible strength or Codex.'
    return (f'{cap.upper()} · Eligible: {names}\nMaximum available escalation: {maximum}\n'
            f"Large-model escalation: {'allowed by cap' if TIERS.index(cap)>=TIERS.index('Large') else 'blocked by cap'} ({large} eligible) · "
            f"Experimental: {'allowed by cap' if cap=='Maximum' else 'blocked by cap'} ({experimental} eligible)\n"
            + selection + '\nBeyond cap, resource/quality limits, or failed attempts: return to Codex. Selection still depends on role and task.')


def compression_text(data):
    lines = []
    for key, label in [('final_tasks', 'Final task payloads'), ('individual_outputs', 'Other individual outputs (legacy / fixed / consensus participants)')]:
        r = data[key]
        if r['input_bytes']:
            lines.append(f"{label}: {r['input_bytes']:,} input bytes → {r['returned_bytes']:,} returned bytes\n"
                         f"Local compression: {r['reduction']:.1%}; potential context avoided: {r['potential_bytes']:,} bytes")
    return '\n'.join(lines) or 'Local compression: no measured payloads yet.'


def activity_text(row, now):
    from .widget import elapsed
    local = row['source'] == 'local'
    duration = max(0, now-row['started'])
    tokens = row.get('output_tokens')
    line = f"{'LOCAL / OLLAMA' if local else 'CLOUD / CODEX'} · {row['model']} · {elapsed(duration)}"
    if tokens is not None:
        line += f" · {'~' if local else ''}{tokens:,} output tokens"
        if local and duration:
            line += f' · ~{tokens/duration:.1f} tok/s (includes load)'
    else:
        line += ' · ' + row['status']
    if local:
        line += f"\nRole: {row.get('role') or 'unknown'} · Model tier: {row.get('model_tier') or 'unknown'} · Cap: {row.get('route_cap') or 'fixed / unavailable'} · Task: {row.get('tool') or 'unavailable'}"
        line += (f"\nEscalated from: {row['escalated_from']} · {row.get('escalation_reason') or 'requested'}" if row.get('escalated_from')
                 else '\nSelected directly · ' + (row.get('selection_reason') or 'fixed model selection / historical record'))
    return line


def model_text(row, total, compression):
    p, m = row['profile'], row['metrics']
    a, c, r = (m.get(k) or 0 for k in ('accepted', 'corrected', 'rejected'))
    reviewed = a+c+r
    fmt = lambda value, unit='': f'{value:,.1f}{unit}' if value is not None else 'unavailable'
    lines = [p.display_name or p.name, p.name, f"Roles: {', '.join(p.roles)} · Capabilities: {', '.join(p.capabilities or p.roles)}",
             f"Architecture: {p.architecture} · Active: {p.active_parameters_b or 'unknown'}B / total: {p.total_parameters_b:g}B",
             f"Quantization: {p.quantization} · Minimum tier: {row['tier']} · Experimental: {p.experimental}",
             f"Configured thinking mode: {p.thinking} (traces are never shown or stored)",
             f"Registered: yes · Enabled: {p.enabled} · Installed: {row['installed'] if row['installed'] is not None else 'unknown'}",
             f"Currently selected / active: {row.get('active', False)}",
             f"Eligible now: {row['eligible']} · Permitted tools: {', '.join(row['tools']) or 'none'}",
             *row['reasons'], f"Weight size: {p.weight_gb:g} GiB (registry metadata)"]
    gpu, allocation = m.get('model_vram_bytes'), m.get('model_allocation_bytes')
    if gpu is not None and allocation:
        lines.append(f"Sampled Ollama allocation: {allocation/2**30:.2f} GiB; GPU: {gpu/2**30:.2f} GiB. "
                     f"VRAM fit: {'full' if gpu >= allocation else 'partial'}; CPU offload: {'none observed' if gpu >= allocation else 'observed allocation'}. Last benchmark, not live.")
    else:
        lines.append('VRAM fit / CPU offload: unknown (weights alone do not establish fit).')
    lines.extend([f"Calls: {m['calls']:,} · Total recorded tokens: {total.get('total_tokens', 'unavailable')}",
                  f"Average latency: {fmt(m['average_latency'], 's')} · Generation: {fmt(m['tokens_per_second'], ' tok/s')}",
                  f'Reviewed results: {reviewed} · Accepted: {a} · Corrected: {c} · Rejected: {r}',
                  f'Acceptance: {a/reviewed:.0%} · Unusable: {r/reviewed:.0%}' if reviewed else 'Acceptance / unusable rates: unavailable',
                  QUALITY_HELP, compression_text(compression), COMPRESSION_HELP])
    return '\n\n'.join(lines)
