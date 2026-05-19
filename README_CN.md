# ESP32 Glances 监控仪表盘

中文文档 | [English](README.md)

基于 ESP32 和触摸屏的实时服务器监控仪表盘，使用 MicroPython 开发。通过 WiFi 从 [Glances](https://nicolargo.github.io/glances/) 监控服务器获取并显示系统指标。

![License](https://img.shields.io/badge/license-AGPL--3.0--or--later-blue.svg)

## 功能特性

- **实时监控**: 实时显示 CPU、内存、磁盘、网络、温度、系统负载和 Docker 容器状态
- **可视化仪表盘**: 彩色编码的指标，带进度条和实时 CPU 使用率图表
- **WiFi 连接**: 自动连接，带动画启动序列
- **触摸屏支持**: 支持 XPT2046 电阻式触摸控制器
- **亮度控制**: 通过硬件按钮调节背光（长按调节，释放反转方向）
- **时间同步**: 从 Glances 服务器自动同步时间
- **低资源占用**: 针对 ESP32 优化，高效轮询和增量显示更新

## 硬件要求

### 主要组件
- **主控**: ESP32-WROOM-32E-N4 开发板
- **显示屏**: ST7789 LCD，240×320 像素，SPI 接口
- **触摸**: XPT2046 电阻式触摸控制器
- **按钮**: Boot 按钮（GPIO0）用于背光控制

### 引脚配置

完整引脚映射请参见 [IO.md](IO.md)。主要连接：

**LCD (ST7789)**
- MOSI: GPIO13
- SCLK: GPIO14
- CS: GPIO15
- DC: GPIO2
- RST: GPIO12
- BL: GPIO21（背光 PWM）

**触摸 (XPT2046)**
- MOSI: GPIO32
- MISO: GPIO39
- SCLK: GPIO25
- CS: GPIO33
- IRQ: GPIO36

## 软件要求

- **MicroPython**: ESP32 v1.19 或更高版本
- **Glances 服务器**: 在监控目标上运行 v3.x 或 v4.x
- **网络**: ESP32 和 Glances 服务器必须在同一网络或具有网络连接

## 安装步骤

### 1. 烧录 MicroPython

下载并将 MicroPython 固件烧录到 ESP32：

```bash
esptool.py --chip esp32 --port /dev/ttyUSB0 erase_flash
esptool.py --chip esp32 --port /dev/ttyUSB0 write_flash -z 0x1000 esp32-*.bin
```

### 2. 配置 WiFi 和 Glances

复制示例配置并编辑您的设置：

```bash
cp config.example.py config.py
```

编辑 `config.py`：

```python
WIFI_SSID = "你的WiFi名称"
WIFI_PASSWORD = "你的WiFi密码"

GLANCES_BASE_URL = "http://192.168.1.100:61208"  # 你的 Glances 服务器地址
HTTP_TIMEOUT_SECONDS = 2

REFRESH_INTERVAL_SECONDS = 5
```

### 3. 上传文件到 ESP32

使用 `ampy`、`rshell` 或 Thonny IDE 等工具将所有项目文件上传到 ESP32：

```bash
# 使用 ampy
ampy --port /dev/ttyUSB0 put boot.py
ampy --port /dev/ttyUSB0 put main.py
ampy --port /dev/ttyUSB0 put config.py
ampy --port /dev/ttyUSB0 put lib
```

### 4. 设置 Glances 服务器

在监控目标（Linux 服务器、树莓派等）上安装并运行 Glances：

```bash
# 安装 Glances
pip install glances

# 以 Web 服务器模式运行
glances -w --disable-plugin docker
```

或启用 Docker 支持：

```bash
glances -w
```

Glances 默认在 61208 端口启动。

## 使用指南

### 启动仪表盘

仪表盘在启动时自动运行。手动启动方式：

```python
import main
```

或重置 ESP32 - `boot.py` 将初始化系统，`main.py` 会自动启动。

### 亮度控制

- **长按** Boot 按钮（GPIO0）：亮度持续增加/减少
- **释放**：方向反转（如果正在增加，下次按下将减少，反之亦然）

### 显示布局

仪表盘显示以下信息：

- **顶部栏**: Glances 服务器 IP 和连接状态
- **CPU**: 使用率百分比、频率和实时使用率图表
- **内存**: 使用率百分比和进度条
- **磁盘**: 使用率百分比和已用/总容量
- **网络**: 上传/下载速率和总传输数据量
- **温度**: 最高传感器温度，带颜色编码（绿色 < 50°C，橙色 < 70°C，红色 ≥ 70°C）
- **系统负载**: 1 分钟、5 分钟和 15 分钟平均负载
- **Docker**: 运行/停止的容器数量
- **运行时间**: 系统运行时间，实时更新
- **底部栏**: 当前时间（从服务器同步）和亮度级别

### 故障排除

**WiFi 连接失败**
- 验证 `config.py` 中的 SSID 和密码
- 检查 ESP32 是否在 WiFi 范围内
- 确保网络支持 2.4GHz（ESP32 不支持 5GHz）

**无数据显示**
- 验证 Glances 服务器正在运行：`curl http://your-server:61208/api/4/quicklook`
- 检查 `config.py` 中的 `GLANCES_BASE_URL`
- 确保防火墙允许 61208 端口
- 检查串口输出的错误消息

**显示问题**
- 验证引脚连接是否与 [IO.md](IO.md) 匹配
- 检查串口输出中的 SPI 总线初始化信息
- 确保电源供应充足（ESP32 + LCD 可能消耗较大电流）

**更新缓慢**
- 减少 `config.py` 中的 `REFRESH_INTERVAL_SECONDS`（建议最小 1 秒）
- 检查 ESP32 和 Glances 服务器之间的网络延迟

## 项目结构

```
esp32-glances-dashboard/
├── boot.py                 # 启动初始化
├── main.py                 # 应用程序入口
├── config.example.py       # 配置模板
├── IO.md                  # 硬件引脚映射文档
└── lib/
    ├── pins.py           # 引脚定义
    ├── wifi_client.py    # WiFi 连接和启动动画
    ├── glances_client.py # Glances API 客户端和轮询
    ├── display.py        # ST7789 驱动和仪表盘 UI
    └── backlight_button.py # 亮度控制按钮处理
```

## 使用的 API 端点

仪表盘轮询以下 Glances API v4 端点：

- `/api/4/quicklook` - CPU 和内存（每 1 秒）
- `/api/4/network` - 网络统计（每 5 秒）
- `/api/4/load` - 系统负载平均值（每 5 秒）
- `/api/4/sensors` - 温度传感器（每 5 秒）
- `/api/4/uptime` - 系统运行时间（每 5 分钟）
- `/api/4/fs` - 文件系统使用情况（每 10 分钟）
- `/api/4/containers` - Docker 容器（每 10 分钟）
- `/api/4/now` - 服务器时间同步（每 5 分钟）

## 自定义配置

### 更改颜色

在 `lib/display.py` 中编辑颜色定义：

```python
class Display:
    BLACK = color565(0, 0, 0)
    WHITE = color565(220, 230, 235)
    CYAN = color565(50, 230, 245)
    GREEN = color565(100, 230, 80)
    # ... 根据需要修改
```

### 调整轮询间隔

在 `lib/glances_client.py` 中编辑任务间隔：

```python
self.tasks = (
    {"name": "quicklook", "path": "/api/4/quicklook", "interval": 1000, ...},
    # interval 单位为毫秒
)
```

### 修改仪表盘布局

布局在 `lib/display.py` 的 `_draw_layout()` 方法中定义。调整卡片位置和大小：

```python
self._card(x, y, width, height, "标题", color)
```

## 性能指标

- **内存**: 运行时约 50KB 可用 RAM
- **网络**: 平均带宽使用约 2-5KB/s
- **CPU**: ESP32 CPU 使用率极低，显示更新为增量式
- **功耗**: 约 200-300mA @ 5V（随背光亮度变化）

## 开源协议

本项目采用 **GNU Affero General Public License v3.0 或更高版本** (AGPL-3.0-or-later) 协议。

完整协议文本请参见 [LICENSE](LICENSE)。

## 贡献

欢迎贡献！请随时提交问题或拉取请求。

## 致谢

- [Glances](https://nicolargo.github.io/glances/) - 为本仪表盘提供支持的监控工具
- [MicroPython](https://micropython.org/) - 微控制器的 Python 实现
- ST7789 和 XPT2046 驱动实现

## 相关链接

- **源代码**: https://github.com/en-nya/esp32-glances-dashboard
- **Glances 文档**: https://glances.readthedocs.io/
- **MicroPython ESP32**: https://docs.micropython.org/en/latest/esp32/quickref.html
