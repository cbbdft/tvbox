import urllib.request, re

M3U_URL = "https://raw.githubusercontent.com/BurningC4/Chinese-IPTV/master/TV-IPV4.m3u"
EPG_URL = "https://epg.yang-1989.eu.org/epg.xml.gz"

print("Fetching M3U...")
req = urllib.request.Request(M3U_URL, headers={"User-Agent": "Mozilla/5.0"})
content = urllib.request.urlopen(req, timeout=15).read().decode("utf-8", errors="replace")
print(f"Got {len(content)} chars")

lines = content.split("\n")
m3u_lines = ['#EXTM3U x-tvg-url="{}"'.format(EPG_URL)]

count = 0
current_name = None
current_attrs = ""

for line in lines:
    line = line.strip()
    if line.startswith("#EXTINF:"):
        # Extract the attribute portion (before the last comma)
        idx = line.rfind(",")
        if idx >= 0:
            attrs = line[8:idx].strip()  # "#EXTINF:" to just before name
            current_name = line[idx+1:].strip()
            m = re.search(r'tvg-id="([^"]*)"', line)
            tvg_id = m.group(1) if m else ""
            m = re.search(r'tvg-logo="([^"]*)"', line)
            tvg_logo = m.group(1) if m else ""
            current_attrs = (attrs, tvg_id, tvg_logo)
    elif line and not line.startswith("#") and current_name:
        attrs, tvg_id, tvg_logo = current_attrs
        m3u_lines.append("#EXTINF:-1 tvg-id=\"{}\" tvg-logo=\"{}\",{}".format(tvg_id, tvg_logo, current_name))
        m3u_lines.append(line)
        count += 1
        current_name = None

print(f"Parsed {count} channels")

m3u_content = "\n".join(m3u_lines)
with open(r"C:\Users\Administrator\.openclaw\workspace\tvbox\sources\china.m3u", "w", encoding="utf-8") as f:
    f.write(m3u_content)

print(f"Saved to china.m3u ({count} channels)")
print("\nFirst 10 lines:")
for l in m3u_lines[:10]:
    print(l)
