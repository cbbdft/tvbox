# -*- coding: utf-8 -*-
"""
TVBox 直播源测工具
功能：批量测试直播源URL是否可用，只保留有效源
"""
import os
import sys
import json
import urllib.request
import urllib.error
import time
import ssl
from concurrent.futures import ThreadPoolExecutor, as_completed

# 配置
TIMEOUT = 10  # 单个源测试超时（秒）
MAX_WORKERS = 10  # 并发测试数
TEST_METHODS = ['head', 'get']  # 先试HEAD请求，失败再试GET

# 跳过已知无效的CDN域名（这些域名需要特殊DNS或海外访问）
SKIP_PREFIXES = [
    'http://cctv',
    'http://livewk.hls.cntv',  # CNTV需要特殊DNS
]


def test_url(url, timeout=TIMEOUT):
    """测试单个URL是否可用"""
    if not url or not url.startswith('http'):
        return False, 'invalid_url'

    # 检查是否在跳过列表
    for prefix in SKIP_PREFIXES:
        if url.lower().startswith(prefix):
            return False, 'skip_known_bad'

    # 尝试HEAD请求（更轻量）
    for method in TEST_METHODS:
        try:
            if method == 'head':
                req = urllib.request.Request(url, method='HEAD')
            else:
                req = urllib.request.Request(url, method='GET')

            req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            req.add_header('Referer', 'https://www.google.com/')
            req.add_header('Origin', 'https://www.google.com/')

            # 忽略SSL证书错误
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as response:
                status = response.status
                content_length = response.headers.get('Content-Length', '0')
                content_type = response.headers.get('Content-Type', '')

                # 检查是否是视频内容
                if status == 200:
                    if 'm3u8' in url or 'video' in content_type or 'application' in content_type:
                        return True, f'OK ({status})'
                    elif int(content_length) > 0:
                        return True, f'OK ({status}, {content_length}bytes)'
                    else:
                        # 可能有效但没Content-Length
                        return True, f'OK ({status})'
                else:
                    return False, f'http_{status}'

        except urllib.error.HTTPError as e:
            if e.code in [403, 404, 500, 502, 503]:
                return False, f'http_{e.code}'
            # 临时错误，继续试GET
            continue

        except urllib.error.URLError as e:
            return False, f'url_error_{type(e.reason).__name__}'

        except Exception as e:
            return False, f'error_{type(e).__name__}'

    return False, 'all_methods_failed'


def test_sources_in_file(filepath):
    """测试单个JSON文件中的所有源"""
    print(f"\n{'='*60}")
    print(f"测试文件: {filepath}")

    if not os.path.exists(filepath):
        print(f"[SKIP] 文件不存在")
        return None

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    channels = data.get('channels', [])
    print(f"共 {len(channels)} 个源待测试...")

    results = []
    for i, channel in enumerate(channels, 1):
        name = channel.get('name', 'unknown')
        url = channel.get('url', '')
        status = '[TESTING]' if i <= 3 else ''  # 只对前3个显示进度

        if i <= 5 or i == len(channels):
            print(f"  [{i}/{len(channels)}] {name} ... ", end='', flush=True)

        is_working, msg = test_url(url)
        results.append({
            'channel': channel,
            'is_working': is_working,
            'message': msg
        })

        if i <= 5 or i == len(channels):
            print(f" {'OK' if is_working else 'FAIL'} ({msg})")

        # 简单限速，避免被封
        time.sleep(0.1)

    # 统计
    working = [r for r in results if r['is_working']]
    failed = [r for r in results if not r['is_working']]

    print(f"\n[结果] 有效: {len(working)} | 无效: {len(failed)} | 总计: {len(results)}")

    # 列出无效源（便于排查）
    if failed:
        print(f"\n[无效源列表]:")
        for r in failed:
            name = r['channel'].get('name', 'unknown')
            url = r['channel'].get('url', '')
            print(f"  - {name}: {url} -> {r['message']}")

    return {
        'name': data.get('name', os.path.basename(filepath)),
        'channels': [r['channel'] for r in working],
        'stats': {
            'total': len(results),
            'working': len(working),
            'failed': len(failed)
        }
    }


def main():
    # 确定源目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    sources_dir = os.path.join(project_dir, 'sources')

    print(f"TVBox 直播源测工具")
    print(f"项目目录: {project_dir}")
    print(f"源目录: {sources_dir}")

    # 收集所有JSON文件
    if not os.path.exists(sources_dir):
        print(f"[ERROR] 源目录不存在: {sources_dir}")
        sys.exit(1)

    json_files = [f for f in os.listdir(sources_dir) if f.endswith('.json')]

    if not json_files:
        print(f"[ERROR] 源目录中没有JSON文件")
        sys.exit(1)

    print(f"找到 {len(json_files)} 个源文件: {json_files}")

    all_results = []

    # 逐个测试文件
    for filename in json_files:
        filepath = os.path.join(sources_dir, filename)
        result = test_sources_in_file(filepath)
        if result:
            all_results.append(result)

    # 输出汇总
    print(f"\n{'='*60}")
    print(f"[最终汇总]")

    total_sources = sum(r['stats']['total'] for r in all_results)
    total_working = sum(r['stats']['working'] for r in all_results)
    total_failed = sum(r['stats']['failed'] for r in all_results)

    for r in all_results:
        name = r['name']
        stats = r['stats']
        print(f"  {name}: {stats['working']}/{stats['total']} 有效")

    print(f"\n总计: {total_working}/{total_sources} 源有效")

    if total_working == 0:
        print("\n[WARNING] 所有源都无效！请检查网络或源列表是否已失效。")
        print("[HINT] 很多直播源需要特殊DNS或CDN配置，请在TVBox设备上直接测试。")
        return

    # 生成验证通过的源文件（覆盖原文件，只保留有效源）
    print(f"\n{'='*60}")
    print(f"[生成验证通过的源文件]")

    for r in all_results:
        name = r['name']
        channels = r['channels']
        # 找到原文件路径
        filename = f"{name.split('/')[-1].replace(' ', '_')}.json"
        if not filename.endswith('.json'):
            filename = name + '.json'

        # 搜索原文件
        for f in json_files:
            filepath = os.path.join(sources_dir, f)
            with open(filepath, 'r', encoding='utf-8') as file:
                data = json.load(file)
                if data.get('name') == name or f.replace('.json', '') in name:
                    filepath = filepath
                    break
        else:
            filepath = os.path.join(sources_dir, filename)

        # 写回有效源
        output_data = {'name': name, 'channels': channels}
        with open(filepath, 'w', encoding='utf-8') as file:
            json.dump(output_data, file, ensure_ascii=False, indent=2)

        print(f"  已更新: {os.path.basename(filepath)} ({len(channels)} 个有效源)")

    print(f"\n[完成] 源测试工具执行完毕！")


if __name__ == '__main__':
    main()