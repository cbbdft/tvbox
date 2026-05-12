import urllib.request, os, re

for k in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'all_proxy', 'ALL_PROXY']:
    os.environ.pop(k, None)

proxy_handler = urllib.request.ProxyHandler({})
opener = urllib.request.build_opener(proxy_handler)
headers = {'User-Agent': 'Mozilla/5.0'}

sources = [
    ('vbskycn ipv4', 'https://live.zhoujie218.top/tv/iptv4.m3u'),
    ('vbskycn ipv6', 'https://live.zhoujie218.top/tv/iptv6.m3u'),
    ('Ftindy IPTV', 'https://raw.githubusercontent.com/Ftindy/IPTV-URL/main/IPTV.m3u'),
    ('YanG聚合', 'https://raw.githubusercontent.com/YanG-1989/m3u/main/Gather.m3u'),
    ('BigBigGrandG', 'https://raw.githubusercontent.com/BigBigGrandG/IPTV-URL/release/Gather.m3u'),
    ('Kimentanm', 'https://raw.githubusercontent.com/Kimentanm/aptv/master/m3u/iptv.m3u'),
    ('Ftindy bestv', 'https://raw.githubusercontent.com/Ftindy/IPTV-URL/main/bestv.m3u'),
    ('joevess home', 'https://raw.githubusercontent.com/joevess/IPTV/main/home.m3u8'),
    ('Guovin', 'https://raw.githubusercontent.com/Guovin/iptv-api/gd/output/result.m3u'),
]

all_cctv = {}

for name, url in sources:
    print('=== ' + name + ' ===')
    try:
        req = urllib.request.Request(url, headers=headers)
        resp = opener.open(req, timeout=8)
        text = resp.read().decode('utf-8', errors='replace')
        lines = text.split('\n')
        extinf = [l for l in lines if l.startswith('#EXTINF')]
        print('Total: ' + str(len(extinf)) + ' channels')
        
        cctv_count = 0
        for i, l in enumerate(extinf):
            m = re.search(r',(.+)$', l)
            name2 = m.group(1) if m else ''
            if 'CCTV' in name2:
                cctv_count += 1
                # find URL
                url2 = ''
                for j in range(i+1, min(i+5, len(lines))):
                    if lines[j].strip() and not lines[j].startswith('#'):
                        url2 = lines[j].strip()
                        break
                all_cctv[name2] = url2
        
        print('CCTV found: ' + str(cctv_count))
        
        for l in extinf[:3]:
            m = re.search(r',(.+)$', l)
            if m:
                print('  ' + m.group(1))
    except Exception as e:
        print('FAIL: ' + str(e)[:80])
    print()

print('=== All CCTV ===')
for ch_name, ch_url in sorted(all_cctv.items()):
    print(ch_name + ' -> ' + ch_url[:120])