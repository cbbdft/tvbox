# -*- coding: utf-8 -*-
"""
TVBox 直播源验证工具 - 简单粗暴版
直接测试每个源的几个频道，不搞花活
"""
import os
import sys
import json
import urllib.request
import ssl
import re
import time
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

TIMEOUT = 6


def fetch(url, timeout=TIMEOUT):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return resp.read().decode('utf-8', errors='ignore'), resp.status
    except Exception as e:
        return None, str(e)


def test_stream(url, timeout=5):
    if not url or not isinstance(url, str) or not url.startswith('http'):
        return False
    try:
        req = urllib.request.Request(url, method='HEAD', headers={'User-Agent': 'Mozilla/5.0'})
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return resp.status == 200
    except:
        pass
    return False


def parse_m3u(content):
    channels = []
    lines = content.split('\n')
    for i in range(len(lines) - 1):
        line = lines[i].strip()
        if line.startswith('#EXTINF:'):
            match = re.search(r',(.+)$', line)
            name = match.group(1).strip() if match else ''
            logo_m = re.search(r'tvg-logo="([^"]+)"', line)
            logo = logo_m.group(1) if logo_m else ''
            next_line = lines[i + 1].strip() if i + 1 < len(lines) else ''
            if next_line.startswith('http'):
                channels.append({'name': name, 'url': next_line, 'logo': logo})
    return channels


def parse_txt(content):
    channels = []
    for line in content.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        parts = line.rsplit(',', 1)
        if len(parts) == 2 and parts[1].strip().startswith('http'):
            channels.append({'name': parts[0].strip(), 'url': parts[1].strip(), 'logo': ''})
    return channels


def parse_json_channels(content):
    """解析各种JSON格式"""
    try:
        data = json.loads(content)
    except:
        return []

    channels = []

    # 格式1: 纯数组 [{name, url, logo}, ...]
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                name = item.get('name') or item.get('title') or item.get('tvg-name', '')
                url = item.get('url') or item.get('link') or ''
                logo = item.get('logo') or item.get('pic') or item.get('tvg-logo', '')
                if url and isinstance(url, str) and url.startswith('http'):
                    channels.append({'name': str(name), 'url': url, 'logo': str(logo)})
        return channels

    # 格式2: {channels: [...]} 或 {data: [...]}
    if isinstance(data, dict):
        for key in ['channels', 'data', 'list', 'results']:
            if key in data and isinstance(data[key], list):
                for item in data[key]:
                    if isinstance(item, dict):
                        name = item.get('name') or item.get('title') or ''
                        url = item.get('url') or item.get('link') or ''
                        logo = item.get('logo') or item.get('pic') or ''
                        if url and isinstance(url, str) and url.startswith('http'):
                            channels.append({'name': str(name), 'url': url, 'logo': str(logo)})
                if channels:
                    return channels

    return channels


def main():
    sources = [
        ('https://raw.githubusercontent.com/YanG-1989/m3u/main/Gather.m3u', 'YanG聚合'),
        ('https://raw.githubusercontent.com/gnodgl/IPTV/master/CCTV.m3u', 'CCTV'),
        ('https://raw.githubusercontent.com/cuikaipeng/IPTV/main/CCTV.m3u', 'cuikaipeng_CCTV'),
        ('https://raw.githubusercontent.com/cuikaipeng/IPTV/main/IPTV.m3u', 'cuikaipeng_IPTV'),
        ('https://raw.githubusercontent.com/MercuryZz/IPTVN/refs/heads/Files/IPTV.m3u', 'IPTVN'),
        ('https://raw.githubusercontent.com/trial/m3u/main/tv.m3u', 'trial'),
        ('https://raw.githubusercontent.com/Kimentanm/aptv/master/m3u/iptv.m3u', 'Kimentanm'),
        ('https://raw.githubusercontent.com/zbefine/iptv/main/iptv.m3u', 'zbefine'),
        ('https://raw.githubusercontent.com/lalifeier/IPTV/main/txt/IPTV.txt', 'lalifeier'),
        ('https://raw.githubusercontent.com/dxawi/0/main/0.json', 'dxawi'),
        ('https://raw.githubusercontent.com/UndCover/PyramidStore/main/py.json', 'PyramidStore'),
    ]

    print('TVBox 直播源验证')
    print('='*50)

    results = []

    for url, name in sources:
        print(f'\n[{name}] {url}')

        content, status = fetch(url)
        if not content:
            print(f'  FAIL: {status}')
            continue

        print(f'  OK: {len(content)} bytes, ', end='')

        # 解析
        if '.m3u' in url.lower() or '#EXTM3U' in content:
            chs = parse_m3u(content)
            fmt = 'M3U'
        elif url.endswith('.txt'):
            chs = parse_txt(content)
            fmt = 'TXT'
        else:
            chs = parse_json_channels(content)
            fmt = 'JSON'

        print(f'{fmt}, {len(chs)} channels')

        if not chs:
            # 打印内容前200字符看看格式
            print(f'  [预览] {content[:200]}')
            continue

        # 抽样测试前8个
        sample = chs[:8]
        working = []
        for i, ch in enumerate(sample):
            n = ch['name'][:25] if ch['name'] else '?'
            u = ch['url'][:50] if ch['url'] else '?'
            print(f'  [{i+1}] {n}', end='')
            ok = test_stream(ch['url'])
            print(f' -> {"OK" if ok else "FAIL"}')
            if ok:
                working.append(ch)
            time.sleep(0.05)

        ratio = len(working) / len(sample) if sample else 0
        print(f'  -> {len(working)}/{len(sample)} working ({ratio*100:.0f}%)')

        if working and ratio >= 0.25:
            results.append({
                'name': name,
                'url': url,
                'fmt': fmt,
                'total': len(chs),
                'working': len(working),
                'ratio': ratio,
                'channels': chs  # 全量保存
            })

    # 汇总
    print('\n' + '='*50)
    print('汇总:')
    results.sort(key=lambda x: x['ratio'], reverse=True)

    for r in results:
        print(f'  {r["name"]} ({r["fmt"]}): {r["total"]}ch, {r["working"]}/{min(8,r["total"])}sample OK ({r["ratio"]*100:.0f}%)')

    if not results:
        print('  没有可用源!')
        return

    # 保存
    print('\n保存可用源:')
    for r in results:
        fname = f'C:/Users/Administrator/.openclaw/workspace/tvbox/sources/{r["name"]}.json'
        data = {
            'name': r['name'],
            'source': r['url'],
            'total': r['total'],
            'channels': r['channels']
        }
        try:
            with open(fname, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f'  OK: sources/{r["name"]}.json ({r["total"]}ch)')
        except Exception as e:
            print(f'  FAIL: {e}')

    print('\nDone!')


if __name__ == '__main__':
    main()