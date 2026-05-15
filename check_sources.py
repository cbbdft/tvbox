#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TVBox 直播源检测与维护工具
- 检测 M3U 文件中所有直播源的可用性
- 自动过滤失效源
- 生成检测报告
- 支持定时维护

作者: Senior Developer
更新日期: 2026-05-15
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import requests


def parse_m3u_file(file_path):
    """解析 M3U 文件，提取频道信息和 URL"""
    channels = []
    current_channel = {}

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()

            if line.startswith('#EXTINF'):
                # 提取频道名称
                match = re.search(r',(.+)$', line)
                if match:
                    current_channel['name'] = match.group(1).strip()

                # 提取分组
                group_match = re.search(r'group-title="([^"]+)"', line)
                if group_match:
                    current_channel['group'] = group_match.group(1)

                # 提取 LOGO
                logo_match = re.search(r'logo="([^"]+)"', line)
                if logo_match:
                    current_channel['logo'] = logo_match.group(1)

            elif line.startswith('#EXTM3U'):
                continue

            elif line and not line.startswith('#'):
                # 这是 URL 行
                if current_channel.get('name'):
                    current_channel['url'] = line
                    channels.append(current_channel.copy())
                    current_channel.clear()

    return channels


def test_channel_url(url, timeout=5):
    """测试单个 URL 是否可用"""
    try:
        resp = requests.head(url, timeout=timeout, allow_redirects=True)
        return resp.status_code == 200
    except requests.exceptions.RequestException:
        try:
            resp = requests.get(url, timeout=timeout, stream=True)
            available = resp.status_code == 200
            resp.close()
            return available
        except requests.exceptions.RequestException:
            return False


def test_channels(channels, max_concurrent=10):
    """批量测试频道可用性"""
    results = {'available': [], 'unavailable': [], 'total': len(channels)}

    for i, ch in enumerate(channels):
        if i % 20 == 0:
            print(f"  进度: {i}/{len(channels)}")

        url = ch.get('url', '')
        name = ch.get('name', 'Unknown')

        if not url:
            results['unavailable'].append({'name': name, 'reason': 'no_url'})
            continue

        # 过滤非 m3u8 或 http 开头的 URL
        if not (url.startswith('http://') or url.startswith('https://')):
            results['unavailable'].append({'name': name, 'reason': 'invalid_protocol'})
            continue

        available = test_channel_url(url)

        if available:
            results['available'].append({'name': name, 'url': url})
        else:
            results['unavailable'].append({'name': name, 'url': url, 'reason': 'timeout_or_404'})

    return results


def generate_report(results, output_file):
    """生成检测报告"""
    report = f"""# TVBox 直播源检测报告
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 统计概览
- 总频道数: {results['total']}
- ✅ 可用: {len(results['available'])} ({len(results['available'])/results['total']*100:.1f}%)
- ❌ 失效: {len(results['unavailable'])} ({len(results['unavailable'])/results['total']*100:.1f}%)

## 可用频道列表
| 序号 | 频道名称 | 直播源 URL |
|------|----------|------------|
"""

    for i, ch in enumerate(results['available'], 1):
        report += f"| {i} | {ch['name']} | `{ch['url']}` |\n"

    report += f"""
## 失效频道列表
| 序号 | 频道名称 | 原因 |
|------|----------|------|
"""

    for i, ch in enumerate(results['unavailable'], 1):
        report += f"| {i} | {ch['name']} | {ch.get('reason', 'unknown')} |\n"

    report += """
---
> 数据来源: live.zbds.top (每6小时自动更新)
> 维护工具: tvbox_source_checker.py
"""

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)

    return output_file


def filter_working_channels(input_m3u, output_m3u, results):
    """生成只包含可用频道的 M3U 文件"""
    available_urls = {ch['url'] for ch in results['available']}
    available_names = {ch['name'] for ch in results['available']}

    header = "#EXTM3U x-tvg-url=\"\"\n"
    header += "#=============================\n"
    header += f"# 直播源 - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    header += f"# 可用频道: {len(results['available'])}/{results['total']}\n"
    header += "#=============================\n\n"

    with open(input_m3u, 'r', encoding='utf-8') as fin, open(output_m3u, 'w', encoding='utf-8') as fout:
        fout.write(header)

        current_lines = []
        for line in fin:
            line = line.rstrip('\n')

            if line.startswith('#EXTINF'):
                # 检查前面的内容是否是要保存的
                name_match = re.search(r',(.+)$', line)
                if name_match:
                    name = name_match.group(1).strip()
                    # 保留当前行
                    current_lines.append(line)

            elif line.startswith('#EXTM3U'):
                pass  # 已写入 header

            elif line and not line.startswith('#'):
                # URL 行
                if line in available_urls:
                    current_lines.append(line)
                    fout.write('\n'.join(current_lines) + '\n')
                    fout.write('\n')
                    current_lines = []

    return output_m3u


def main():
    print("=" * 60)
    print("  TVBox 直播源检测工具")
    print("=" * 60)
    print()

    # 配置
    base_dir = Path(__file__).parent.parent
    m3u_file = base_dir / 'sources' / 'zbds_cctv_satellite.m3u'
    report_file = base_dir / 'sources' / 'source_report.md'
    filtered_file = base_dir / 'sources' / 'zbds_cctv_satellite_filtered.m3u'

    if not m3u_file.exists():
        print(f"错误: 找不到 M3U 文件: {m3u_file}")
        sys.exit(1)

    print(f"[1/4] 解析 M3U 文件: {m3u_file.name}")
    channels = parse_m3u_file(str(m3u_file))
    print(f"      找到 {len(channels)} 个频道")
    print()

    print(f"[2/4] 开始检测源可用性...")
    results = test_channels(channels)
    print()

    print(f"[3/4] 生成检测报告...")
    generate_report(results, str(report_file))
    print(f"      报告已保存: {report_file.name}")
    print()

    print(f"[4/4] 生成可用频道列表...")
    filter_working_channels(str(m3u_file), str(filtered_file), results)
    print(f"      可用频道文件: {filtered_file.name}")
    print()

    print("=" * 60)
    print(f"  检测完成!")
    print(f"  ✅ 可用: {len(results['available'])}/{results['total']}")
    print(f"  ❌ 失效: {len(results['unavailable'])}/{results['total']}")
    print("=" * 60)

    # 返回状态码（用于 CI/CD）
    if len(results['available']) == 0:
        sys.exit(2)  # 全部失效
    elif len(results['available']) < results['total'] * 0.5:
        sys.exit(1)  # 超过一半失效


if __name__ == '__main__':
    main()
