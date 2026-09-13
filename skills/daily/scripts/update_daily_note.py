#!/usr/bin/env python3
"""Merge generated daily bodies without replacing user edits or stale snapshots."""
import argparse
from datetime import date
import fcntl
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


def merge(original, day, bodies):
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', day):
        raise Conflict('date must be YYYY-MM-DD')
    date.fromisoformat(day)
    if not isinstance(bodies, dict) or not bodies:
        raise Conflict('bodies must be a nonempty group-to-Markdown object')
    for group, body in bodies.items():
        if not isinstance(group, str) or not group.strip() or group == 'all':
            raise Conflict('use exact groups, never all')
        if not isinstance(body, str) or not body.strip() or 'tracework:daily' in body or re.search(r'^#{1,3}\s', body, re.M):
            raise Conflict('body must be nonempty prose without managed markers or outer headings')
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
    days = list(DAY.finditer(original))
    matching = [m for m in days if b'-'.join(m.groups()).decode() == day]
    if len(matching) > 1:
        raise Conflict('duplicate date heading')
    for (block_day, _), (start, _, _, _) in blocks.items():
        previous = [m for m in days if m.start() < start]
        if not previous or b'-'.join(previous[-1].groups()).decode() != block_day:
            raise Conflict('block/date heading mismatch')
    edits = []
    new_blocks = []
    for group, body in bodies.items():
        group_hex = group.encode().hex()
        payload = (body.rstrip() + '\n').encode()
        block = f'<!-- tracework:daily date={day} group={group_hex} sha256={digest(payload)} -->\n'.encode() + payload + END
        old = blocks.get((day, group_hex))
        if old:
            start, end, previous, stored_hash = old
            if digest(previous) != stored_hash:
                raise Conflict(f'user-edited block: {day}/{group}')
            edits.append((start, end, block))
        else:
            new_blocks.append(block)
    if new_blocks:
        if matching:
            heading = matching[0]
            following = re.search(rb'^#{1,3}\s', original[heading.end():], re.M)
            end = heading.end() + following.start() if following else len(original)
            owned = [v for (d, _), v in blocks.items() if d == day]
            if not owned and original[heading.end():end].strip():
                raise Conflict('legacy date content has unknown ownership')
            # Insert immediately after the heading; keep every existing byte.
            edits.append((heading.end(), heading.end(), b'\n\n' + b'\n\n'.join(new_blocks) + b'\n'))
        else:
            edits.append((len(original), len(original), b'\n\n### ' + day.replace('-', '.').encode() + b'\n\n' + b'\n\n'.join(new_blocks) + b'\n'))
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
    with path.with_name(path.name + '.tracework.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--path', required=True)
    parser.add_argument('--date', required=True)
    parser.add_argument('--bodies', required=True, help='UTF-8 JSON: exact group -> Markdown')
    parser.add_argument('--expected-file-hash', required=True, help='SHA-256 of draft snapshot, or missing')
    args = parser.parse_args()
    try:
        bodies = json.loads(Path(args.bodies).read_text(encoding='utf-8'))
        status = update(args.path, args.date, bodies, args.expected_file_hash)
        print(json.dumps({'status': status, 'path': args.path}))
        return 0
    except (OSError, ValueError) as error:
        print(json.dumps({'status': 'conflict', 'reason': str(error), 'draft': args.bodies}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
