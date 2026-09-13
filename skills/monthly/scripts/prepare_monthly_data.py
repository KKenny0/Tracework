#!/usr/bin/env python3
"""
prepare_monthly_data.py - 从月度归档中提取信号并构建总结骨架（单次遍历）

职责：
- 读取月度归档文件 (YYYY-MM.md)
- 识别日期块、项目标签、模块标签、类别标签、任务状态
- 提取高频关键词、风险词、下一步信号
- 按项目归并条目，统计已完成/未完成事项
- 收集风险项和下一步信号
- 输出信号 JSON + 骨架 JSON 两个文件

不做：
- 不做总结和归纳
- 不做推理性归类
- 不做内容改写
- 不做语言润色
- 不做 Markdown 渲染
- 不做脑补

用法：
    python prepare_monthly_data.py \
      --input <monthly_archive.md> \
      --signals-output <signals.json> \
      --skeleton-output <skeleton.json> \
      [--summary-mode project_focused] \
      [--evidence-mode strict] \
      [--real-projects ProjA ProjB] \
      [--real-project-min-days 2]
"""

import argparse
import calendar
from tracework_state import read_view
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


# ============================================================================
# Part 1: 信号提取（源自 extract_worklog_signals.py）
# ============================================================================

# --- 识别正则 ---
RE_DATE = re.compile(r'^###\s*(\d{4})[.-](\d{2})[.-](\d{2})')
# 项目标签：- [项目名]，排除 [x] 和 [ ] 任务标记
RE_PROJECT = re.compile(r'^-\s*\[([^\]]+)\]')
RE_MODULE = re.compile(r'^(\t| {4})-\s*\{([^}]+)\}')
RE_CATEGORY = re.compile(r'【([^】]+)】')
RE_TASK_DONE = re.compile(r'^\s*-\s*\[x\]')
RE_TASK_TODO = re.compile(r'^\s*-\s*\[\s*\]')
RE_REPORT_FIELD = re.compile(
    r'^\s*-\s*(工作流|收口类型|状态|进展|影响|风险/问题|风险|问题|下一步|来源/证据边界|证据边界)[：:]\s*(.*)$'
)

# --- 信号词库 ---
STATUS_COMPLETE = frozenset([
    '完成', '已完成', '已接入', '已验证', '已修复', '已落地', '交付', '上线',
])
STATUS_IN_PROGRESS = frozenset([
    '调整中', '优化中', '联调中', '测试中', '迭代中', '开发中', '重构中',
])
RISK_WORDS = frozenset([
    '风险', '问题', '阻塞', '不稳定', '兼容性', '待确认', '未验证', '异常', '崩溃', '死锁',
])
NEXT_ACTION_WORDS = frozenset([
    '下一步', '后续', '待补', '计划', '准备', '需要继续', '待开工',
])

# --- 已知的有效工作类别 ---
VALID_CATEGORIES = frozenset([
    '能力升级', '结构变更', '问题定位', '配置调整', '文档优化', '阶段总结', '阶段冻结',
])

# --- 常见无意义词过滤 ---
STOP_WORDS = frozenset([
    '的', '了', '在', '是', '和', '与', '或', '等', '到', '为', '对', '从',
    '将', '可', '被', '让', '用', '以', '及', '其', '该', '这', '那',
    '中', '上', '下', '内', '外', '前', '后', '之', '时', '里',
    '一', '个', '不', '有', '无', '也', '都', '还', '会', '能',
    '已', '新', '多', '更', '最', '所', '如', '而', '但', '使',
    '行', '点', '做', '加', '含', '项', '类', '组', '批', '套',
    # Daily Note 结构短语
    '今日进展', '当前应用', '新增', '支持', '移除',
    '确保', '添加', '优化', '使用', '增强', '实现', '更新',
    '修复', '改进', '集成', '引入', '统一', '规范化',
    '提升', '简化', '明确', '强制', '完善', '重构',
])


def get_indent_level(line):
    """计算行首缩进层级。兼容 Tab 和 4 空格缩进。"""
    count = 0
    for ch in line:
        if ch == '\t':
            count += 1
        elif ch == ' ':
            pass  # 空格计入但不单独计数，按 4 空格 = 1 层级
        else:
            break
    # 计算前导空格数
    spaces = 0
    for ch in line:
        if ch == ' ':
            spaces += 1
        else:
            break
    # 如果前导空白全是空格，按 4 空格 = 1 层级
    if count == 0 and spaces > 0:
        return spaces // 4
    # 混合缩进：tab 数 + 剩余空格按比例
    return count + (spaces % 4) // 4


def extract_project(line):
    """从 `- [项目名]` 格式中提取项目名，排除 [x] 和 [ ] 任务标记。"""
    m = RE_PROJECT.match(line.strip())
    if m:
        name = m.group(1).strip()
        # 排除任务标记：x, 空格, 纯空白
        if name and name not in ('x', 'X') and not re.match(r'^\s*$', m.group(1)):
            return name
    return None


def extract_module(line):
    """从 `\t- {模块名}` 或 `    - {模块名}` 格式中提取模块名。"""
    m = RE_MODULE.match(line)
    return m.group(2) if m else None


def extract_categories(text):
    """从文本中提取所有 `【类别】` 标签，只保留已知有效类别。"""
    found = RE_CATEGORY.findall(text)
    return [c for c in found if c in VALID_CATEGORIES]


def extract_status_signals(text):
    """从文本中提取状态信号。"""
    signals = []
    for word in STATUS_COMPLETE:
        if word in text:
            signals.append(word)
    for word in STATUS_IN_PROGRESS:
        if word in text:
            signals.append(word)
    return signals


def extract_risk_signals(text):
    """从文本中提取风险信号。"""
    if is_no_risk_text(text):
        return []
    signals = []
    for word in RISK_WORDS:
        if word in text:
            signals.append(word)
    return signals


def extract_next_action_signals(text):
    """从文本中提取下一步信号。"""
    signals = []
    for word in NEXT_ACTION_WORDS:
        if word in text:
            signals.append(word)
    return signals


def extract_evidence_boundary(text):
    """从来源/证据边界字段中提取 evidence boundary。"""
    for boundary in ('verified', 'recorded', 'limited'):
        if boundary in text:
            return boundary
    return ''


def is_no_risk_text(text):
    """识别新日报格式里明确声明无风险的占位句。"""
    normalized = re.sub(r'\s+', '', text or '')
    return normalized in {
        '无',
        '暂无',
        '无明确风险',
        '无明确问题',
        '无明确风险记录',
        '无风险记录',
        '无风险/问题',
        '无风险问题',
    }


def extract_keywords(text, top_n=20):
    """
    从文本中提取高频关键词。
    使用简单的分词策略：按中文词和英文短语切分。
    """
    # 提取中文短语（2-6字）和英文短语
    cn_phrases = re.findall(r'[\u4e00-\u9fff]{2,6}', text)
    en_phrases = re.findall(r'[A-Za-z][A-Za-z0-9_]+', text)

    # 过滤停用词和太短的词
    cn_filtered = [p for p in cn_phrases if p not in STOP_WORDS and len(p) >= 2]
    en_filtered = [p for p in en_phrases if len(p) >= 3]

    counter = Counter(cn_filtered + en_filtered)
    return [word for word, count in counter.most_common(top_n)]


def parse_monthly_file(filepath, month_key=None):
    """
    解析月度归档文件，提取结构化信号。

    返回：
        dict: 月度信号数据
    """
    text = Path(filepath).read_text(encoding='utf-8') if filepath else ''
    editorial_context = []

    def keep_editorial(match):
        day, group_hex, body = match.groups()
        try:
            group = bytes.fromhex(group_hex).decode('utf-8')
        except (ValueError, UnicodeError):
            group = 'unassigned'
        if not month_key or day.startswith(month_key):
            editorial_context.append({'date': day, 'reporting_group': group,
                                      'text': body, 'source': 'daily_prose',
                                      'evidence_boundary': 'editorial_only'})
        return ''

    text = re.sub(
        r'<!-- tracework:daily date=(\d{4}-\d{2}-\d{2}) group=([0-9a-f]+) sha256=[0-9a-f]{64} -->\r?\n(.*?)<!-- /tracework:daily -->',
        keep_editorial, text, flags=re.S)
    lines = text.splitlines(keepends=True)
    month_key = month_key or (Path(filepath).stem if filepath else 'unknown')

    entries = []
    current_date = None
    current_entry = None

    # 全文文本，用于关键词提取
    all_text = []

    # 任务子条目追踪状态
    current_task = None      # {'task': str, 'details': [], '_indent': int}
    current_task_key = None  # 'completed_tasks' or 'incomplete_tasks'
    current_project = None

    for line in lines:
        stripped = line.strip()

        # 检测日期标题
        date_match = RE_DATE.match(stripped)
        if date_match:
            # 保存上一个 entry
            if current_entry:
                # 完成未结束的任务收集
                if current_task is not None:
                    current_entry[current_task_key].append(
                        {'task': current_task['task'], 'details': current_task['details']}
                    )
                    current_task = None
                current_entry['raw_text'] = '\n'.join(current_entry.pop('_lines', []))
                entries.append(current_entry)

            year, month, day = date_match.groups()
            current_date = f"{year}.{month}.{day}"
            current_entry = {
                'date': current_date,
                'daily_focus': '',
                'projects': [],
                'modules': [],
                'categories': [],
                'report_items': [],
                'evidence_boundaries': [],
                'completed_tasks': [],
                'incomplete_tasks': [],
                'status_signals': [],
                'risk_signals': [],
                'next_action_signals': [],
                'topics': [],
                '_lines': [line],  # 临时保存原始行
            }
            current_project = None
            continue

        if current_entry is None:
            continue

        current_entry['_lines'].append(line)
        all_text.append(stripped)

        # 提取项目标签
        project = extract_project(stripped)
        if project:
            current_entry['projects'].append(project)
            current_project = project

        # 提取模块标签
        module = extract_module(line)
        if module:
            current_entry['modules'].append(module)

        # 提取类别标签（只保留已知有效类别）
        categories = extract_categories(stripped)
        if categories:
            current_entry['categories'].extend(categories)

        report_match = RE_REPORT_FIELD.match(stripped)
        if report_match:
            field, value = report_match.groups()
            value = value.strip()
            report_item = {
                'project': current_project,
                'field': field,
                'text': value,
            }
            boundary = extract_evidence_boundary(value)
            if boundary:
                report_item['evidence_boundary'] = boundary
                current_entry['evidence_boundaries'].append(boundary)
            current_entry['report_items'].append(report_item)
            if field in {'状态', '进展', '影响'}:
                current_entry['status_signals'].extend(extract_status_signals(value))
            if field in {'风险/问题', '风险', '问题'}:
                if not is_no_risk_text(value):
                    current_entry['risk_signals'].extend(extract_risk_signals(value) or ['report-risk'])
            if field == '下一步':
                current_entry['next_action_signals'].extend(
                    extract_next_action_signals(value) or ['report-next-action']
                )

        # --- 任务与子条目追踪 ---
        is_done = bool(RE_TASK_DONE.match(stripped))
        is_todo = bool(RE_TASK_TODO.match(stripped))

        if is_done or is_todo:
            # 完成上一条任务的子条目收集
            if current_task is not None:
                current_entry[current_task_key].append(
                    {'task': current_task['task'], 'details': current_task['details']}
                )
            # 开始新任务
            task_desc = re.sub(r'^\s*-\s*\[(?:x|\s*)\]\s*', '', stripped)
            if task_desc:
                current_task = {
                    'task': task_desc,
                    'details': [],
                    '_indent': get_indent_level(line),
                }
                current_task_key = 'completed_tasks' if is_done else 'incomplete_tasks'
            else:
                current_task = None
        elif current_task is not None:
            task_indent = current_task['_indent']
            line_indent = get_indent_level(line)
            if stripped.startswith('- ') and line_indent > task_indent:
                # 子条目：比父任务缩进更深的列表项
                detail_text = re.sub(r'^-\s*', '', stripped)
                if detail_text:
                    current_task['details'].append(detail_text)
            elif stripped and line_indent <= task_indent:
                # 缩进回退或有内容行回到同级，结束当前任务收集
                current_entry[current_task_key].append(
                    {'task': current_task['task'], 'details': current_task['details']}
                )
                current_task = None

        # 提取当日焦点
        if stripped.startswith('>') and '当日焦点' in stripped:
            focus = re.sub(r'^>\s*\U0001f3af?\s*当日焦点[：:]\s*', '', stripped).strip()
            if focus:
                current_entry['daily_focus'] = focus

        # 提取各类信号
        current_entry['status_signals'].extend(extract_status_signals(stripped))
        current_entry['risk_signals'].extend(extract_risk_signals(stripped))
        current_entry['next_action_signals'].extend(extract_next_action_signals(stripped))

        # 提取内联状态标记（出现在列表项中的 【后续动作】【进行中】【待执行】【性能优化】等）
        inline_markers = re.findall(r'【(后续动作|进行中|待执行|性能优化)】', stripped)
        if inline_markers:
            for marker in inline_markers:
                if marker == '后续动作':
                    current_entry['next_action_signals'].append('【后续动作】')
                elif marker == '进行中':
                    current_entry['status_signals'].append('【进行中】')
                elif marker == '待执行':
                    current_entry['next_action_signals'].append('【待执行】')
                elif marker == '性能优化':
                    current_entry['status_signals'].append('【性能优化】')

    # 保存最后一个 entry
    if current_entry:
        if current_task is not None:
            current_entry[current_task_key].append(
                {'task': current_task['task'], 'details': current_task['details']}
            )
        current_entry['raw_text'] = '\n'.join(current_entry.pop('_lines', []))
        entries.append(current_entry)

    # 去重信号
    for entry in entries:
        entry['status_signals'] = list(set(entry['status_signals']))
        entry['risk_signals'] = list(set(entry['risk_signals']))
        entry['next_action_signals'] = list(set(entry['next_action_signals']))
        entry['projects'] = list(dict.fromkeys(entry['projects']))  # 去重保序
        entry['modules'] = list(dict.fromkeys(entry['modules']))
        entry['categories'] = list(dict.fromkeys(entry['categories']))
        entry['evidence_boundaries'] = list(dict.fromkeys(entry.get('evidence_boundaries', [])))

    # 全局关键词提取
    all_text_str = '\n'.join(all_text)
    global_keywords = extract_keywords(all_text_str)

    # 全局项目汇总
    all_projects = list(dict.fromkeys(
        p for entry in entries for p in entry['projects']
    ))

    # 全局类别汇总
    all_categories = list(dict.fromkeys(
        c for entry in entries for c in entry['categories']
    ))

    return {
        'month': month_key,
        'total_days': len(entries),
        'projects_detected': all_projects,
        'categories_detected': all_categories,
        'high_frequency_topics': global_keywords,
        'entries': entries,
        'editorial_context': editorial_context,
    }


def load_monthly_raw_entries(vault_path, month_key, project_slugs=None, as_of=None, views=None):
    """Load raw entries for the month without rewriting or interpreting them."""
    vault = Path(vault_path).expanduser().resolve()
    weeks_dir = vault / 'raw' / 'weeks'
    projects_file = vault / 'raw' / 'projects.json'
    registry = {}
    if projects_file.is_file():
        try:
            projects = json.loads(projects_file.read_text(encoding='utf-8'))
            for project in projects if isinstance(projects, list) else []:
                if not isinstance(project, dict):
                    continue
                slug = project.get('slug')
                if isinstance(slug, str) and slug:
                    registry[slug] = project
        except (json.JSONDecodeError, OSError):
            pass

    collected = []
    if not weeks_dir.is_dir():
        return collected

    slugs = project_slugs if project_slugs is not None else sorted({p.stem for p in weeks_dir.glob('*/*.json')})
    year, month = map(int, month_key.split('-'))
    end = f'{month_key}-{calendar.monthrange(year, month)[1]:02d}'
    for slug in slugs:
        view = read_view(vault, slug, month_key + '-01', end, as_of)
        if views is not None:
            views.append(view)
        project = registry.get(slug, {})
        for entry in view['entries']:
            collected.append({
                'project_slug': slug,
                'project_name': project.get('name') or slug,
                'reporting_group': project.get('reporting_group') or 'unassigned',
                'source_path': entry['_source_path'],
                'entry_index': entry['_source_index'],
                'entry': {k: v for k, v in entry.items() if not k.startswith('_')},
            })
    return collected


def build_raw_work_streams(raw_items):
    """Group raw facts without ranking them by activity volume."""
    grouped = {}
    for item in raw_items:
        entry = item.get('entry') if isinstance(item.get('entry'), dict) else {}
        project_name = item.get('project_name') or item.get('project_slug') or 'unassigned'
        reporting = entry.get('reporting') if isinstance(entry.get('reporting'), dict) else {}
        stream = (
            entry.get('work_stream')
            or reporting.get('work_stream')
            or entry.get('project_area')
            or project_name
        )
        key = (item.get('reporting_group') or 'unassigned', project_name, str(stream))
        bucket = grouped.setdefault(key, {
            'reporting_group': key[0],
            'project': key[1],
            'work_stream': key[2],
            'entries': [],
        })
        bucket['entries'].append({
            'timestamp': entry.get('timestamp'),
            'summary': entry.get('summary'),
            'status': entry.get('status'),
            'type': entry.get('type'),
            'source_path': item.get('source_path'),
            'entry_index': item.get('entry_index'),
        })
    return [grouped[key] for key in sorted(grouped)]


# ============================================================================
# Part 2: 骨架构建（源自 build_monthly_review.py）
# ============================================================================

# 默认最少出现天数阈值：出现天数 >= 此值的项目视为真实项目
DEFAULT_REAL_PROJECT_MIN_DAYS = 2


def group_by_project(entries):
    """按项目归并日志条目。"""
    project_entries = defaultdict(list)
    unassigned = []

    for entry in entries:
        if entry.get('projects'):
            for project in entry['projects']:
                project_entries[project].append(entry)
        else:
            unassigned.append(entry)

    return dict(project_entries), unassigned


def detect_real_projects(project_entries, min_days=2):
    """根据出现天数自动识别真实项目，过滤误检测（如 Markdown 链接）。

    Markdown 链接误检测的特征：项目名通常只在 1 天出现，
    且文本中包含 URL（括号开头）。
    """
    real = set()
    for project, entries in project_entries.items():
        active_days = len(set(e['date'] for e in entries))
        if active_days >= min_days:
            real.add(project)
    return sorted(real)


def collect_completed_items(project_entries):
    """收集各项目的已完成事项。"""
    result = {}
    for project, entries in project_entries.items():
        items = []
        for entry in entries:
            for task in entry.get('completed_tasks', []):
                task_text = task['task'] if isinstance(task, dict) else task
                task_details = task.get('details', []) if isinstance(task, dict) else []
                items.append({
                    'date': entry['date'],
                    'task': task_text,
                    'details': task_details,
                })
            for report_item in entry.get('report_items', []):
                if report_item.get('project') not in (project, None, ''):
                    continue
                if report_item.get('field') == '进展' and report_item.get('text'):
                    details = []
                    if report_item.get('evidence_boundary'):
                        details.append(f"evidence_boundary={report_item['evidence_boundary']}")
                    items.append({
                        'date': entry['date'],
                        'task': f"[{report_item['field']}] {report_item['text']}",
                        'details': details,
                    })
        result[project] = items
    return result


def collect_report_items(project_entries):
    """按项目收集新日报格式中的 report-led 字段。"""
    result = {}
    for project, entries in project_entries.items():
        items = []
        for entry in entries:
            for report_item in entry.get('report_items', []):
                if report_item.get('project') not in (project, None, ''):
                    continue
                items.append({
                    'date': entry['date'],
                    'field': report_item.get('field', ''),
                    'text': report_item.get('text', ''),
                    'evidence_boundary': report_item.get('evidence_boundary', ''),
                })
        result[project] = items
    return result


def collect_daily_focuses(entries):
    """收集各日期的当日焦点。"""
    focuses = []
    for entry in entries:
        focus = entry.get('daily_focus', '')
        if focus:
            focuses.append({
                'date': entry['date'],
                'focus': focus,
            })
    return focuses


def collect_incomplete_items(project_entries):
    """收集各项目的未完成/进行中事项。"""
    result = {}
    for project, entries in project_entries.items():
        items = []
        for entry in entries:
            for task in entry.get('incomplete_tasks', []):
                task_text = task['task'] if isinstance(task, dict) else task
                task_details = task.get('details', []) if isinstance(task, dict) else []
                items.append({
                    'date': entry['date'],
                    'task': task_text,
                    'details': task_details,
                })
            for signal in entry.get('status_signals', []):
                if signal in {'调整中', '优化中', '联调中', '测试中', '迭代中'}:
                    items.append({
                        'date': entry['date'],
                        'task': f"[进行中信号] {signal}",
                        'details': [],
                    })
        result[project] = items
    return result


def collect_risks(entries):
    """收集所有风险信号。"""
    risks = []
    for entry in entries:
        for signal in entry.get('risk_signals', []):
            risks.append({
                'date': entry['date'],
                'signal': signal,
                'projects': entry.get('projects', []),
            })
        for report_item in entry.get('report_items', []):
            if (
                report_item.get('field') in {'风险/问题', '风险', '问题'}
                and report_item.get('text')
                and not is_no_risk_text(report_item.get('text'))
            ):
                risks.append({
                    'date': entry['date'],
                    'signal': report_item['text'],
                    'projects': [report_item.get('project')] if report_item.get('project') else entry.get('projects', []),
                    'source': 'daily_report_field',
                })
    return risks


def collect_next_actions(entries):
    """收集所有下一步信号。"""
    actions = []
    for entry in entries:
        for signal in entry.get('next_action_signals', []):
            actions.append({
                'date': entry['date'],
                'signal': signal,
                'projects': entry.get('projects', []),
            })
        for report_item in entry.get('report_items', []):
            if report_item.get('field') == '下一步' and report_item.get('text'):
                actions.append({
                    'date': entry['date'],
                    'signal': report_item['text'],
                    'projects': [report_item.get('project')] if report_item.get('project') else entry.get('projects', []),
                    'source': 'daily_report_field',
                })
    return actions


def identify_main_threads(project_entries, high_freq_topics):
    """
    识别本月主线。
    基于项目跨度天数和高频主题，按活跃度排序。
    """
    threads = []
    for project, entries in project_entries.items():
        active_days = len(set(e['date'] for e in entries))
        categories = []
        for e in entries:
            categories.extend(e.get('categories', []))
        top_categories = [c for c, _ in Counter(categories).most_common(3)]

        threads.append({
            'project': project,
            'active_days': active_days,
            'top_categories': top_categories,
        })

    threads.sort(key=lambda t: t['active_days'], reverse=True)
    return threads


def detect_work_phases(entries):
    """按周分组，检测每月的工作阶段和重心转移。

    返回按时间排序的阶段列表，每个阶段包含日期范围、主导项目、
    主导类别和任务数量。
    """
    if not entries:
        return []

    # 按周分桶（ISO week）
    week_buckets = defaultdict(list)
    for entry in entries:
        date_str = entry['date']
        try:
            dt = datetime.strptime(date_str, '%Y.%m.%d')
            week_key = dt.isocalendar()[:2]  # (year, week_number)
        except ValueError:
            week_key = date_str
        week_buckets[week_key].append(entry)

    phases = []
    for week_key in sorted(week_buckets.keys()):
        week_entries = week_buckets[week_key]
        dates = sorted(set(e['date'] for e in week_entries))

        # 主导项目（该周出现天数最多的）
        project_day_counts = defaultdict(int)
        for entry in week_entries:
            for p in entry.get('projects', []):
                project_day_counts[p] += 1
        dominant_project = max(project_day_counts, key=project_day_counts.get) if project_day_counts else ''

        # 主导类别
        cat_counts = Counter()
        for entry in week_entries:
            cat_counts.update(entry.get('categories', []))
        top_categories = [c for c, _ in cat_counts.most_common(3)]

        # 任务数
        task_count = sum(
            len(e.get('completed_tasks', [])) + len(e.get('incomplete_tasks', []))
            for e in week_entries
        )

        phases.append({
            'period': f"{dates[0]}-{dates[-1]}" if len(dates) > 1 else dates[0],
            'work_days': len(dates),
            'dominant_project': dominant_project,
            'dominant_categories': top_categories,
            'task_count': task_count,
        })

    return phases


def build_engineering_details(entries, project_entries):
    """构建 engineering_review 模式的额外详情。"""
    details = {
        'daily_intensity': {},
    }

    for entry in entries:
        date = entry['date']
        completed = len(entry.get('completed_tasks', []))
        incomplete = len(entry.get('incomplete_tasks', []))
        details['daily_intensity'][date] = completed + incomplete

    return details


def build_review_skeleton(signals, summary_mode='project_focused', evidence_mode='strict',
                          real_projects=None, real_project_min_days=DEFAULT_REAL_PROJECT_MIN_DAYS):
    """
    构建月度总结骨架。

    参数：
        signals: 信号 JSON 数据
        summary_mode: 总结模式
        evidence_mode: 证据模式
        real_projects: 手动指定的真实项目列表（None 则自动检测）
        real_project_min_days: 自动检测的最少出现天数阈值

    返回一个 dict，包含结构化的总结数据，供 agent 生成 summary.md。
    """
    entries = signals.get('entries', [])
    month = signals.get('month', 'unknown')
    high_freq = signals.get('high_frequency_topics', [])

    # 按项目归并
    project_entries, unassigned = group_by_project(entries)

    # 识别真实项目：手动指定 或 自动检测
    if real_projects is not None:
        detected_real = sorted(real_projects)
    else:
        detected_real = detect_real_projects(project_entries, real_project_min_days)

    # 收集各维度数据
    completed = collect_completed_items(project_entries)
    report_items = collect_report_items(project_entries)
    incomplete = collect_incomplete_items(project_entries)
    risks = collect_risks(entries)
    next_actions = collect_next_actions(entries)
    main_threads = identify_main_threads(project_entries, high_freq)
    daily_focuses = collect_daily_focuses(entries)

    # 统计
    total_completed = sum(len(items) for items in completed.values())
    total_incomplete = sum(len(items) for items in incomplete.values())
    total_report_items = sum(len(items) for items in report_items.values())

    # 收集类别分布（所有模式都输出）
    all_categories = []
    for entry in entries:
        all_categories.extend(entry.get('categories', []))
    category_distribution = dict(Counter(all_categories))

    skeleton = {
        'month': month,
        'summary_mode': summary_mode,
        'evidence_mode': evidence_mode,
        'real_projects': detected_real,
        'statistics': {
            'total_days': signals.get('total_days', 0),
            'total_projects': len(project_entries),
            'total_completed_tasks': total_completed,
            'total_incomplete_tasks': total_incomplete,
            'total_report_items': total_report_items,
            'total_risk_signals': len(risks),
            'total_next_action_signals': len(next_actions),
            'total_categories': len(all_categories),
        },
        'main_threads': main_threads,
        'high_frequency_topics': high_freq[:15],
        'category_distribution': category_distribution,
        'by_project': {},
        'risks': risks,
        'next_actions': next_actions,
        'daily_focuses': daily_focuses,
        'unassigned_entries_count': len(unassigned),
        'warnings': [],
        'raw_entries': signals.get('raw_entries', []),
        'effective_views': signals.get('effective_views', []),
        'editorial_context': signals.get('editorial_context', []),
        'raw_entries_by_project': {},
        'reporting_groups': {},
        'raw_work_streams': build_raw_work_streams(signals.get('raw_entries', [])),
    }

    skeleton['current_risks'] = [dict(state, project_slug=view['project_slug'])
        for view in signals.get('effective_views', []) for state in view['states']
        if state['subject'].startswith('risk:') and state['state'] not in ('mitigated', 'resolved', 'closed', 'accepted')]
    skeleton['accepted_risks'] = [dict(state, project_slug=view['project_slug'])
        for view in signals.get('effective_views', []) for state in view['states']
        if state['subject'].startswith('risk:') and state['state'] == 'accepted']

    for raw_item in signals.get('raw_entries', []):
        project_name = raw_item.get('project_name') or raw_item.get('project_slug') or 'unassigned'
        skeleton['raw_entries_by_project'].setdefault(project_name, []).append(raw_item)
        group = raw_item.get('reporting_group') or 'unassigned'
        skeleton['reporting_groups'].setdefault(group, [])
        if project_name not in skeleton['reporting_groups'][group]:
            skeleton['reporting_groups'][group].append(project_name)

    # 按项目组织详细数据
    for project in project_entries:
        skeleton['by_project'][project] = {
            'completed_items': completed.get(project, []),
            'incomplete_items': incomplete.get(project, []),
            'report_items': report_items.get(project, []),
            'active_days': len(set(e['date'] for e in project_entries[project])),
            'is_real_project': project in set(detected_real),
        }

    if summary_mode == 'engineering_review':
        skeleton['engineering_details'] = build_engineering_details(entries, project_entries)

    # 工作阶段检测（所有模式都输出）
    skeleton['work_phases'] = detect_work_phases(entries)

    if unassigned:
        skeleton['warnings'].append(
            f"有 {len(unassigned)} 条日志条目未归属到任何项目标签"
        )
    if entries and total_completed == 0 and total_report_items == 0:
        skeleton['warnings'].append("本月未检测到明确的已完成任务或日报进展字段")
    if not signals.get('raw_entries'):
        skeleton['warnings'].append("本月无 matching raw entries；其他来源只能作为 limited 证据，无其他信号时返回空状态")
    if entries and not high_freq:
        skeleton['warnings'].append("未能提取到高频主题关键词")

    return skeleton


# ============================================================================
# Part 3: 合并主流程 - 单次遍历：解析 → 提取信号 → 构建骨架 → 写出
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='从月度归档中提取信号并构建总结骨架（单次遍历）',
    )
    parser.add_argument('--input', default=None,
                        help='月度归档文件路径 (YYYY-MM.md)')
    parser.add_argument('--signals-output', required=True,
                        help='信号 JSON 输出文件路径')
    parser.add_argument('--skeleton-output', required=True,
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
    parser.add_argument('--real-projects', nargs='*', default=None,
                        help='手动指定真实项目列表（空格分隔），默认自动检测')
    parser.add_argument('--real-project-min-days', type=int,
                        default=DEFAULT_REAL_PROJECT_MIN_DAYS,
                        help=f'自动检测真实项目的最少出现天数阈值 (默认: {DEFAULT_REAL_PROJECT_MIN_DAYS})')

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

    signals = parse_monthly_file(args.input, target_month)
    signals['effective_views'] = []
    signals['raw_entries'] = (
        load_monthly_raw_entries(args.vault, target_month, args.project_slug, args.as_of, signals['effective_views']) if args.vault else []
    )

    # light 模式：精简 signals 中的 entries
    if args.summary_mode == 'light':
        signals['entries'] = [
            {
                'date': e['date'],
                'projects': e['projects'],
                'topics': e.get('topics', []),
            }
            for e in signals['entries']
        ]

    # --- Step 2: 构建骨架 ---
    print("正在构建骨架...")
    skeleton = build_review_skeleton(
        signals, args.summary_mode, args.evidence_mode,
        real_projects=args.real_projects,
        real_project_min_days=args.real_project_min_days,
    )

    # --- Step 3: 写出两个 JSON 文件 ---
    for output_path in [args.signals_output, args.skeleton_output]:
        out_dir = os.path.dirname(output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

    with open(args.signals_output, 'w', encoding='utf-8') as f:
        json.dump(signals, f, ensure_ascii=False, indent=2)

    with open(args.skeleton_output, 'w', encoding='utf-8') as f:
        json.dump(skeleton, f, ensure_ascii=False, indent=2)

    # --- 打印处理摘要 ---
    print()
    print(f"=== 处理完成：{signals['month']} ===")
    print()
    print(f"[信号提取]")
    print(f"  日期数：{signals['total_days']}")
    print(f"  项目：{', '.join(signals['projects_detected'])}")
    print(f"  类别：{', '.join(signals['categories_detected'])}")
    print(f"  高频主题（Top 10）：{', '.join(signals['high_frequency_topics'][:10])}")
    print()
    stats = skeleton['statistics']
    print(f"[骨架构建]")
    print(f"  {stats['total_days']} 工作日 | {stats['total_projects']} 项目 | "
          f"{stats['total_completed_tasks']} 已完成 | {stats['total_incomplete_tasks']} 进行中")
    print(f"  真实项目：{', '.join(skeleton['real_projects'])}")
    if skeleton['warnings']:
        print(f"  警告：")
        for w in skeleton['warnings']:
            print(f"    - {w}")
    print()
    print(f"输出文件：")
    print(f"  信号 JSON：{args.signals_output}")
    print(f"  骨架 JSON：{args.skeleton_output}")


if __name__ == '__main__':
    main()
