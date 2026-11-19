#!/usr/bin/env python3
"""Merge generated daily bodies without replacing user edits or stale snapshots."""
import argparse
from datetime import date
from tracework_raw import json_lock
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile


class Conflict(ValueError):
    pass


def digest(data):
    return hashlib.sha256(data).hexdigest()


START = re.compile(rb'<!-- tracework:daily date=(\d{4}-\d{2}-\d{2}) group=([0-9a-f]+) sha256=([0-9a-f]{64}) -->\r?\n')
END = b'<!-- /tracework:daily -->'
DAY = re.compile(rb'^### (\d{4})[.-](\d{2})[.-](\d{2})[ \t]*\r?$', re.M)
FENCE = re.compile(r'^ {0,3}(`{3,}|~{3,})(.*)$')
OUTER_HEADING = re.compile(r'^ {0,3}#{1,3}(?=\s|$)')


def has_outer_heading(body):
    fence = None
    for line in body.split('\n'):
        marker = FENCE.match(line)
        if fence:
            if marker and marker[1].startswith(fence) and not marker[2].strip(' \t\r'):
                fence = None
        elif marker and (marker[1][0] == '~' or '`' not in marker[2]):
            fence = marker[1]
        elif OUTER_HEADING.match(line):
            return True
    return False


def validate_targets(original, day, groups):
    """Validate the snapshot for the exact requested write targets."""
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', day):
        raise Conflict('date must be YYYY-MM-DD')
    date.fromisoformat(day)
    for group in groups:
        if not isinstance(group, str) or not group.strip() or group == 'all':
            raise Conflict('use exact groups, never all')
    original.decode('utf-8')
    blocks = {}
    spans = []
    cursor = 0
    while True:
        start = original.find(b'<!-- tracework:daily', cursor)
        if start < 0:
            break
        m = START.match(original, start)
        end = original.find(END, m.end() if m else start)
        if not m or end < 0 or b'tracework:daily' in original[m.end():end]:
            raise Conflict('damaged daily markers')
        key = (m[1].decode(), m[2].decode())
        try:
            date.fromisoformat(key[0])
            group = bytes.fromhex(key[1]).decode('utf-8')
        except ValueError as error:
            raise Conflict('invalid marker identity') from error
        if not group.strip() or group == 'all' or key in blocks:
            raise Conflict('duplicate or invalid daily block')
        blocks[key] = (start, end + len(END), original[m.end():end], m[3].decode())
        spans.append((start, end + len(END)))
        cursor = end + len(END)
    # Any unmatched/respelled marker is unsafe, including orphan closing markers.
    outside = original
    for start, end in reversed(spans):
        outside = outside[:start] + outside[end:]
    if b'tracework:daily' in outside:
        raise Conflict('unmatched daily marker')
    days = [heading for heading in DAY.finditer(original)
            if not any(start <= heading.start() < end for start, end in spans)]
    matching = [m for m in days if b'-'.join(m.groups()).decode() == day]
    if len(matching) > 1:
        raise Conflict('duplicate date heading')
    for (block_day, _), (start, _, _, _) in blocks.items():
        previous = [m for m in days if m.start() < start]
        if not previous or b'-'.join(previous[-1].groups()).decode() != block_day:
            raise Conflict('block/date heading mismatch')
    selected = {}
    for group in groups:
        old = blocks.get((day, group.encode().hex()))
        if old is None:
            continue
        start, end, previous, stored_hash = old
        if digest(previous) != stored_hash:
            raise Conflict(f'user-edited block: {day}/{group}')
        selected[group] = (start, end, previous)
    heading_end = matching[0].end() if matching else None
    if len(selected) < len(groups) and heading_end is not None and not any(d == day for d, _ in blocks):
        following = re.search(rb'^#{1,3}\s', original[heading_end:], re.M)
        end = heading_end + following.start() if following else len(original)
        if original[heading_end:end].strip():
            raise Conflict('legacy date content has unknown ownership')
    return selected, heading_end


def merge(original, day, bodies):
    if not isinstance(bodies, dict) or not bodies:
        raise Conflict('bodies must be a nonempty group-to-Markdown object')
    for body in bodies.values():
        if (not isinstance(body, str) or not body.strip() or 'tracework:daily' in body
                or has_outer_heading(body)):
            raise Conflict('body must be nonempty prose without managed markers or outer headings')
    selected, heading_end = validate_targets(original, day, bodies)
    edits = []
    new_blocks = []
    for group, body in bodies.items():
        group_hex = group.encode().hex()
        payload = (body.rstrip() + '\n').encode()
        block = f'<!-- tracework:daily date={day} group={group_hex} sha256={digest(payload)} -->\n'.encode() + payload + END
        if group in selected:
            start, end, _ = selected[group]
            edits.append((start, end, block))
        else:
            new_blocks.append(block)
    if new_blocks:
        payload = b'\n\n'.join(new_blocks) + b'\n'
        if heading_end is not None:
            # Insert immediately after the heading; keep every existing byte.
            edits.append((heading_end, heading_end, b'\n\n' + payload))
        else:
            edits.append((len(original), len(original), b'\n\n### ' + day.replace('-', '.').encode() + b'\n\n' + payload))
    result = original
    for start, end, replacement in sorted(edits, reverse=True):
        result = result[:start] + replacement + result[end:]
    return result


def snapshot(path):
    if path.is_symlink():
        raise Conflict('symlink output is not supported')
    return path.read_bytes() if path.exists() else None


def update(path, day, bodies, expected_hash):
    path = Path(path)
    # ponytail: advisory per-file lock serializes this writer, unrelated editors
    # use the snapshot check; filesystem-wide compare-and-swap if ever available.
    path.parent.stat()  # Preserve the existing requirement that the vault directory exists.
    with json_lock(path.with_name(path.name + '.tracework')):
        before = snapshot(path)
        actual = digest(before) if before is not None else 'missing'
        if actual != expected_hash:
            raise Conflict('file changed since draft snapshot')
        after = merge(before or b'', day, bodies)
        if after == before:
            return 'unchanged'
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.tracework-daily-', delete=False) as handle:
                temporary = handle.name
                handle.write(after)
                handle.flush()
                os.fsync(handle.fileno())
            if before is not None:
                os.chmod(temporary, path.stat().st_mode & 0o777)
            if snapshot(path) != before:
                raise Conflict('file changed during merge')
            os.replace(temporary, path)
        finally:
            if temporary and os.path.exists(temporary):
                os.unlink(temporary)
    return 'updated'


def inspect_snapshot(path, day, groups):
    before = snapshot(Path(path))
    selected, _ = validate_targets(before or b'', day, groups)
    return {'status': 'ready', 'expected_file_hash': digest(before) if before is not None else 'missing',
            'bodies': {group: body.decode() for group, (_, _, body) in selected.items()}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--path', required=True)
    parser.add_argument('--date', required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--inspect', action='store_true', help='Read exact date/group bodies and snapshot hash')
    mode.add_argument('--bodies', help='UTF-8 JSON: exact group -> Markdown')
    parser.add_argument('--group', action='append', help='Exact group to inspect; repeat for each target group')
    parser.add_argument('--expected-file-hash', help='SHA-256 of draft snapshot, or missing')
    args = parser.parse_args()
    if args.inspect and (not args.group or args.expected_file_hash is not None):
        parser.error('--inspect requires --group and takes no --expected-file-hash')
    if not args.inspect and (args.group or args.expected_file_hash is None):
        parser.error('--bodies requires --expected-file-hash and takes no --group')
    try:
        if args.inspect:
            result = inspect_snapshot(args.path, args.date, dict.fromkeys(args.group))
            print(json.dumps(result))
            return 0
        bodies = json.loads(Path(args.bodies).read_text(encoding='utf-8'))
        status = update(args.path, args.date, bodies, args.expected_file_hash)
        print(json.dumps({'status': status, 'path': args.path}))
        return 0
    except (OSError, ValueError) as error:
        result = {'status': 'conflict', 'reason': str(error)}
        if args.bodies is not None:
            result['draft'] = args.bodies
        print(json.dumps(result))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
