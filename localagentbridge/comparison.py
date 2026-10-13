"""Offline comparison accounting. No inference, startup or automatic acceptance.

Usage is a view of usage_report.investment, never a second token collector.
Energy is trapezoidal integration over observed, identity-stable intervals only.
"""
from collections import defaultdict
import math

from .usage_report import aggregate, operating_savings

PHASES = ('planning', 'dispatch', 'queue', 'loading', 'exact_counting', 'generation',
          'tools', 'verification', 'review', 'repair', 'fallback', 'integration', 'shutdown')
OUTCOMES = ('not_run', 'blocked', 'failed', 'rejected', 'accepted_first_pass',
            'accepted_after_local_retry', 'accepted_after_codex_repair')
ACCEPTED = set(OUTCOMES[-3:])
DOMAINS = ('gpu_board', 'cpu_package', 'whole_system')


def number(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def energy(samples, start, end, *, max_gap_seconds=5, idle_watts=None):
    """Samples: timestamp UTC seconds, watts W (or None), source/domain/device.

    Each sample must also have a monotonic_seconds clock or an explicit
    clock='utc_only' limitation. Missing samples/identity changes break coverage.
    Return one physical measurement stream. Never sum board and wall readings.
    """
    if not all(number(v) for v in (start, end, max_gap_seconds)) or end <= start or max_gap_seconds == 0:
        raise ValueError('Invalid measurement interval or gap limit')
    if idle_watts is not None and not number(idle_watts):
        raise ValueError('Idle reference must be observed nonnegative watts')
    rows = []
    seen = {}
    for sample in samples:
        if not number(sample.get('timestamp')):
            raise ValueError('Power samples require numeric UTC seconds')
        if sample.get('domain') not in DOMAINS or not all(sample.get(k) for k in ('source', 'device')):
            raise ValueError('Power measurement boundary and identity required')
        if sample.get('units') != 'W':
            raise ValueError('Power must be converted to W before integration')
        if sample.get('watts') is not None and not number(sample['watts']):
            raise ValueError('Invalid observed power')
        if not number(sample.get('monotonic_seconds')) and sample.get('clock') != 'utc_only':
            raise ValueError('Declare monotonic clock or utc_only limitation')
        key = sample['timestamp']
        if key in seen:
            if seen[key] != sample:
                raise ValueError('Conflicting power samples at one timestamp')
            continue
        seen[key] = sample
        rows.append(sample)
    rows.sort(key=lambda r: r['timestamp'])
    streams = {(r['source'], r['domain'], r['device']) for r in rows}
    if len(streams) > 1:
        raise ValueError('Integrate each source/domain/device separately; do not overlap streams')
    covered = joules = 0.0
    gaps = []
    for left, right in zip(rows, rows[1:]):
        a, b = max(start, left['timestamp']), min(end, right['timestamp'])
        if b <= a:
            continue
        dt = right['timestamp'] - left['timestamp']
        reason = None
        if dt > max_gap_seconds:
            reason = 'sampling_gap'
        elif left.get('watts') is None or right.get('watts') is None:
            reason = 'unavailable_power'
        elif left.get('generation') != right.get('generation'):
            reason = 'sensor_restart'
        elif number(left.get('monotonic_seconds')) and number(right.get('monotonic_seconds')):
            active = right['monotonic_seconds'] - left['monotonic_seconds']
            if active <= 0 or abs(active - dt) >= 1:
                reason = 'clock_discontinuity_or_suspend'
        elif left.get('clock') != right.get('clock'):
            reason = 'clock_changed'
        if reason:
            gaps.append({'start': a, 'end': b, 'reason': reason})
            continue
        slope = (right['watts'] - left['watts']) / dt
        wa = left['watts'] + slope * (a - left['timestamp'])
        wb = left['watts'] + slope * (b - left['timestamp'])
        joules += (wa + wb) * (b - a) / 2
        covered += b - a
    source, domain, device = next(iter(streams)) if streams else (None, None, None)
    gross = joules / 3600 if covered else None
    return dict(source=source, domain=domain, device=device, start=start, end=end,
                gross_observed_wh=gross, covered_seconds=covered,
                boundary_seconds=end-start, uncovered_seconds=max(0, end-start-covered),
                coverage_ratio=covered/(end-start), gaps=gaps,
                complete=math.isclose(covered, end-start, abs_tol=1e-6),
                idle_subtracted_estimate_wh=(gross-idle_watts*covered/3600)
                if gross is not None and idle_watts is not None else None,
                idle_reference_watts=idle_watts,
                limitations=['No extrapolation over gaps or uncovered endpoints; sampled, not continuous.',
                             'Board/package energy is not whole-system electricity or cloud datacenter energy.'] +
                (['UTC-only source: suspend/clock continuity not independently verified.']
                 if any(r.get('clock') == 'utc_only' for r in rows) else []))


def empty_attempt(*, arm, fixture, trial, attempt, candidate, settings_sha256, fixture_sha256):
    """Sanitized schema; null means unmeasured. Live session IDs stay private."""
    return dict(schema_version=1, mode='not_run', arm=arm, fixture=fixture, trial=trial,
                attempt=attempt, candidate=candidate, settings_sha256=settings_sha256,
                fixture_sha256=fixture_sha256, accounting_run_id=None, lane=None,
                admission={'status': 'not_run', 'reason': None}, outcome='not_run',
                failure_class=None, independent_checks=[], regressions=None,
                review={'independent': False, 'evidence': None, 'candidate_sha256': None},
                first_pass_accepted=None, corrections=None, owner_interventions=None,
                owner_review_seconds=None, end_to_end_seconds=None,
                phase_seconds={p: None for p in PHASES},
                cloud_coverage={p: 'unknown' for p in PHASES},
                usage_report_sha256=None, local_receipt_ids=[], cloud_session_bindings=[],
                actual_supervisor={'model': None, 'settings': None, 'session_evidence': None},
                actual_provider={'model': None, 'identity': None, 'settings': None, 'receipt_evidence': None},
                preflight_tokens=None, cache_state='unknown',
                resources={'peak_ram_bytes': None, 'minimum_available_ram_bytes': None,
                           'peak_vram_mib': None, 'disk_read_bytes': None, 'disk_write_bytes': None,
                           'scope': 'unavailable', 'coverage': None},
                energy=[], notes=[])


def validate_attempt(row):
    if row.get('outcome') not in OUTCOMES:
        raise ValueError('Unknown attempt outcome')
    if row.get('mode') not in ('not_run', 'mock', 'live'):
        raise ValueError('Unknown evidence mode')
    if row['outcome'] in ACCEPTED:
        review = row.get('review', {})
        checks = row.get('independent_checks', [])
        if (not review.get('independent') or not review.get('evidence') or
                not review.get('candidate_sha256') or not checks or
                not all(c.get('passed') is True and c.get('evidence') for c in checks) or
                row.get('regressions') != [] or row['admission']['status'] != 'admitted'):
            raise ValueError('Accepted work needs independent checks, review, hash and no regressions')
    if row['outcome'] in ('blocked', 'not_run') and row.get('first_pass_accepted') is True:
        raise ValueError('Blocked/not-run is not a quality success')
    if row['outcome'] in ('failed', 'blocked', 'rejected') and not row.get('failure_class'):
        raise ValueError('Unsuccessful work requires an explicit failure class')
    for field in ('owner_interventions', 'owner_review_seconds', 'end_to_end_seconds'):
        if row.get(field) is not None and not number(row[field]):
            raise ValueError('Invalid measurement: '+field)
    return row


def report(attempts, usage, *, equivalence_evidence=None):
    """All attempts in scope; one existing accounting run per arm/fixture/trial.

    Cloud phase coverage is a supervisor evidence declaration: 'observed' or
    'not_applicable:<reason>'. A binding alone never proves complete coverage.
    Supplied usage must be the existing report's selected (deduplicated) records.
    """
    usage = usage.get('investment', usage)  # Accept the existing CLI report envelope.
    groups = defaultdict(list)
    seen = set()
    for row in attempts:
        validate_attempt(row)
        key = (row['arm'], row['fixture'], row['trial'], row['attempt'])
        if key in seen:
            raise ValueError('Duplicate attempt')
        seen.add(key)
        groups[key[:3]].append(row)
    result = []
    bound_runs = set()
    for (arm, fixture, trial), rows in sorted(groups.items()):
        rows.sort(key=lambda r: r['attempt'])
        if [r['attempt'] for r in rows] != list(range(1, len(rows)+1)):
            raise ValueError('Missing earlier attempt: unsuccessful work cannot be omitted')
        identities = {(r['candidate'], r['fixture_sha256'], r['settings_sha256'], r['mode']) for r in rows}
        if len(identities) != 1:
            raise ValueError('Attempt identities changed within a task')
        run_ids = {r.get('accounting_run_id') for r in rows}
        if len(run_ids) != 1:
            raise ValueError('Bind the complete task, including attempts, to one accounting run')
        run_id = next(iter(run_ids))
        if run_id and run_id in bound_runs:
            raise ValueError('Accounting run overlaps two task configurations')
        if run_id:
            bound_runs.add(run_id)
        selected = [r for r in usage.get('records', [])
                    if run_id and (r.get('attribution') or {}).get('run_id') == run_id]
        # Reject repeated source record identities rather than inflate imported totals.
        record_ids = [(r.get('source'), r.get('id')) for r in selected]
        if len(record_ids) != len(set(record_ids)):
            raise ValueError('Duplicate selected usage receipt')
        cloud = aggregate([r for r in selected if r['source'] != 'local'])
        local = aggregate([r for r in selected if r['source'] == 'local'])
        final = rows[-1]
        accepted = final['outcome'] in ACCEPTED
        complete = bool(selected) and all(
            set(r.get('cloud_coverage', {})) == set(PHASES) and
            all(v == 'observed' or (isinstance(v, str) and v.startswith('not_applicable:') and
                                   v.removeprefix('not_applicable:').strip())
                for v in r['cloud_coverage'].values()) and r.get('usage_report_sha256')
            for r in rows)
        energies = defaultdict(list)
        for r in rows:
            boundaries = set()
            for e in r['energy']:
                physical = (e['domain'], e['device'])
                if physical in boundaries:
                    raise ValueError('Overlapping power streams for one physical domain/device')
                boundaries.add(physical)
                energies[(e['domain'], e['device'], e['source'])].append(e)
        energy_totals = []
        for (domain, device, source), values in energies.items():
            values.sort(key=lambda e: e['start'])
            if any(a['end'] > b['start'] for a, b in zip(values, values[1:])):
                raise ValueError('Overlapping attempt energy intervals')
            measured = [e['gross_observed_wh'] for e in values if e['gross_observed_wh'] is not None]
            full = len(values) == len(rows) and all(e['complete'] for e in values)
            energy_totals.append(dict(domain=domain, device=device, source=source,
                known_gross_wh=sum(measured) if measured else None,
                total_gross_wh=sum(measured) if full and measured else None,
                complete=full, includes_unsuccessful_attempts=True))
        result.append(dict(arm=arm, fixture=fixture, trial=trial, mode=final['mode'],
            candidate=final['candidate'], fixture_sha256=final['fixture_sha256'],
            lane=final['lane'], attempts=len(rows), final_outcome=final['outcome'],
            accepted=accepted, quality_evaluated=final['outcome'] not in ('blocked','not_run'),
            first_pass_accepted=(rows[0]['outcome']=='accepted_first_pass')
                if rows[0]['outcome'] not in ('blocked','not_run') else None,
            cloud=cloud, local=local, cloud_complete=bool(complete), energy=energy_totals,
            known_elapsed_seconds=sum(r['end_to_end_seconds'] or 0 for r in rows)
                if any(r['end_to_end_seconds'] is not None for r in rows) else None,
            total_elapsed_seconds=sum(r['end_to_end_seconds'] for r in rows)
                if all(r['end_to_end_seconds'] is not None for r in rows) else None))
    comparisons = []
    for hybrid in result:
        if hybrid['arm'] == 'A':
            continue
        baseline = next((b for b in result if (b['arm'], b['fixture'], b['trial']) ==
                         ('A', hybrid['fixture'], hybrid['trial'])), None)
        same = bool(baseline and baseline['accepted'] and hybrid['accepted'] and
                    baseline['mode'] == hybrid['mode'] == 'live' and
                    baseline['candidate'] == hybrid['candidate'] and
                    baseline['fixture_sha256'] == hybrid['fixture_sha256'])
        b = baseline['cloud']['tokens']['total_tokens']['total'] if baseline else None
        h = hybrid['cloud']['tokens']['total_tokens']['total']
        comparisons.append(dict(arm=hybrid['arm'], fixture=hybrid['fixture'], trial=hybrid['trial'],
            **operating_savings(b, h, equivalent=same,
                complete=bool(baseline and baseline['cloud_complete'] and hybrid['cloud_complete']),
                evidence=equivalence_evidence)))
    # Energy per accepted task includes energy spent on all failed tasks too.
    fleet = []
    for arm in sorted({r['arm'] for r in result}):
        tasks = [r for r in result if r['arm'] == arm and r['final_outcome'] != 'not_run']
        accepted = sum(r['accepted'] for r in tasks)
        streams = {(e['domain'], e['device'], e['source']) for r in tasks for e in r['energy']}
        for domain, device, source in sorted(streams):
            entries = [next((e for e in r['energy'] if (e['domain'],e['device'],e['source']) ==
                            (domain,device,source)), None) for r in tasks]
            complete = bool(entries) and all(e and e['complete'] for e in entries)
            total = sum(e['total_gross_wh'] for e in entries) if complete else None
            fleet.append(dict(arm=arm, domain=domain, device=device, source=source,
                accepted_tasks=accepted, all_tasks_gross_wh=total,
                wh_per_accepted_task=total/accepted if total is not None and accepted else None))
    return dict(schema_version=1, tasks=result, comparisons=comparisons,
                energy_per_accepted_task=fleet, categories=usage.get('categories'),
                limitations=['Mock evidence never establishes savings or quality.',
                             'Missing counters remain unknown. Subset tokens are not added to totals.',
                             'Blocked/not-run qualification is not a model-quality failure.'])


def next_step(manifest, attempts, usage, *, elapsed_seconds, evidence_bytes):
    """Read-only bounded operator queue. This is not dispatch/startup authority.

    Empty evidence permits proposing the first pilot slot only. After that, any
    incomplete accounting or failed pilot acceptance halts continuation. Repair
    attempts are supervisor-controlled within the selected slot, never automatic.
    """
    plan = manifest['plan']
    usage = usage.get('investment', usage)
    limits = plan['budgets']
    if not number(elapsed_seconds) or not number(evidence_bytes):
        raise ValueError('Observed elapsed/storage required')
    for value, ceiling in ((elapsed_seconds,limits['total_wall_seconds']),
                           (evidence_bytes,limits['total_output_bytes']),
                           (len(attempts),limits['maximum_attempts'])):
        if value >= ceiling:
            return {'status':'halt','reason':'Comparison budget exhausted'}
    cases = {c['key']: c for c in manifest['cases']}
    allowed = {(c['arm'],c['fixture'],c['trial']) for c in cases.values() if c['arm'] != 'D'}
    for row in attempts:
        if (row['arm'],row['fixture'],row['trial']) not in allowed or row['mode'] != 'live':
            raise ValueError('Only declared eligible live slots can advance the queue')
        if not 1 <= row['attempt'] <= limits['attempts_per_session']:
            raise ValueError('Attempt budget exceeded')
        case = next(c for c in cases.values() if (c['arm'],c['fixture'],c['trial']) ==
                    (row['arm'],row['fixture'],row['trial']))
        if (row['candidate'] != manifest['candidate_commit'] or
                row['settings_sha256'] != case['settings_sha256'] or
                row['fixture_sha256'] != case['fixture_sha256']):
            raise ValueError('Attempt does not match the frozen candidate/settings/fixture')
    if attempts:
        cloud = aggregate([r for r in usage.get('records',[]) if r['source'] != 'local'])['tokens']['total_tokens']['total']
        if cloud is None:
            return {'status':'halt','reason':'Complete cloud counters unavailable'}
        if cloud >= limits['maximum_cloud_total_tokens']:
            return {'status':'halt','reason':'Cloud token budget exhausted'}
    result = report(attempts, usage)
    finished = {(t['arm'],t['fixture'],t['trial']):t for t in result['tasks']}
    pilot = plan['pilot']
    for task in result['tasks']:
        if (not task['cloud_complete'] or task['total_elapsed_seconds'] is None or
                task['cloud']['tokens']['total_tokens']['total'] is None):
            return {'status':'halt','reason':'Incomplete end-to-end accounting'}
        if task['total_elapsed_seconds'] > limits['task_end_to_end_seconds']:
            return {'status':'halt','reason':'Task time budget exceeded'}
        if task['fixture'] in pilot['fixtures'] and task['trial'] == pilot['trial'] and not task['accepted']:
            return {'status':'halt','reason':'Pilot acceptance failed; review before any new package'}
        # Unsupported CPU/wall sensors remain unknown; only the declared measured
        # boundary gates this board-energy comparison. Do not turn absent CPU
        # power into a demand to install/probe a sensor or into a zero reading.
        declared = [e for e in task['energy'] if e['domain'] == 'gpu_board'
                    and e['known_gross_wh'] is not None]
        if not declared or not all(e['complete'] for e in declared):
            return {'status':'halt','reason':'Declared power coverage incomplete; review measurement gap'}
    pilot_cases = [c for c in cases.values() if c['arm'] in pilot['arms'] and
                   c['trial']==pilot['trial'] and c['fixture'] in pilot['fixtures']]
    rest = [c for c in cases.values() if c['arm'] != 'D' and c not in pilot_cases]
    remaining_pilot = [c for c in pilot_cases if (c['arm'],c['fixture'],c['trial']) not in finished]
    if remaining_pilot and elapsed_seconds >= pilot['wall_seconds']:
        return {'status':'halt','reason':'Pilot wall budget exhausted'}
    remaining = [c for c in pilot_cases+rest if (c['arm'],c['fixture'],c['trial']) not in finished]
    return {'status':'proposed' if remaining else 'complete', 'next':remaining[0] if remaining else None,
            'requires':'Existing bounded package approval, exact qualification/resource/session checks and scoped contract approval; no startup performed'}
