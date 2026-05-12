# -*- coding: utf-8 -*-
"""
TVBox 直播源快速验证工具 v3
- 抽样测试每个源（每批取前10个频道测试）
- 自动跳过明显无效的源
- 处理编码问题
"""
import os
import sys
import json
import urllib.request
import ssl
import re
import time
import io

# 设置stdout编码为utf-8，避免windows gbk编码问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

TIMEOUT = 6
SAMPLE_SIZE = 10  # 每个源抽样测试数量


def safe_print(msg):
    """安全打印，处理编码"""
    try:
        print(msg)
    except:
        print(str(msg).encode('utf-8', errors='replace').decode('utf-8'))


def fetch_url(url, timeout=TIMEOUT):
    """获取URL内容"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
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


def test_stream_url(url, timeout=5):
    """测试单个流媒体URL是否可访问"""
    if not url or not isinstance(url, str) or not url.startswith('http'):
        return False
    try:
        req = urllib.request.Request(url, method='HEAD', headers={
            'User-Agent': 'Mozilla/5.0',
        })
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            if resp.status == 200:
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
            name = ''
            logo = ''
            match = re.search(r',(.+)$', line)
            if match:
                name = match.group(1).strip()
            logo_match = re.search(r'tvg-logo="([^"]+)"', line)
            if logo_match:
                logo = logo_match.group(1)
            i += 1
            if i < len(lines):
                url = lines[i].strip()
                if url.startswith('http'):
                    channels.append({'name': name or url.split('/')[-1], 'url': url, 'logo': logo})
        i += 1
    return channels


def parse_txt(content):
    """解析txt格式"""
    channels = []
    for line in content.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        parts = line.split(',')
        if len(parts) >= 2:
            name = parts[0].strip()
            url = parts[-1].strip()
            if url.startswith('http'):
                channels.append({'name': name, 'url': url, 'logo': ''})
    return channels


def parse_json(content):
    """解析TVBox JSON格式"""
    try:
        data = json.loads(content)
        channels = []
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    name = item.get('name', item.get('title', item.get('tvg-name', '')))
                    url = item.get('url', item.get('link', ''))
                    logo = item.get('logo', item.get('pic', item.get('tvg-logo', '')))
                    if url and isinstance(url, str) and url.startswith('http'):
                        channels.append({'name': str(name), 'url': url, 'logo': str(logo)})
        elif isinstance(data, dict):
            if 'channels' in data and isinstance(data['channels'], list):
                for ch in data['channels']:
                    name = ch.get('name', 'unknown')
                    url = ch.get('url', '')
                    logo = ch.get('logo', '')
                    if url:
                        channels.append({'name': name, 'url': url, 'logo': logo})
            elif 'data' in data and isinstance(data['data'], list):
                for ch in data['data']:
                    name = ch.get('name', 'unknown')
                    url = ch.get('url', '')
                    if url:
                        channels.append({'name': name, 'url': url, 'logo': ''})
        return channels
    except:
        return []


def test_source(url, name=''):
    """测试一个源URL"""
    safe_print(f"\n{'='*50}")
    safe_print(f"[{name}]")
    safe_print(f"URL: {url}")

    content, status = fetch_url(url)
    if not content:
        safe_print(f"  FAIL: 获取失败 -> {status}")
        return None

    safe_print(f"  OK: {len(content)} 字符")

    # 解析格式
    if '.m3u' in url.lower() or '#EXTM3U' in content:
        channels = parse_m3u(content)
        fmt = 'M3U'
    elif url.endswith('.txt'):
        channels = parse_txt(content)
        fmt = 'TXT'
    else:
        channels = parse_json(content)
        fmt = 'JSON'

    safe_print(f"  格式: {fmt} | 解析出 {len(channels)} 个频道")

    if not channels:
        safe_print(f"  FAIL: 无法解析内容")
        return None

    # 抽样测试前SAMPLE_SIZE个
    sample = channels[:SAMPLE_SIZE]
    working = []
    for i, ch in enumerate(sample):
        name_short = ch['name'][:30] if ch['name'] else 'unnamed'
        safe_print(f"  [{i+1}/{len(sample)}] {name_short} ... ", end='', flush=True)
        is_ok = test_stream_url(ch['url'])
        if is_ok:
            safe_print(f"OK")
            working.append(ch)
        else:
            safe_print(f"FAIL")
        time.sleep(0.05)

    working_ratio = len(working) / len(sample) if sample else 0
    safe_print(f"  抽样结果: {len(working)}/{len(sample)} 可用 ({working_ratio*100:.0f}%)")

    if working_ratio >= 0.3:  # 30%以上可用才保留
        return {
            'name': name,
            'source': url,
            'format': fmt,
            'total_channels': len(channels),
            'working_sample': len(working),
            'sample_size': len(sample),
            'sample_ratio': working_ratio,
            'sample_channels': working,
            'all_channels': channels
        }
    else:
        safe_print(f"  SKIP: 可用率太低 (<30%)")
        return None


def main():
    candidates = [
        # m3u格式
        ('https://raw.githubusercontent.com/YanG-1989/m3u/main/Gather.m3u', 'YanG聚合直播'),
        ('https://raw.githubusercontent.com/gnodgl/IPTV/master/CCTV.m3u', 'CCTV专版'),
        ('https://raw.githubusercontent.com/cuikaipeng/IPTV/main/CCTV.m3u', '崔凯CCTV'),
        ('https://raw.githubusercontent.com/cuikaipeng/IPTV/main/IPTV.m3u', '崔凯IPTV'),
        ('https://raw.githubusercontent.com/kakaxi-1/IPTV/main/ipv6.m3u', 'IPV6直播'),
        ('https://raw.githubusercontent.com/MercuryZz/IPTVN/refs/heads/Files/IPTV.m3u', 'IPTVN'),
        ('https://raw.githubusercontent.com/trial/m3u/main/tv.m3u', 'Trial直播'),
        ('https://raw.githubusercontent.com/Kimentanm/aptv/master/m3u/iptv.m3u', 'Kimentanm IPTV'),
        ('https://raw.githubusercontent.com/zbefine/iptv/main/iptv.m3u', 'zbefine IPTV'),
        ('https://raw.githubusercontent.com/balala2oo8/iptv/main/o.m3u', 'balala2 IPTV'),
        # txt格式
        ('https://raw.githubusercontent.com/lalifeier/IPTV/main/txt/IPTV.txt', 'lalifeier TXT'),
        # json格式
        ('https://raw.githubusercontent.com/dxawi/0/main/0.json', 'dxawi JSON'),
        ('https://raw.githubusercontent.com/UndCover/PyramidStore/main/py.json', 'PyramidStore'),
        ('https://raw.iqiq.io/lm317379829/PyramidStore/pyramid/py.json', 'PyramidStore2'),
        ('https://leezn.github.io/TVBox/py.json', 'LeeZn Py'),
        ('https://leezn.github.io/TVBox/js.json', 'LeeZn JS'),
        # 喝汤哥源
        ('https://ghproxy.com/https://raw.githubusercontent.com/gaotianliuyun/gao/master/XYQ.json', '喝汤哥XYQ'),
        ('https://ghproxy.com/https://raw.githubusercontent.com/gaotianliuyun/gao/master/js.json', '喝汤哥JS'),
    ]

    safe_print(f"TVBox 直播源快速验证工具")
    safe_print(f"测试 {len(candidates)} 个候选源，每源抽样 {SAMPLE_SIZE} 个频道")

    results = []
    for url, name in candidates:
        try:
            r = test_source(url, name)
            if r:
                results.append(r)
        except Exception as e:
            safe_print(f"  ERROR: {e}")
        time.sleep(0.3)

    # 汇总
    safe_print(f"\n{'='*60}")
    safe_print(f"[最终汇总]")

    if not results:
        safe_print("没有找到可用的源！")
        return

    results.sort(key=lambda x: x['sample_ratio'], reverse=True)

    for r in results:
        safe_print(f"\n{r['name']} ({r['format']})")
        safe_print(f"  源: {r['source']}")
        safe_print(f"  总频道: {r['total_channels']} | 抽样: {r['working_sample']}/{r['sample_size']} ({r['sample_ratio']*100:.0f}%)")

    # 生成配置文件
    safe_print(f"\n{'='*60}")
    safe_print(f"[生成配置文件]")

    for r in results:
        safe_name = r['name'].replace('/', '_').replace(' ', '_').replace('\n', '')
        out_file = f"C:/Users/Administrator/.openclaw/workspace/tvbox/sources/{safe_name}.json"
        out_data = {
            'name': r['name'],
            'source': r['source'],
            'total_channels': r['total_channels'],
            'channels': r['all_channels']  # 保存全量，实际用可筛选
        }
        try:
            with open(out_file, 'w', encoding='utf-8') as f:
                json.dump(out_data, f, ensure_ascii=False, indent=2)
            safe_print(f"  OK: sources/{safe_name}.json ({r['total_channels']}频道)")
        except Exception as e:
            safe_print(f"  FAIL: {e}")

    safe_print(f"\n[完成]")


if __name__ == '__main__':
    main()