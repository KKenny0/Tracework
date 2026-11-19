#!/usr/bin/env python3
"""
split_daily_note.py - 按月拆分 Daily Note.md

职责：
- 读取 Daily Note.md
- 识别年/月/日标题层级
- 将同月内容合并输出为 YYYY-MM.md
- 不做任何内容改写、总结或归纳

用法：
    python split_daily_note.py <input_file> <output_dir> [--month-filter YYYY-MM] [--overwrite-policy overwrite|append|skip_existing]
"""

import argparse
import os
import re
import sys
from collections import OrderedDict
from datetime import date


# --- 标题识别正则 ---
RE_YEAR = re.compile(r'^#\s*\d{4}\s*年')
RE_MONTH = re.compile(r'^##\s*(\d{4})\s*年\s*(\d{1,2})\s*月')
RE_DATE = re.compile(r'^###\s*(\d{4})[.-](\d{2})[.-](\d{2})')
OUTER_DATE = re.compile(r'###[ \t]+(\d{4})[.-](\d{2})[.-](\d{2})[ \t]*')
FENCE = re.compile(r'^ {0,3}(`{3,}|~{3,})(.*)$')
MANAGED_MARKER = re.compile(
    r'<!-- tracework:daily date=(\d{4}-\d{2}-\d{2}) group=[0-9a-f]+ sha256=[0-9a-f]{64} -->\r?\n'
    r'|(<!-- /tracework:daily -->)|tracework:daily'
)


def is_outer_boundary(line):
    heading = line.rstrip('\r\n')
    if RE_YEAR.match(heading) or RE_MONTH.match(heading):
        return True
    match = OUTER_DATE.fullmatch(heading)
    if match:
        try:
            date(*map(int, match.groups()))
        except ValueError:
            return False
        return True
    return False

# 保留月标题之前的所有内容作为文件头（如 TODO LIST 等不属于任何月份的内容）
# 但实际上 Daily Note 结构是 年 > 月 > 日，我们按月切分即可


def parse_daily_note(filepath, month_filter=None):
    """
    解析 Daily Note.md，按月归集内容。

    返回：
        OrderedDict: key 为 "YYYY-MM"，value 为该月的原始行列表（含月标题和日标题）
        list: 文件头部行（第一个月标题之前的所有行）
    """
    with open(filepath, 'r', encoding='utf-8', newline='') as f:
        lines = f.readlines()

    months = OrderedDict()
    header_lines = []
    current_month = None
    found_first_month = False
    managed = False
    fence = None

    for line in lines:
        if managed:
            if fence is None and is_outer_boundary(line):
                if month_filter is None or current_month == month_filter:
                    raise ValueError('Unclosed managed Daily block')
                managed = False
                current_month = None
            else:
                marker = FENCE.match(line.rstrip('\r\n'))
                if marker:
                    if fence and marker[1].startswith(fence) and not marker[2].strip(' \t'):
                        fence = None
                    elif fence is None and (marker[1][0] == '~' or '`' not in marker[2]):
                        fence = marker[1]

        markers = list(MANAGED_MARKER.finditer(line))
        if managed or markers:
            for marker in markers:
                if marker[1]:
                    if managed or marker[1][:7] != current_month:
                        raise ValueError('Unexpected managed Daily block start')
                    managed = True
                elif marker[2] and managed:
                    managed = False
                    fence = None
                else:
                    raise ValueError('Damaged or unmatched managed Daily marker')
            # The marker hash covers the original body bytes, including line endings.
            months[current_month].append(line)
            continue
        stripped = line.strip()

        # 检测月标题
        month_match = RE_MONTH.match(stripped)
        if month_match:
            found_first_month = True
            year = int(month_match.group(1))
            month = int(month_match.group(2))
            current_month = f"{year:04d}-{month:02d}"
            if current_month not in months:
                months[current_month] = []
            months[current_month].append(line)
            continue

        # 检测年标题
        if RE_YEAR.match(stripped):
            found_first_month = True
            # 年标题不计入任何月份，但会在输出时作为上下文参考
            continue

        # 检测日标题 —— 日标题一定属于当前月
        # 如果没有月级标题，从日期推断月份
        date_match = RE_DATE.match(stripped)
        if date_match:
            found_first_month = True
            year = int(date_match.group(1))
            month = int(date_match.group(2))
            inferred_month = f"{year:04d}-{month:02d}"
            if inferred_month != current_month:
                # 月份切换（或首次推断）
                current_month = inferred_month
                if current_month not in months:
                    months[current_month] = []
            months[current_month].append(line)
            continue

        # 如果还没遇到第一个月标题，视为文件头
        if not found_first_month:
            header_lines.append(line)
        elif current_month is not None:
            # 属于当前月份的内容行
            months[current_month].append(line)
        else:
            # 在年标题之后、月标题之前的内容，暂存到 header
            # 这种情况在格式规范的文件中不应出现
            header_lines.append(line)

    if managed and (month_filter is None or current_month == month_filter):
        raise ValueError('Unclosed managed Daily block')
    return months, header_lines


def write_month_file(output_dir, month_key, lines, overwrite_policy):
    """
    将一个月的内容写入 YYYY-MM.md 文件。

    参数：
        output_dir: 输出目录
        month_key: "YYYY-MM" 格式
        lines: 该月的所有原始行
        overwrite_policy: overwrite | append | skip_existing
    """
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, f"{month_key}.md")

    if os.path.exists(filepath):
        if overwrite_policy == 'skip_existing':
            return filepath, 'skipped'
        elif overwrite_policy == 'append':
            with open(filepath, 'a', encoding='utf-8', newline='') as f:
                f.write('\n')
                f.writelines(lines)
            return filepath, 'appended'

    # overwrite 或文件不存在
    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        f.writelines(lines)

    return filepath, 'created'


def main():
    parser = argparse.ArgumentParser(description='按月拆分 Daily Note.md')
    parser.add_argument('input_file', help='Daily Note.md 文件路径')
    parser.add_argument('output_dir', help='输出目录路径')
    parser.add_argument('--month-filter', default=None,
                        help='只处理指定月份，格式 YYYY-MM')
    parser.add_argument('--overwrite-policy', default='overwrite',
                        choices=['overwrite', 'append', 'skip_existing'],
                        help='已有文件的处理策略 (默认: overwrite)')

    args = parser.parse_args()

    # 验证输入文件
    if not os.path.isfile(args.input_file):
        print(f"错误：输入文件不存在 - {args.input_file}", file=sys.stderr)
        sys.exit(1)

    # 解析
    try:
        months, header_lines = parse_daily_note(args.input_file, args.month_filter)
    except (OSError, ValueError) as error:
        parser.exit(1, f'{error}\n')

    if not months:
        print("错误：未识别到任何月份内容。请检查文件格式。", file=sys.stderr)
        sys.exit(1)

    # 过滤月份
    if args.month_filter:
        if args.month_filter not in months:
            print(f"错误：指定月份 {args.month_filter} 在文件中未找到。", file=sys.stderr)
            print(f"可用月份：{', '.join(months.keys())}", file=sys.stderr)
            sys.exit(1)
        months = OrderedDict([(args.month_filter, months[args.month_filter])])

    # 写出
    results = []
    for month_key, lines in months.items():
        filepath, action = write_month_file(
            args.output_dir, month_key, lines, args.overwrite_policy
        )
        results.append({'month': month_key, 'file': filepath, 'action': action})

    # 输出摘要
    print(json_dumps_summary(results))
    return results


def json_dumps_summary(results):
    """生成执行摘要的 JSON 字符串。"""
    import json
    summary = {
        'months_created': [r['month'] for r in results if r['action'] == 'created'],
        'months_updated': [r['month'] for r in results if r['action'] == 'appended'],
        'months_skipped': [r['month'] for r in results if r['action'] == 'skipped'],
        'total_months_processed': len(results),
    }
    return json.dumps(summary, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()
