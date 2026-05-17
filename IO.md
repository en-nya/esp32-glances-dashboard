
# 1. ESP32-32E 主控电路

器件：`U2`  
型号：`ESP32-WROOM-32E-N4`  
标题：`ESP32-32E主控电路`

---

## 1.1 ESP32 左侧引脚连接

| 引脚号 | ESP32 引脚名 | 网络/连接名称 | 说明 |
|---|---|---|---|
| 1 | GND | GND | 接地 |
| 2 | 3V3 | VCC3V3 | 3.3V 电源输入 |
| 3 | EN | RESET | 复位/使能信号 |
| 4 | SENSOR_VP | RTP_IRQ | 电阻触摸屏中断信号 |
| 5 | SENSOR_VN | RTP_DOUT | 电阻触摸屏数据输出 |
| 6 | IO34 | BAT_ADC | 电池电压 ADC 检测 |
| 7 | IO35 | IO35 | 引出/预留 IO35 |
| 8 | IO32 | RTP_DIN | 电阻触摸屏数据输入 |
| 9 | IO33 | RTP_CS | 电阻触摸屏片选 |
| 10 | IO25 | RTP_SCK | 电阻触摸屏 SPI 时钟 |
| 11 | IO26 | AUDIO_IN | 音频输入 |
| 12 | IO27 | SPI_CS | SPI 片选 |
| 13 | IO14 | LCD_SCK | LCD SPI 时钟 |
| 14 | IO12 | LCD_MISO | LCD SPI MISO |
| 15 | GND | GND | 接地 |
| 16 | IO13 | LCD_MOSI | LCD SPI MOSI |
| 17 | NC | NC | 未连接 |
| 18 | NC | NC | 未连接 |
| 19 | NC | NC | 未连接 |

---

## 1.2 ESP32 右侧引脚连接

| 引脚号 | ESP32 引脚名 | 网络/连接名称 | 说明 |
|---|---|---|---|
| 20 | NC | NC | 未连接 |
| 21 | NC | NC | 未连接 |
| 22 | NC | NC | 未连接 |
| 23 | IO15 | LCD_CS | LCD 片选 |
| 24 | IO2 | LCD_RS | LCD 数据/命令选择 |
| 25 | IO0 | IO0 | 启动/下载相关 IO |
| 26 | IO4 | AUDIO_EN | 音频使能 |
| 27 | IO16 | IO16 | 引出/预留 IO16 |
| 28 | IO17 | IO17 | 引出/预留 IO17 |
| 29 | IO5 | SD_CS | SD 卡片选 |
| 30 | IO18 | SD_SCK / SPI_CLK | SD/SPI 时钟 |
| 31 | IO19 | SD_MISO / SPI_MISO | SD/SPI MISO |
| 32 | NC | NC | 未连接 |
| 33 | IO21 | LCD_BL | LCD 背光控制 |
| 34 | RXD0 | RXD0 | 串口 0 接收 |
| 35 | TXD0 | TXD0 | 串口 0 发送 |
| 36 | IO22 | IO22 | 引出/预留 IO22 |
| 37 | IO23 | SD_MOSI / SPI_MOSI | SD/SPI MOSI |
| 38 | GND | GND | 接地 |
| 39 | GND | GND | 接地，模块顶部 GND |

---

## 1.3 ESP32 电源去耦电容

| 器件 | 参数 | 连接 |
|---|---|---|
| C6 | 10uF，±10%，25V | VCC3V3 与 GND 之间 |
| C5 | 100nF，±10%，50V | VCC3V3 与 GND 之间 |

---

# 2. 电阻触摸屏控制电路

器件：`U4`  
型号：`XPT2046`  
标题：`电阻触摸屏控制电路`

---

## 2.1 XPT2046 左侧引脚连接

| 引脚号 | XPT2046 引脚名 | 网络/连接名称 | 说明 |
|---|---|---|---|
| 1 | VCC | VCC3V3 | 3.3V 电源 |
| 2 | XP | X+ | 触摸屏 X+ |
| 3 | YP | Y+ | 触摸屏 Y+ |
| 4 | XN | X- | 触摸屏 X- |
| 5 | YN | Y- | 触摸屏 Y- |
| 6 | GND | GND | 接地 |
| 7 | VBAT | NC | 未连接 |
| 8 | AUX | NC | 未连接 |

---

## 2.2 XPT2046 右侧引脚连接

| 引脚号 | XPT2046 引脚名 | 网络/连接名称 | 说明 |
|---|---|---|---|
| 9 | VREF | VCC3V3 / C13 | 参考电压，接 3.3V，并通过 C13 去耦到地 |
| 10 | IOVDD | VCC3V3 / C13 | IO 电源，接 3.3V，并通过 C13 去耦到地 |
| 11 | PENIRQ | RTP_IRQ | 触摸中断输出，外接上拉电阻 R7 |
| 12 | DOUT | RTP_DOUT | SPI 数据输出，接 ESP32 `SENSOR_VN / GPIO39` |
| 13 | BUSY | NC | 未连接 |
| 14 | DIN | RTP_DIN | SPI 数据输入，接 ESP32 `GPIO32` |
| 15 | CS# | RTP_CS | SPI 片选，低有效，接 ESP32 `GPIO33` |
| 16 | DCLK | RTP_SCK | SPI 时钟，接 ESP32 `GPIO25` |

---

## 2.3 XPT2046 外围器件

| 器件 | 参数 | 连接 |
|---|---|---|
| C12 | 100nF，±10%，50V | XPT2046 的 VCC 与 GND 之间 |
| C13 | 100nF，±10%，50V | VREF / IOVDD 与 GND 之间 |
| R7 | 10kΩ | RTP_IRQ 上拉到 VCC3V3 |

---

# 3. ESP32 与 XPT2046 触摸芯片连接对应关系

| 功能 | ESP32 引脚 | ESP32 GPIO | XPT2046 引脚 | 网络名 |
|---|---|---|---|---|
| 触摸 SPI 时钟 | IO25 | GPIO25 | DCLK，16脚 | RTP_SCK |
| 触摸 SPI MOSI | IO32 | GPIO32 | DIN，14脚 | RTP_DIN |
| 触摸 SPI MISO | SENSOR_VN | GPIO39 | DOUT，12脚 | RTP_DOUT |
| 触摸片选 | IO33 | GPIO33 | CS#，15脚 | RTP_CS |
| 触摸中断 | SENSOR_VP | GPIO36 | PENIRQ，11脚 | RTP_IRQ |
| 触摸屏 X+ | — | — | XP，2脚 | X+ |
| 触摸屏 Y+ | — | — | YP，3脚 | Y+ |
| 触摸屏 X- | — | — | XN，4脚 | X- |
| 触摸屏 Y- | — | — | YN，5脚 | Y- |

---

# 4. PlatformIO / 编译配置内容提取

图片中的配置文本如下：

```ini
upload_speed = 921600
;build_type = debug
board_build.partitions = huge_app.csv

build_flags =
    ;-DDEBUG_MEMORY=1
    -D ESP32_2432S028R=1
    -DUSER_SETUP_LOADED=1
    -DST7789_DRIVER=1
    -DTFT_WIDTH=240
    -DTFT_HEIGHT=320
    -DTFT_BACKLIGHT_ON=HIGH
    -DTFT_MOSI=13
    -DTFT_SCLK=14
    -DTFT_CS=15
    -DTFT_DC=2
    -DTFT_RST=12
    -DTFT_BL=21
    -DTOUCH_CS=33
    -DTOUCH_CLK=25
    -DTOUCH_MISO=39
    -DTOUCH_MOSI=32
    -DTOUCH_IRQ=36
    -DLOAD_GLCD=1
    -DLOAD_FONT2=1
    -DLOAD_GFXFF=1
    -DSMOOTH_FONT=1
    -DSPI_FREQUENCY=55000000
    -DSPI_READ_FREQUENCY=20000000
    -DSPI_TOUCH_FREQUENCY=2500000
```

---

# 5. 软件配置与原理图引脚对应

## 5.1 LCD 显示屏配置

| 软件宏定义 | GPIO | 原理图网络名 | 说明 |
|---|---|---|---|
| `TFT_MOSI=13` | GPIO13 | LCD_MOSI | LCD SPI MOSI |
| `TFT_SCLK=14` | GPIO14 | LCD_SCK | LCD SPI 时钟 |
| `TFT_CS=15` | GPIO15 | LCD_CS | LCD 片选 |
| `TFT_DC=2` | GPIO2 | LCD_RS | LCD 数据/命令选择 |
| `TFT_RST=12` | GPIO12 | LCD_MISO / 可能复用 | 软件中作为 TFT_RST |
| `TFT_BL=21` | GPIO21 | LCD_BL | LCD 背光控制 |

---

## 5.2 触摸屏配置

| 软件宏定义 | GPIO | 原理图网络名 | XPT2046 引脚 |
|---|---|---|---|
| `TOUCH_CS=33` | GPIO33 | RTP_CS | CS#，15脚 |
| `TOUCH_CLK=25` | GPIO25 | RTP_SCK | DCLK，16脚 |
| `TOUCH_MISO=39` | GPIO39 | RTP_DOUT | DOUT，12脚 |
| `TOUCH_MOSI=32` | GPIO32 | RTP_DIN | DIN，14脚 |
| `TOUCH_IRQ=36` | GPIO36 | RTP_IRQ | PENIRQ，11脚 |

---

# 6. 关键引脚汇总

## ESP32 主要功能分配

| GPIO | 功能 |
|---|---|
| GPIO0 | IO0，启动/下载相关 |
| GPIO2 | LCD_RS / TFT_DC |
| GPIO4 | AUDIO_EN |
| GPIO5 | SD_CS |
| GPIO12 | LCD_MISO / 软件中配置为 TFT_RST |
| GPIO13 | LCD_MOSI |
| GPIO14 | LCD_SCK |
| GPIO15 | LCD_CS |
| GPIO16 | IO16 预留 |
| GPIO17 | IO17 预留 |
| GPIO18 | SD_SCK / SPI_CLK |
| GPIO19 | SD_MISO / SPI_MISO |
| GPIO21 | LCD_BL |
| GPIO22 | IO22 预留 |
| GPIO23 | SD_MOSI / SPI_MOSI |
| GPIO25 | RTP_SCK / TOUCH_CLK |
| GPIO26 | AUDIO_IN |
| GPIO27 | SPI_CS |
| GPIO32 | RTP_DIN / TOUCH_MOSI |
| GPIO33 | RTP_CS / TOUCH_CS |
| GPIO34 | BAT_ADC |
| GPIO35 | IO35 预留 |
| GPIO36 | RTP_IRQ / TOUCH_IRQ |
| GPIO39 | RTP_DOUT / TOUCH_MISO |


