import urllib.request, ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Download the live source
url = 'https://jihulab.com/Liangmyjj/tvboxx/-/raw/main/LOVE/%E6%96%B0IP%E7%99%BE%E4%BA%8B%E9%80%9A.txt'
req = urllib.request.Request(url, headers={'User-Agent': 'TVBox/1.0'})
resp = urllib.request.urlopen(req, timeout=15, context=ctx)
data = resp.read()
text = data.decode('utf-8', errors='replace')

# Parse into M3U format
epg_url = 'https://epg.112114.xyz/?ch={name}&date={date}'
lines = text.strip().split('\n')
m3u_lines = ['#EXTM3U x-tvg-url="' + epg_url + '"']
count = 0
for line in lines:
    line = line.strip()
    if not line or ',' not in line:
        continue
    parts = line.split(',', 1)
    name = parts[0].strip()
    url2 = parts[1].strip()
    if name and url2 and url2.startswith('http'):
        if '4K' in name or '4k' in name.lower():
            grp = '4K超高清'
        elif 'CCTV' in name or '央视' in name:
            grp = '央视频道'
        elif '珠江' in name or '广东' in name or '广州' in name:
            grp = '广东频道'
        elif '凤凰' in name:
            grp = '凤凰卫视'
        else:
            grp = '其他'
        m3u_lines.append('#EXTINF:-1 tvg-id="" group-title="' + grp + '",' + name)
        m3u_lines.append(url2)
        count += 1

print('Parsed', count, 'channels')
m3u_content = '\n'.join(m3u_lines)
with open(r'C:\Users\Administrator\.openclaw\workspace\tvbox\sources\yinzuo_live.m3u', 'w', encoding='utf-8') as f:
    f.write(m3u_content)
print('Saved yinzuo_live.m3u')
print('Total lines:', len(m3u_lines))
for l in m3u_lines[:10]:
    print(l)