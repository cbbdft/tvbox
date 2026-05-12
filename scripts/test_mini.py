# Minimal test - just fetch one URL
import urllib.request, ssl, json

LOG = 'C:/Users/Administrator/.openclaw/workspace/tvbox/sources/test_log.txt'

def log(msg):
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(str(msg) + '\n')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

urls = [
    ('https://raw.githubusercontent.com/YanG-1989/m3u/main/Gather.m3u', 'YanG'),
    ('https://raw.githubusercontent.com/gnodgl/IPTV/master/CCTV.m3u', 'gnodgl'),
    ('https://raw.githubusercontent.com/cuikaipeng/IPTV/main/CCTV.m3u', 'cuikaipeng'),
]

with open(LOG, 'w') as f:
    f.write('Start\n')

for url, name in urls:
    log(f'Testing {name}...')
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            content = resp.read().decode('utf-8', errors='ignore')
            log(f'  OK: {len(content)} bytes')
    except Exception as e:
        log(f'  FAIL: {e}')

log('Done')
print('Check log file')