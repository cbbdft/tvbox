# TVBox 直播源管理与加速配置中心

基于开源 TVBox 方案，为 Android 4.4 电视盒子打造的本地化直播源管理与加速配置中心。

## 功能特性

- 统一管理多个直播源（央视、卫视、地方台、体育、影视等）
- 支持多源自动切换（故障转移）
- 内置代理/VPN 加速配置，适配多种主流代理协议
- 支持自建源和第三方源混合使用
- 定期自动更新源列表

## 适用设备

- Android 4.4+ 电视盒子
- 其他支持 TVBox 的设备

## 快速开始

### 1. 安装 TVBox

下载 TVBox APK 并安装到你的 Android 4.4 电视盒子上。

推荐版本：
- TVBox 官方版本
- 其他基于 TVBox 的第三方修改版

### 2. 配置直播源

#### 方式一：使用配置接口（推荐）

在 TVBox 的配置页面填入以下接口地址：

```
https://raw.githubusercontent.com/cbbdft/tvbox/main/tvbox-config.json
```

#### 方式二：本地配置

将本仓库的 `tvbox-config.json` 文件复制到设备存储，然后在 TVBox 中选择"本地配置"。

### 3. 配置加速代理（可选）

如果你在海外或需要加速观看，可使用 `acceleration/` 目录下的代理配置文件。

## 目录结构

```
tvbox/
├── README.md              # 本说明文件
├── tvbox-config.json      # TVBox 主配置文件
├── sources/               # 直播源列表
│   ├── china.json         # 国内央视频道
│   ├── hunan.json         # 湖南系
│   ├── iqiyi.json         # 爱奇艺系
│   ├── tencent.json       # 腾讯系
│   ├── youku.json         # 优酷系
│   ├── sports.json        # 体育频道
│   └── custom.json        # 自定义源
├── scripts/               # 管理脚本
│   └── update_sources.py  # 自动更新源列表
├── acceleration/          # 加速配置
│   ├── v2ray.json         # V2Ray 配置示例
│   └── clash.yaml         # Clash 配置示例
└── docs/
    └── usage.md           # 详细使用说明
```

## 直播源分类

### 国内主流

| 分类 | 数量 | 说明 |
|------|------|------|
| 央视频道 | 20+ | CCTV1-15 及各地方央视台 |
| 卫视频道 | 30+ | 各大卫视 |
| 地方频道 | 50+ | 各省市地方台 |
| 体育频道 | 10+ | CCTV5、虎牙、斗鱼等 |
| 影视专区 | 20+ | 付费影视轮播 |

### 海外源

提供部分海外华语频道，需配合代理使用。

## 加速配置

### 支持的代理协议

- Shadowsocks (SS)
- ShadowsocksR (SSR)
- V2Ray (VMess / VLESS)
- Trojan
- Clash

### 配置步骤

1. 在 `acceleration/` 目录选择你需要的配置文件
2. 根据你的代理服务填充服务器信息
3. 将配置导入到你的代理客户端

支持的客户端：
- Clash for Android
- v2rayNG
- Shadowsocks for Android

## 脚本工具

### 自动更新源列表

```bash
python scripts/update_sources.py
```

## 免责声明

- 本项目仅供学习交流
- 请通过正规渠道获取直播内容授权
- 禁止用于任何商业盈利活动