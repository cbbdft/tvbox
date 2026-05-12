# -*- coding: utf-8 -*-
"""Step 1: Fetch all sources, save to JSON (skip slow/broken URLs)"""
import os, json, urllib.request, ssl, re

LOG = 'C:/Users/Administrator/.openclaw/workspace/tvbox/sources/step1_log.txt'
OUT = 'C:/Users/Administrator/.openclaw/workspace/tvbox/sources/fetched.json'
TIMEOUT = 12

def log(msg):
    ts = time.strftime('%H:%M:%S')
    line = f'[{ts}] {msg}'
    print(line)
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(line + '\n')

import time

def fetch(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx) as resp:
            return resp.read().decode('utf-8', errors='ignore')
    except Exception as e:
        log(f'  FAIL: {e}')
        return None

def parse_m3u(content):
    chs = []
    lines = content.split('\n')
    for i in range(len(lines) - 1):
        line = lines[i].strip()
        if line.startswith('#EXTINF:'):
            m = re.search(r',(.+)$', line)
            name = m.group(1).strip() if m else ''
            lm = re.search(r'tvg-logo="([^"]+)"', line)
            logo = lm.group(1) if lm else ''
            nl = lines[i + 1].strip()
            if nl.startswith('http'):
                chs.append({'name': name, 'url': nl, 'logo': logo})
    return chs

def parse_txt(content):
    chs = []
    for line in content.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        parts = line.rsplit(',', 1)
        if len(parts) == 2 and parts[1].strip().startswith('http'):
            chs.append({'name': parts[0].strip(), 'url': parts[1].strip(), 'logo': ''})
    return chs

def parse_json(content):
    try:
        data = json.loads(content)
    except:
        return []
    chs = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                n = item.get('name') or item.get('title') or ''
                u = item.get('url') or item.get('link') or ''
                if u and isinstance(u, str) and u.startswith('http'):
                    chs.append({'name': str(n), 'url': u, 'logo': str(item.get('logo', ''))})
        return chs
    if isinstance(data, dict):
        for key in ['channels', 'data', 'list', 'results']:
            if key in data and isinstance(data[key], list):
                for item in data[key]:
                    if isinstance(item, dict):
                        n = item.get('name') or item.get('title') or ''
                        u = item.get('url') or item.get('link') or ''
                        if u and isinstance(u, str) and u.startswith('http'):
                            chs.append({'name': str(n), 'url': u, 'logo': str(item.get('logo', ''))})
                if chs:
                    return chs
    return []

# Sources to test (avoiding slow proxy URLs like ghproxy.com)
sources = [
    ('https://raw.githubusercontent.com/YanG-1989/m3u/main/Gather.m3u', 'YanG_Gather'),
    ('https://raw.githubusercontent.com/gnodgl/IPTV/master/CCTV.m3u', 'gnodgl_CCTV'),
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

# Clear log
with open(LOG, 'w', encoding='utf-8') as f:
    f.write('')

log(f'Starting fetch of {len(sources)} sources')

results = {}
for url, name in sources:
    log(f'--- {name} ---')
    content = fetch(url)
    if content is None:
        results[name] = {'url': url, 'status': 'FAIL', 'count': 0, 'channels': []}
        continue
    if '.m3u' in url or '#EXTM3U' in content:
        chs = parse_m3u(content)
    elif url.endswith('.txt'):
        chs = parse_txt(content)
    else:
        chs = parse_json(content)
    log(f'  {len(content)} bytes -> {len(chs)} channels')
    results[name] = {'url': url, 'status': 'OK', 'count': len(chs), 'channels': chs}
    time.sleep(0.5)

# Save
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
log(f'Saved to {OUT}')
log('DONE')