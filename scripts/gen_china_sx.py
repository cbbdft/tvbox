import urllib.request, re

TXT_URL = "https://raw.githubusercontent.com/hgqcs/TVBox_backup/main/live.txt"
EPG_URL = "https://epg.yang-1989.eu.org/epg.xml.gz"

print("Fetching live.txt...")
req = urllib.request.Request(TXT_URL, headers={"User-Agent": "Mozilla/5.0"})
content = urllib.request.urlopen(req, timeout=15).read().decode("utf-8", errors="replace")
print(f"Got {len(content)} chars")

lines = content.split("\n")
m3u_lines = ['#EXTM3U x-tvg-url="{}"'.format(EPG_URL)]

in_sx_section = False
count = 0

for line in lines:
    line = line.strip()
    if not line:
        continue
    
    # Section detection - emoji headers
    if line.startswith("🗻"):
        in_sx_section = True
        continue
    elif line.startswith("⏰") or line.startswith("🌏"):
        in_sx_section = False
        continue
    elif line.startswith("#"):
        # Generic comment/genre marker
        in_sx_section = False
        continue
    
    # Only process if we're in the 蜀小果线 section
    if not in_sx_section:
        continue
    
    # Line like: CCTV1综合,https://php.61073736.repl.co/sxg.php?id=CCTV-1H265_4000
    if "," not in line:
        continue
    parts = line.split(",", 1)
    name = parts[0].strip()
    url = parts[1].strip()
    if not (name and url and url.startswith("http")):
        continue
    
    # Extract channel id from URL param
    m = re.search(r"id=([^&]+)", url)
    ch_id = m.group(1) if m else name
    
    # Determine group
    if "CCTV" in name:
        grp = "央视频道"
    elif "卫视" in name:
        grp = "省级卫视"
    elif "4K" in name or "超高清" in name:
        grp = "4K超高清"
    elif "CHC" in name:
        grp = "数字频道"
    elif "CETV" in name:
        grp = "教育频道"
    else:
        grp = "其他"
    
    # Simple group-title format
    m3u_lines.append('#EXTINF:-1 tvg-id="{}" group-title="{}",{}'.format(ch_id, grp, name))
    m3u_lines.append(url)
    count += 1

print(f"Parsed {count} channels from 蜀小果线")

m3u_content = "\n".join(m3u_lines)
with open(r"C:\Users\Administrator\.openclaw\workspace\tvbox\sources\china_sx.m3u", "w", encoding="utf-8") as f:
    f.write(m3u_content)

print(f"Saved to china_sx.m3u ({count} channels)")

# Verify: count lines
actual = len(m3u_content.split("\n"))
print(f"Total M3U lines: {actual}")
print(f"Header + {count} channels x 2 lines = {1 + count*2}")