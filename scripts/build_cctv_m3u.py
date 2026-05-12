#!/usr/bin/env python3
"""
抓取CCTV+省级频道，生成可用M3U（快速版：无逐个验证，按规则过滤）
"""
import urllib.request, ssl, os, re

for k in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'all_proxy', 'ALL_PROXY']:
    os.environ.pop(k, None)

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
proxy_handler = urllib.request.ProxyHandler({})
opener = urllib.request.build_opener(proxy_handler)
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', 'Referer': 'https://github.com/'}

SOURCES = [
    ('vbskycn',      'https://live.zhoujie218.top/tv/iptv4.m3u'),
    ('BigBigGrandG', 'https://raw.githubusercontent.com/BigBigGrandG/IPTV-URL/release/Gather.m3u'),
    ('Kimentanm',    'https://raw.githubusercontent.com/Kimentanm/aptv/master/m3u/iptv.m3u'),
    ('Guovin',       'https://raw.githubusercontent.com/Guovin/iptv-api/gd/output/result.m3u'),
]

# 目标关键词
TARGET = [
    'CCTV', '央视', 'CETV', 'CGTN',
    '东方卫视', '浙江卫视', '江苏卫视', '安徽卫视', '湖南卫视',
    '北京卫视', '天津卫视', '河北卫视', '山西卫视', '内蒙古卫视',
    '辽宁卫视', '吉林卫视', '黑龙江卫视', '上海卫视', '福建卫视',
    '江西卫视', '山东卫视', '河南卫视', '湖北卫视', '广东卫视',
    '广西卫视', '海南卫视', '重庆卫视', '四川卫视', '贵州卫视',
    '云南卫视', '西藏卫视', '陕西卫视', '甘肃卫视', '青海卫视',
    '宁夏卫视', '新疆卫视', '深圳卫视', '厦门卫视', '青岛卫视',
    '凤凰卫视', '华视', '中视', '民视', '公视',
    'CCTV4K', 'CCTV8K', '4K', '8K',
    '第一财经', '财经', '新闻',
]

# 过滤掉这些前缀/特征
SKIP_IF_CONTAINS = ['github.com', 'github.io', 'migu', 'cmvideo', 'aliyuncs']
SKIP_IF_STARTSWITH = ['http://[', 'http://10.', 'http://192.', 'http://172.']

def fetch(url, timeout=8):
    try:
        req = urllib.request.Request(url, headers=headers)
        resp = opener.open(req, timeout=timeout)
        return resp.read().decode('utf-8', errors='replace')
    except:
        return None

def parse(text):
    if not text:
        return []
    lines = text.split('\n')
    result = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('#EXTINF:'):
            name = ''
            grp = ''
            m = re.search(r',(.+)$', line)
            if m:
                name = m.group(1).strip()
            m2 = re.search(r'group-title="([^"]+)"', line)
            if m2:
                grp = m2.group(1).strip()
            i += 1
            while i < len(lines):
                nxt = lines[i].strip()
                if nxt and not nxt.startswith('#'):
                    if nxt.startswith('http'):
                        result.append((name, nxt, grp))
                    break
                i += 1
        i += 1
    return result

def is_target(name, grp):
    n = name.lower()
    g = grp.lower() if grp else ''
    for kw in TARGET:
        if kw.lower() in n or kw.lower() in g:
            return True
    return False

def is_clean_url(url):
    for s in SKIP_IF_CONTAINS:
        if s in url:
            return False
    for s in SKIP_IF_STARTSWITH:
        if url.startswith(s):
            return False
    if 'auth=***' in url or 'key=***' in url:
        return False
    return True

def dedup_keep_first(channels):
    """按name去重，保留第一个"""
    seen = set()
    result = []
    for ch in channels:
        name = ch[0]
        if name not in seen:
            seen.add(name)
            result.append(ch)
    return result

# === 主流程 ===
print('开始抓取...')
all_channels = []

for src_name, src_url in SOURCES:
    text = fetch(src_url)
    if not text:
        print(f'FAIL [{src_name}]')
        continue
    entries = parse(text)
    matched = [e for e in entries if is_target(e[0], e[2])]
    print(f'[{src_name}] Total={len(entries)}, Matched={len(matched)}')
    all_channels.extend(matched)

print(f'抓取完成，共 {len(all_channels)} 条')

# 去重
all_channels = dedup_keep_first(all_channels)
print(f'去重后 {len(all_channels)} 条')

# 按目标过滤
clean = [(n, u, g) for n, u, g in all_channels if is_clean_url(u)]
print(f'过滤后（干净URL） {len(clean)} 条')

# 分类
cctv_chs = [(n, u, g) for n, u, g in clean if any(k in n.upper() for k in ['CCTV', 'CETV', 'CGTN', '央视'])]
prov_chs = [(n, u, g) for n, u, g in clean if not any(k in n.upper() for k in ['CCTV', 'CETV', 'CGTN', '央视'])]

print(f'\nCCTV相关: {len(cctv_chs)} 条')
print(f'省级/其他: {len(prov_chs)} 条')

# 生成 M3U
def to_m3u(channels):
    lines = ['#EXTM3U', '']
    for name, url, grp in channels:
        gid = f' tvg-group="{grp}"' if grp else ''
        lines.append(f'#EXTINF:-1 tvg-name="{name}"{gid},{name}')
        lines.append(url)
        lines.append('')
    return '\n'.join(lines)

base = 'C:/Users/Administrator/.openclaw/workspace/tvbox/sources/'

m3u_cctv = to_m3u(cctv_chs)
m3u_all = to_m3u(clean)

with open(base + 'cctv_provincial.m3u', 'w', encoding='utf-8') as f:
    f.write(m3u_all)

with open(base + 'cctv_only.m3u', 'w', encoding='utf-8') as f:
    f.write(m3u_cctv)

print(f'\n已写入:')
print(f'  cctv_provincial.m3u ({len(clean)} 频道)')
print(f'  cctv_only.m3u ({len(cctv_chs)} 频道)')

# 打印 CCTV 台列表
print('\n=== CCTV 台 ===')
for n, u, g in cctv_chs:
    print(f'  {n}')

print('\n=== 省级/其他台 ===')
for n, u, g in prov_chs:
    print(f'  {n}')
