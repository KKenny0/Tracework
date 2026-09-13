#!/usr/bin/env python3
"""Scoped effective raw facts, correction history and period-end lifecycle state."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import re


def validate_slug(slug):
    if not isinstance(slug, str) or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]*', slug):
        raise ValueError('invalid project slug')
    return slug


def entry_hash(entry):
    raw = {k: v for k, v in entry.items() if not k.startswith('_')}
    return hashlib.sha256(json.dumps(raw, sort_keys=True, ensure_ascii=False,
                                    separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def entry_id(entry, slug):
    return f"raw:{slug}:{entry['_source_week']}:{entry['_source_index']}"


def timestamp(value):
    parsed = dt.datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    return parsed.replace(tzinfo=dt.timezone.utc) if parsed.tzinfo is None else parsed


def validate_correction(correction):
    if not isinstance(correction, dict) or set(correction) != {'operation', 'target_ref', 'target_hash', 'reason'}:
        raise ValueError('correction requires operation, target_ref, target_hash, reason only')
    if correction['operation'] not in ('replace', 'retract'):
        raise ValueError('correction operation must be replace or retract')
    ref = correction['target_ref']
    if not isinstance(ref, dict) or set(ref) != {'week', 'entry_index', 'timestamp'}:
        raise ValueError('target_ref is local to this project: week, entry_index, timestamp only')
    if not isinstance(ref['week'], str) or not re.fullmatch(r'\d{4}-W\d{2}', ref['week']):
        raise ValueError('invalid target week')
    dt.date.fromisocalendar(int(ref['week'][:4]), int(ref['week'][6:]), 1)
    if type(ref['entry_index']) is not int or ref['entry_index'] < 0:
        raise ValueError('invalid target entry_index')
    timestamp(ref['timestamp'])
    if not isinstance(correction['target_hash'], str) or not re.fullmatch(r'[0-9a-f]{64}', correction['target_hash']):
        raise ValueError('invalid target_hash')
    if not isinstance(correction['reason'], str) or not correction['reason'].strip():
        raise ValueError('correction reason is required')
    return ref


def load_records(vault, slug):
    validate_slug(slug)
    root = Path(vault).resolve() / 'raw' / 'weeks'
    records, paths = [], []
    for path in sorted(root.glob(f'*/{slug}.json')):
        # Repo/config paths do not grant permission to follow escaping storage links.
        if path.resolve() != path:
            raise ValueError('raw storage symlinks cannot establish project ownership')
        data = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(data, list):
            raise ValueError(f'raw file is not an array: {path}')
        paths.append(str(path))
        for i, entry in enumerate(data):
            if isinstance(entry, dict):
                records.append({**entry, '_source_week': path.parent.name,
                                '_source_index': i, '_source_path': str(path)})
    return records, paths


def effective_records(records, slug, as_of=None):
    """Resolve immutable replacement chains before filtering by work period."""
    validate_slug(slug)
    cutoff = timestamp(as_of) if as_of else None
    visible, diagnostics = {}, []
    for record in records:
        key = entry_id(record, slug)
        if cutoff:
            captured = record.get('captured_at')
            if not captured:
                diagnostics.append(f'{key}: captured_at missing; exact as-of replay unavailable')
            try:
                if timestamp(captured or record.get('timestamp')) > cutoff:
                    continue
            except (ValueError, TypeError):
                diagnostics.append(f'{key}: invalid capture time; excluded')
                continue
        visible[key] = record
    active = {key: dict(record, _logical_id=key,
                       _question_subjects=[f'open_question:{key}:{i}' for i, _ in enumerate(record.get('open_questions') or [])])
              for key, record in visible.items() if 'correction' not in record}
    history, blocked = [], set()
    corrections = [(key, record) for key, record in visible.items() if 'correction' in record]
    def order(item):
        key, record = item
        try:
            return (timestamp(record.get('captured_at')), record['_source_week'], record['_source_index'])
        except (ValueError, TypeError):
            return (dt.datetime.min.replace(tzinfo=dt.timezone.utc), '', 0)
    for key, record in sorted(corrections, key=order):
        correction = record['correction']
        target_key = None
        try:
            ref = validate_correction(correction)
            target_key = f"raw:{slug}:{ref['week']}:{ref['entry_index']}"
            target = visible.get(target_key)
            if not target:
                raise ValueError('missing or not-yet-known target')
            if target.get('timestamp') != ref['timestamp'] or entry_hash(target) != correction['target_hash']:
                raise ValueError('target timestamp/hash mismatch')
            if record.get('timestamp') != target.get('timestamp') or record['_source_week'] != ref['week']:
                raise ValueError('correction must retain target work time and week')
            if not record.get('captured_at'):
                raise ValueError('correction captured_at required')
            timestamp(record['captured_at'])
            if correction['operation'] == 'replace' and not all(isinstance(record.get(field), str) and record[field].strip() for field in ('summary', 'context', 'type', 'source')):
                raise ValueError('replacement requires complete normal factual fields')
            if target_key not in active:
                raise ValueError('target is not the effective chain tail')
            previous = active.pop(target_key)
            logical = previous['_logical_id']
            if correction['operation'] == 'replace':
                old_questions = previous.get('open_questions') or []
                subjects = [previous['_question_subjects'][i] if i < len(old_questions) and question == old_questions[i]
                            else f'open_question:{key}:{i}' for i, question in enumerate(record.get('open_questions') or [])]
                active[key] = dict(record, _logical_id=logical, _question_subjects=subjects)
            history.append({'entry_id': key, 'target_id': target_key, 'logical_id': logical,
                            'operation': correction['operation'], 'reason': correction['reason'],
                            'captured_at': record['captured_at']})
        except (ValueError, TypeError, KeyError) as error:
            diagnostics.append(f'{key}: correction conflict: {error}')
            if target_key:
                blocked.add(target_key)
    # A conflicting branch must never leave a more optimistic accepted sibling.
    roots = {h['target_id']: h['logical_id'] for h in history}
    blocked_roots = {roots.get(key, key) for key in blocked}
    active = {k: v for k, v in active.items() if v['_logical_id'] not in blocked_roots}
    return list(active.values()), history, diagnostics


def project_states(entries, slug):
    states, diagnostics = {}, []
    for entry in entries:
        identity = entry.get('_logical_id', entry_id(entry, slug))
        if entry.get('type') == 'risk' or entry.get('archetype') == 'risk' or entry.get('status') == 'risk':
            subject = f'risk:{identity}'
            states[subject] = {'subject': subject, 'state': 'open', 'entry_id': identity,
                               'timestamp': entry['timestamp'], 'text': entry.get('summary'), 'evidence_refs': [entry_id(entry, slug)]}
        for i, question in enumerate(entry.get('open_questions') or []):
            if isinstance(question, str):
                subject = entry.get('_question_subjects', [f'open_question:{identity}:{n}' for n, _ in enumerate(entry.get('open_questions') or [])])[i]
                states[subject] = {'subject': subject, 'state': 'open', 'entry_id': identity,
                                   'timestamp': entry['timestamp'], 'text': question, 'evidence_refs': [entry_id(entry, slug)]}
    for entry in sorted(entries, key=lambda e: (timestamp(e['timestamp']), e['_source_week'], e['_source_index'])):
        transition = entry.get('lifecycle_transition')
        if not isinstance(transition, dict):
            continue
        subject, target = transition.get('subject'), transition.get('to')
        if not isinstance(subject, str) or not isinstance(target, str):
            diagnostics.append(f'{entry_id(entry, slug)}: incomplete lifecycle transition; unassociated')
            continue
        if subject not in states:
            if subject.startswith(('risk:raw:', 'open_question:raw:')):
                diagnostics.append(f'{subject}: missing exact subject; unassociated')
                continue
            # Legacy names form their own exact-name chain, never close a raw question.
            states[subject] = {'subject': subject, 'state': transition.get('from', 'unknown'),
                               'entry_id': None, 'text': subject, 'evidence_refs': [], 'legacy': True}
        state = states[subject]
        if state.get('timestamp') and timestamp(entry['timestamp']) < timestamp(state['timestamp']):
            diagnostics.append(f'{subject}: transition precedes subject; ignored')
            continue
        before = transition.get('from')
        if state['state'] == 'conflict' or (before and before != state['state']):
            state['state'] = 'conflict'
            diagnostics.append(f'{subject}: conflicting lifecycle transition')
        elif not before:
            state['state'] = 'conflict'
            diagnostics.append(f'{subject}: previous state unspecified; transition unverified')
        else:
            state['state'] = target
        state['evidence_refs'].append(entry_id(entry, slug))
    return list(states.values()), diagnostics


def read_view(vault, slug, start=None, end=None, as_of=None):
    for bound in (start, end):
        if bound:
            if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', bound):
                raise ValueError('period dates must be YYYY-MM-DD')
            dt.date.fromisoformat(bound)
    if start and end and start > end:
        raise ValueError('start is after end')
    records, paths = load_records(vault, slug)
    effective, history, diagnostics = effective_records(records, slug, as_of)
    eligible = []
    for entry in effective:
        try:
            timestamp(entry['timestamp'])
            if not end or entry['timestamp'][:10] <= end:
                eligible.append(entry)
        except (ValueError, TypeError, KeyError):
            diagnostics.append(f'{entry_id(entry, slug)}: invalid work timestamp; excluded')
    states, state_diagnostics = project_states(eligible, slug)
    entries = [e for e in eligible if not start or e['timestamp'][:10] >= start]
    entries.sort(key=lambda e: (timestamp(e['timestamp']), e['_source_week'], e['_source_index']))
    return {'schema_version': 'tracework.effective_view.v1', 'project_slug': slug,
            'period': {'start': start, 'end': end, 'as_of': as_of}, 'entries': entries,
            'correction_history': history, 'states': states,
            'diagnostics': diagnostics + state_diagnostics, 'raw_paths': paths,
            'raw_entry_count': len(records)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--vault', required=True)
    parser.add_argument('--slug', required=True, help='One explicitly authorized project')
    parser.add_argument('--start')
    parser.add_argument('--end')
    parser.add_argument('--as-of', help='Knowledge cutoff ISO timestamp; defaults to current knowledge')
    args = parser.parse_args()
    try:
        print(json.dumps(read_view(args.vault, args.slug, args.start, args.end, args.as_of), ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError) as error:
        print(json.dumps({'error': str(error)}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
