#!/usr/bin/env python3
"""Prepare monthly raw evidence and optional scoped Daily editorial context."""
import argparse
import calendar
import hashlib
import json
import os
import re
from datetime import datetime
from pathlib import Path
from tracework_raw import read_report


MANAGED = re.compile(
    r'<!-- tracework:daily date=(\d{4}-\d{2}-\d{2}) group=([0-9a-f]+) sha256=([0-9a-f]{64}) -->\r?\n(.*?)<!-- /tracework:daily -->', re.S)
DATE = re.compile(r'^###\s*(\d{4})[.-](\d{2})[.-](\d{2})\s*$')
PROJECT = re.compile(r'^-\s*\[([^\]]+)\]\s*$')


def parse_monthly_file(filepath, month_key, report_view, allow_group_context=True, excluded=None):
    """Admit prose by proven ownership, retaining no inferred task/status facts."""
    if not filepath or report_view['status'] == 'blocked':
        return []
    excluded = excluded if excluded is not None else {}
    text = Path(filepath).read_bytes().decode('utf-8')
    start, end = report_view['period']['start'], report_view['period']['end']
    projects = [p for rows in report_view['groups'].values() for p in rows]
    by_slug = {p['slug']: p for p in projects}
    result = []

    def keep(day, group, body, provenance, slug=None):
        if start <= day <= end and body.strip():
            result.append({'date': day, 'reporting_group': group,
                           'project_slug': slug, 'text': body,
                           'source_path': str(filepath), 'source': 'daily_prose',
                           'scope_provenance': provenance,
                           'evidence_boundary': 'editorial_only'})

    def managed(match):
        day, group_hex, digest, body = match.groups()
        try:
            group = bytes.fromhex(group_hex).decode('utf-8')
        except (ValueError, UnicodeError):
            return ''
        scope = report_view['scope']
        if (allow_group_context and report_view['status'] == 'complete' and report_view['scope_source'] != 'implicit-local'
                and (scope == 'all' or (group != 'unassigned' and group == scope))
                and hashlib.sha256(body.encode()).hexdigest() == digest):
            keep(day, group, body, 'managed_group_and_body_hash')
        else:
            excluded['managed_blocks'] = excluded.get('managed_blocks', 0) + 1
        return ''

    text = MANAGED.sub(managed, text)
    # Malformed managed content cannot fall through as legacy prose.
    if 'tracework:daily' in text:
        return result
    day, project, lines = None, None, []

    def flush():
        if day and project:
            keep(day, project['reporting_group'], '\n'.join(lines),
                 'selected_project_slug', project['slug'])

    for line in text.splitlines():
        date = DATE.fullmatch(line.strip())
        label = PROJECT.fullmatch(line)
        if re.match(r'^###\s*\d{4}[.-]\d{2}[.-]\d{2}', line.strip()):
            flush()
            day, project, lines = '-'.join(date.groups()) if date else None, None, []
        elif re.match(r'^-\s*\[(?![xX]?\s*\])', line):
            flush()
            project, lines = by_slug.get(label.group(1).strip()) if label else None, []
            if project is None:
                excluded['legacy_blocks'] = excluded.get('legacy_blocks', 0) + 1
        elif project:
            lines.append(line)
    flush()
    return result


def monthly_raw_entries(report_view):
    return [
        {'project_slug': p['slug'], 'project_name': p['name'],
         'reporting_group': p['reporting_group'],
         'source_path': e['_source_path'], 'entry_index': e['_source_index'],
         'entry': {k: v for k, v in e.items() if not k.startswith('_')}}
        for rows in report_view['groups'].values() for p in rows
        for e in (p['view'] or {}).get('entries', [])
    ]


def build_signals(report_view, filepath, month, allow_group_context=True):
    raw = monthly_raw_entries(report_view)
    excluded = {}
    editorial = parse_monthly_file(filepath, month, report_view, allow_group_context, excluded)
    return {
        'month': month,
        'report_context': {k: v for k, v in report_view.items() if k != 'groups'},
        'projects': [{k: p[k] for k in ('slug', 'name', 'reporting_group')}
                     for rows in report_view['groups'].values() for p in rows],
        'raw_entries': raw,
        'effective_views': [
            {**{k: v for k, v in p['view'].items() if k != 'entries'},
             'reporting_group': p['reporting_group']}
            for rows in report_view['groups'].values() for p in rows if p['view'] is not None],
        'editorial_context': editorial,
        'excluded_editorial': excluded,
        'coverage': {'raw_days': sorted({r['entry']['timestamp'][:10] for r in raw}),
                     'editorial_days': sorted({e['date'] for e in editorial})},
    }


def build_review_skeleton(signals, summary_mode='project_focused', evidence_mode='strict'):
    """Indexes refer to signals arrays; raw facts occur only in signals.json."""
    projects = {p['slug']: {**p, 'raw_entry_indexes': [], 'effective_view_indexes': []}
                for p in signals['projects']}
    groups, streams = {}, {}
    for slug, project in projects.items():
        groups.setdefault(project['reporting_group'], []).append(slug)
    for index, item in enumerate(signals['raw_entries']):
        slug, entry = item['project_slug'], item['entry']
        projects[slug]['raw_entry_indexes'].append(index)
        reporting = entry.get('reporting') if isinstance(entry.get('reporting'), dict) else {}
        stream = entry.get('work_stream') or reporting.get('work_stream') or slug
        key = (slug, str(stream))
        streams.setdefault(key, {'project_slug': slug, 'reporting_group': item['reporting_group'],
                                 'work_stream': str(stream), 'raw_entry_indexes': []})['raw_entry_indexes'].append(index)
    current, accepted = [], []
    for index, view in enumerate(signals['effective_views']):
        projects[view['project_slug']]['effective_view_indexes'].append(index)
        for state_index, state in enumerate(view['states']):
            reference = {'project_slug': view['project_slug'], 'effective_view_index': index,
                         'state_index': state_index}
            if state['subject'].startswith('risk:'):
                if state['state'] == 'accepted':
                    accepted.append(reference)
                elif state['state'] not in ('mitigated', 'resolved', 'closed'):
                    current.append(reference)
    has_raw = bool(signals['raw_entries'] or any(v['states'] for v in signals['effective_views']))
    return {'month': signals['month'], 'summary_mode': summary_mode, 'evidence_mode': evidence_mode,
            'evidence_source': 'raw' if has_raw else ('daily_only_limited' if signals['editorial_context'] else 'empty'),
            'projects': projects, 'reporting_groups': groups,
            'raw_work_streams': list(streams.values()),
            'current_risks': current, 'accepted_risks': accepted,
            'editorial_context_indexes': list(range(len(signals['editorial_context']))),
            'warnings': [] if has_raw else ['No matching raw facts; editorial prose supports only a limited review.']}


def main():
    parser = argparse.ArgumentParser(
        description='Prepare scoped raw facts and optional Daily editorial context',
    )
    parser.add_argument('--input', default=None,
                        help='月度归档文件路径 (YYYY-MM.md)')
    parser.add_argument('--signals-output',
                        help='信号 JSON 输出文件路径')
    parser.add_argument('--skeleton-output',
                        help='骨架 JSON 输出文件路径')
    parser.add_argument('--vault', default=None,
                        help='Tracework vault path; when provided, raw entries are the semantic source')
    parser.add_argument('--month', default=None,
                        help='Target month YYYY-MM; defaults to the input archive filename')
    parser.add_argument('--summary-mode', default='project_focused',
                        choices=['light', 'project_focused', 'engineering_review'],
                        help='总结模式 (默认: project_focused)')
    parser.add_argument('--evidence-mode', default='strict',
                        choices=['strict', 'best_effort'],
                        help='证据模式 (默认: strict)')
    parser.add_argument('--cwd', default=os.getcwd(), help='Current project root')
    parser.add_argument('--scope', help='Explicit user-selected report group or all')
    parser.add_argument('--end', help='Period end YYYY-MM-DD; defaults to month end')
    parser.add_argument('--save-draft', action='store_true', help='Explicit request to save partial evidence')
    parser.add_argument('--overwrite', action='store_true', help='Explicit request to overwrite context outputs')
    parser.add_argument('--project-slug', action='append', help='Authorized project; repeat for scoped multi-project review')
    parser.add_argument('--as-of', help='Knowledge cutoff ISO timestamp')
    args = parser.parse_args()

    if args.input and not os.path.isfile(args.input):
        parser.error(f"输入文件不存在 - {args.input}")
    target_month = args.month or (Path(args.input).stem if args.input else None)
    try:
        if not target_month or not re.fullmatch(r'\d{4}-\d{2}', target_month):
            raise ValueError()
        datetime.strptime(target_month, '%Y-%m')
    except ValueError:
        parser.error("提供 --month YYYY-MM，或使用 YYYY-MM.md 归档")

    if args.end and not args.end.startswith(target_month + '-'):
        parser.error('--end must be within the target month')
    year, month = map(int, target_month.split('-'))
    report_view = read_report(
        Path(args.cwd), 'monthly', target_month + '-01',
        args.end or f'{target_month}-{calendar.monthrange(year, month)[1]:02d}',
        args.scope, args.project_slug, Path(args.vault) if args.vault else None, args.as_of,
    )
    signals = build_signals(report_view, args.input, target_month,
                            allow_group_context=not args.project_slug)
    skeleton = build_review_skeleton(signals, args.summary_mode, args.evidence_mode)

    skeleton['report_context'] = signals['report_context']
    if report_view['status'] != 'complete':
        skeleton['warnings'].append('Report coverage is incomplete; do not claim a complete period review.')
    policy = report_view['write_policy']
    if policy == 'conversation_only' or (policy == 'explicit_save_only' and not args.save_draft):
        print(json.dumps({'signals': signals, 'skeleton': skeleton}, ensure_ascii=False, indent=2))
        return 2 if report_view['status'] == 'blocked' else 0
    if not args.signals_output or not args.skeleton_output:
        parser.error('Provide --signals-output and --skeleton-output for scoped vault output')
    if not args.overwrite and any(Path(p).exists() for p in (args.signals_output, args.skeleton_output)):
        parser.error('Output exists; use --overwrite only for an explicit update request')

    # --- Step 3: 写出两个 JSON 文件 ---
    for output_path in [args.signals_output, args.skeleton_output]:
        out_dir = os.path.dirname(output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

    with open(args.signals_output, 'w', encoding='utf-8') as f:
        json.dump(signals, f, ensure_ascii=False, indent=2)

    with open(args.skeleton_output, 'w', encoding='utf-8') as f:
        json.dump(skeleton, f, ensure_ascii=False, indent=2)

    print(f"Prepared {target_month}: {len(signals['raw_entries'])} raw entries, "
          f"{len(signals['editorial_context'])} editorial blocks")


if __name__ == '__main__':
    raise SystemExit(main())
