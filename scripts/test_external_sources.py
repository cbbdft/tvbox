# -*- coding: utf-8 -*-
"""
TVBox 直播源验证工具 v2
专门测试外部TV源接口，返回可用的源
"""
import os
import sys
import json
import urllib.request
import ssl
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

TIMEOUT = 8
MAX_WORKERS = 8


def fetch_url(url, timeout=TIMEOUT):
    """获取URL内容"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.google.com/'
        }
        req = urllib.request.Request(url, headers=headers)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as response:
            content = response.read().decode('utf-8', errors='ignore')
            return content, response.status
    except Exception as e:
        return None, str(e)


def test_stream_url(url, timeout=8):
    """测试单个流媒体URL是否可访问"""
    if not url or not url.startswith('http'):
        return False
    try:
        req = urllib.request.Request(url, method='HEAD', headers={
            'User-Agent': 'Mozilla/5.0',
            'Referer': 'https://www.google.com/'
        })
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            ct = resp.headers.get('Content-Type', '')
            cl = resp.headers.get('Content-Length', '0')
            if resp.status == 200:
                return True
    except:
        pass
    # 试试GET
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            if resp.status == 200 and int(resp.headers.get('Content-Length', 0)) > 100:
                return True
    except:
        pass
    return False


def parse_m3u(content):
    """解析m3u内容，返回频道列表"""
    channels = []
    lines = content.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('#EXTINF:'):
            # 提取频道名
            name = ''
            logo = ''
            match = re.search(r',(.+)$', line)
            if match:
                name = match.group(1).strip()
            logo_match = re.search(r'tvg-logo="([^"]+)"', line)
            if logo_match:
                logo = logo_match.group(1)
            # 下一行是URL
            i += 1
            if i < len(lines):
                url = lines[i].strip()
                if url.startswith('http'):
                    channels.append({'name': name, 'url': url, 'logo': logo})
        i += 1
    return channels


def parse_txt(content):
    """解析txt格式的直播源（格式: 频道名,URL）"""
    channels = []
    for line in content.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        # 格式: 频道名,http://xxx.com/xx.m3u8
        parts = line.split(',')
        if len(parts) >= 2:
            name = parts[0].strip()
            url = parts[1].strip()
            if url.startswith('http'):
                channels.append({'name': name, 'url': url, 'logo': ''})
    return channels


def parse_json(content):
    """解析TVBox JSON格式"""
    try:
        data = json.loads(content)
        channels = []
        # 兼容多种JSON格式
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    name = item.get('name', item.get('title', 'unknown'))
                    url = item.get('url', item.get('link', ''))
                    logo = item.get('logo', item.get('pic', ''))
                    if url and url.startswith('http'):
                        channels.append({'name': name, 'url': url, 'logo': logo})
        elif isinstance(data, dict):
            # 可能是 {urls: [...]} 格式
            if 'urls' in data and isinstance(data['urls'], list):
                for url in data['urls']:
                    if isinstance(url, str) and url.startswith('http'):
                        channels.append({'name': url.split('/')[-1], 'url': url, 'logo': ''})
            # 也可能是直接的channels数组
            if 'channels' in data:
                for ch in data['channels']:
                    name = ch.get('name', 'unknown')
                    url = ch.get('url', '')
                    logo = ch.get('logo', '')
                    if url:
                        channels.append({'name': name, 'url': url, 'logo': logo})
        return channels
    except:
        return []


def test_source_url(source_url, source_name=''):
    """测试一个源URL，返回其中可用的频道"""
    print(f"\n{'='*60}")
    print(f"测试源: {source_url}")

    content, status = fetch_url(source_url)
    if not content:
        print(f"[FAIL] 获取失败: {status}")
        return None

    print(f"[OK] 获取成功，内容长度: {len(content)} 字符")

    # 判断格式
    channels = []
    if 'm3u' in source_url.lower() or '#EXTM3U' in content:
        print("  -> 检测为 M3U 格式")
        channels = parse_m3u(content)
    elif source_url.endswith('.txt') or ',' in content.split('\n')[0]:
        print("  -> 检测为 TXT 格式")
        channels = parse_txt(content)
    elif source_url.endswith('.json') or source_url.endswith('.jsonp'):
        print("  -> 检测为 JSON 格式")
        channels = parse_json(content)
    else:
        print("  -> 未知格式，尝试JSON解析")
        channels = parse_json(content)

    print(f"  -> 解析出 {len(channels)} 个频道")

    if not channels:
        print(f"  -> 内容预览: {content[:200]}...")
        return None

    # 测试每个频道
    print(f"  -> 开始测试频道可用性 (超时{TIMEOUT}s)...")

    working = []
    not_working = []

    for i, ch in enumerate(channels):
        if i < 3 or i == len(channels) - 1:
            print(f"    [{i+1}/{len(channels)}] {ch['name']} ... ", end='', flush=True)
        is_ok = test_stream_url(ch['url'])
        if is_ok:
            print(f"OK")
            working.append(ch)
        else:
            if i < 3 or i == len(channels) - 1:
                print(f"FAIL")
            not_working.append(ch)

    print(f"\n  -> 结果: {len(working)}/{len(channels)} 可用")

    if working:
        return {
            'source': source_url,
            'name': source_name or source_url.split('/')[-1],
            'channels': working,
            'stats': {'total': len(channels), 'working': len(working), 'failed': len(not_working)}
        }
    return None


def main():
    # 测试候选源列表（从搜索结果中筛选）
    candidates = [
        ('https://raw.githubusercontent.com/kakaxi-1/IPTV/main/ipv4.1.txt', 'IPV4直播源'),
        ('https://raw.githubusercontent.com/YanG-1989/m3u/main/Gather.m3u', '聚合直播源'),
        ('https://raw.githubusercontent.com/lalifeier/IPTV/main/txt/IPTV.txt', 'IPTV TXT'),
        ('https://raw.githubusercontent.com/gnodgl/IPTV/master/CCTV.m3u', 'CCTV专版'),
        ('https://raw.githubusercontent.com/kakaxi-1/IPTV/main/ipv6.m3u', 'IPV6直播源'),
        ('https://raw.githubusercontent.com/cuikaipeng/IPTV/main/CCTV.m3u', 'CCTV2'),
        ('https://raw.githubusercontent.com/cuikaipeng/IPTV/main/IPTV.m3u', 'IPTV综合'),
    ]

    all_results = []

    for url, name in candidates:
        try:
            result = test_source_url(url, name)
            if result:
                all_results.append(result)
        except Exception as e:
            print(f"测试 {url} 时出错: {e}")
        time.sleep(0.5)

    # 汇总
    print(f"\n{'='*60}")
    print(f"[最终汇总]")
    print(f"测试了 {len(candidates)} 个源")

    total_working_channels = 0
    for r in all_results:
        stats = r['stats']
        print(f"\n{r['name']}: {stats['working']}/{stats['total']} 频道可用")
        print(f"  源: {r['source']}")
        total_working_channels += stats['working']

    print(f"\n总共 {total_working_channels} 个频道可用")

    # 生成可用源的JSON
    if all_results:
        print(f"\n{'='*60}")
        print(f"[生成可用源配置]")

        for r in all_results:
            # 输出到sources目录
            safe_name = r['name'].replace('/', '_').replace(' ', '_')
            output_file = f"C:/Users/Administrator/.openclaw/workspace/tvbox/sources/{safe_name}.json"
            output_data = {
                'name': r['name'],
                'source': r['source'],
                'channels': r['channels']
            }
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            print(f"  已保存: sources/{safe_name}.json ({len(r['channels'])}个频道)")

    print(f"\n[完成]")


if __name__ == '__main__':
    main()