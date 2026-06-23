> 🚨 **本仓库已停止维护（Deprecated / Unmaintained）**
>
> 作者已不再维护本项目。摄像头监控相关功能已**合并到新仓库**：
>
> 👉 **https://github.com/Kecoya/DailyRoutine-Monitoring**
>
> 请前往新仓库获取最新版本、提交 Issue 或贡献代码。本文档下方内容仅作历史存档参考。

---

# 摄像头定时抓拍工具

一个功能强大的 Python 工具，支持智能摄像头管理、时间段抓拍生成 GIF 动图、固定时间点永久保存等多种抓拍模式。
本版本提供 **Web 看板**界面（基于 Flask），在浏览器中即可完成实时预览、配置、控制与图片浏览。

## 功能特点

### 抓拍能力

- ✅ **智能摄像头管理**：按需初始化/释放摄像头，无需长时间占用
- ✅ **多时间段抓拍**：支持配置多个不同的抓拍时间段
- ✅ **GIF 动图生成**：自动将时间段内的临时照片生成 GIF 动图
- ✅ **固定时间拍照**：可在指定时间点拍照并永久保存
- ✅ **照片分类存储**：自动区分临时照片、永久照片和 GIF 动图
- ✅ **带时间戳**：自动在照片上添加时间水印
- ✅ **自动清理**：定期清理过期的临时照片
- ✅ **多摄像头支持**：可选择不同的摄像头设备

### Web 看板

- ✅ **实时预览**：MJPEG 实时画面，可随时启停
- ✅ **在线配置**：浏览器中编辑全部参数（时间段、固定时间、目录、时间戳、清理等）
- ✅ **一键控制**：立即抓拍 / 启动 / 停止定时抓拍
- ✅ **图片画廊**：临时/永久照片缩略图、分页、灯箱、下载、删除
- ✅ **GIF 预览**：在线查看并下载/删除 GIF
- ✅ **启动设置**：开机自启、桌面快捷方式，均在网页内完成
- ✅ **配置管理**：命令行工具可查看、编辑、导入导出、测试配置
- ✅ **系统服务**：支持创建自启动服务（Windows/Linux/macOS）
- ✅ **隐私保护**：图像文件自动加入 Git 忽略列表

## 项目结构

```
├── camera_capture.py     # 主程序（抓拍引擎 + 命令行入口）
├── web_app.py            # Flask Web 看板（路由 + MJPEG + API）
├── templates/index.html  # 看板页面
├── static/app.js         # 前端逻辑
├── static/style.css      # 样式
├── config_manager.py     # 交互式配置管理器（命令行）
├── silent_launcher.py    # 无头静默启动器（开机自启用）
├── setup_and_run.py      # 启动器（双击启动 Web 看板）
├── camera_config.json    # 配置文件
├── requirements.txt      # 依赖清单
├── .gitignore            # Git 忽略规则（保护隐私）
└── README.md             # 本文档
```

## 安装依赖

```bash
pip install -r requirements.txt
```

或使用启动器自动安装：

```bash
python setup_and_run.py --install-deps
```

## 快速开始

### 方式一：启动 Web 看板（推荐）

```bash
python camera_capture.py
```

程序会在 `http://127.0.0.1:5000/` 启动 Web 服务并**自动打开浏览器**。在网页里即可：
- 「实时预览」查看画面
- 「配置」编辑参数并保存
- 「控制」立即抓拍 / 启停定时抓拍
- 「图片画廊」「GIF」浏览、下载、删除
- 「启动设置」配置开机自启、创建桌面快捷方式
- 页脚「退出服务」安全关闭

### 自定义端口 / 地址 / 不开浏览器

```bash
python camera_capture.py --port 8080
python camera_capture.py --host 0.0.0.0 --port 8000   # 允许局域网访问
python camera_capture.py --no-browser                   # 不自动开浏览器
python camera_capture.py --hidden                       # 无头运行（等价于 --no-browser，适合自启）
```

### 方式二：双击启动器

双击 `setup_and_run.py`（或运行 `python setup_and_run.py`）会在后台启动 Web 看板。

### 方式三：配置管理工具（命令行）

```bash
python config_manager.py
```

交互式菜单可：查看配置、编辑参数、创建新配置、导入/导出、测试配置、创建系统服务。

### 开机自启

```bash
python camera_capture.py --enable-startup     # 启用（无头 Web 服务）
python camera_capture.py --disable-startup    # 禁用
```

也可在网页「启动设置」选项卡里一键切换。开机后会以无窗口方式启动 Web 服务，浏览器访问 `http://127.0.0.1:5000/` 即可。

### 创建系统服务文件

```bash
python camera_capture.py --create-service
```

## 命令行参数

| 参数 | 说明 |
| --- | --- |
| （无） | 启动 Web 看板，自动打开浏览器 |
| `--port N` | Web 服务端口，默认 5000 |
| `--host H` | 绑定地址，默认 127.0.0.1 |
| `--no-browser` | 启动后不打开浏览器 |
| `--hidden` / `--tray` | 无头运行（不开浏览器，适合开机自启） |
| `--config PATH` | 指定配置文件，默认 `camera_config.json` |
| `--enable-startup` | 启用开机自启 |
| `--disable-startup` | 禁用开机自启 |
| `--create-service` | 创建系统服务文件 |
| `--edit-config` | 打印配置文件示例 |

## 配置说明

### 配置文件（camera_config.json）

```json
{
  "camera_id": 0,
  "temporary_dir": "temp_captures",
  "permanent_dir": "permanent_captures",
  "gif_dir": "gif_animations",
  "time_ranges": [
    { "start": "09:00", "end": "12:00", "interval": 30 }
  ],
  "fixed_times": [
    { "time": "08:00", "description": "早晨拍照" }
  ],
  "max_temp_captures": 1000,
  "auto_cleanup": true,
  "cleanup_days": 7,
  "gif_fps": 24,
  "gif_duration": 2.0,
  "enable_timestamp": true,
  "timestamp_color": [0, 0, 255],
  "timestamp_scale": 1.0,
  "timestamp_thickness": 2
}
```

### 配置参数说明

| 参数 | 说明 | 默认值 |
| --- | --- | --- |
| `camera_id` | 摄像头设备 ID | 0 |
| `temporary_dir` | 临时照片目录 | `temp_captures` |
| `permanent_dir` | 永久照片目录 | `permanent_captures` |
| `gif_dir` | GIF 动图目录 | `gif_animations` |
| `time_ranges` | 抓拍时间段（`start`/`end` 为 HH:MM，`interval` 秒） | — |
| `fixed_times` | 固定时间拍照点（`time` HH:MM，`description`） | — |
| `max_temp_captures` | 最大临时照片数量 | 1000 |
| `auto_cleanup` | 是否自动清理过期照片 | true |
| `cleanup_days` | 清理多少天前的照片 | 7 |
| `gif_fps` | GIF 帧率 | 24 |
| `gif_duration` | GIF 时长（秒） | 2.0 |
| `enable_timestamp` | 是否添加时间戳 | true |
| `timestamp_color` | 时间戳颜色（BGR） | [0, 0, 255] |
| `timestamp_scale` | 时间戳字体大小 | 1.0 |
| `timestamp_thickness` | 时间戳字体粗细 | 2 |

### 抓拍模式

1. **时间段抓拍**：在配置时间段内按间隔抓拍（临时照片），时段结束自动生成 GIF。
2. **固定时间点拍照**：在指定时间拍照并永久保存到 `permanent_dir`，不会被自动清理。
3. **智能摄像头管理**：只在需要时初始化摄像头，用完即释放，避免长时间占用。

## 输出文件

| 类型 | 目录 | 命名 | 清理 |
| --- | --- | --- | --- |
| 临时照片 | `temp_captures/` | `temp_YYYYMMDD_HHMMSS.jpg` | 自动清理过期 |
| 永久照片 | `permanent_captures/` | `permanent_YYYYMMDD_HHMMSS.jpg` | 不自动删除 |
| GIF 动图 | `gif_animations/` | `gif_YYYYMMDD_start_end.gif` | 不自动删除 |

## 系统服务配置

### Windows

- 网页「启动设置」选项卡 → 启用开机启动；或 `python camera_capture.py --enable-startup`。
- 也可 `python camera_capture.py --create-service` 生成 `.bat`，放入启动文件夹（`Win+R` → `shell:startup`）。
- 开机以**无头 Web 服务**方式运行（无窗口、不开浏览器）。

### Linux

```bash
python camera_capture.py --create-service
sudo cp camera-capture.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now camera-capture.service
```

### macOS

```bash
python camera_capture.py --create-service
cp com.user.camera-capture.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.user.camera-capture.plist
```

## 隐私保护

`.gitignore` 自动忽略照片目录与常见图像格式（`*.jpg`、`*.png`、`*.gif` 等），防止敏感照片误提交。Web 服务默认仅绑定 `127.0.0.1`，外部无法访问；如需局域网访问请用 `--host 0.0.0.0` 并自行放行端口。

## 故障排除

- **摄像头无法打开**：检查是否被占用；尝试改 `camera_id`（0/1/2）；检查驱动。
- **端口被占用**：用 `--port` 指定其他端口。
- **开机启动不生效**：确认 `python camera_capture.py --enable-startup` 已执行，检查启动文件夹中的快捷方式。
- **GIF 生成失败**：确保时间段内有 ≥2 张照片，`gif_fps` 合理，`gif_dir` 可写。
- **查看配置**：`python camera_capture.py --edit-config`。

## 系统要求

- **Python**：3.7+
- **操作系统**：Windows 7+ / Linux / macOS
- **依赖**：OpenCV 4.5+、Pillow 8+、schedule 1.1+、Flask 2.0+（Windows 另需 pywin32、winshell 用于开机自启）
- **硬件**：摄像头；≥1GB 可用空间；≥1GB 内存

## 版本历史

> ⚠️ **本项目已停止维护**，相关功能已迁移至 [DailyRoutine-Monitoring](https://github.com/Kecoya/DailyRoutine-Monitoring)。下方版本记录仅作历史存档。

### v3.0（最终版本）

- 🎉 用 **Flask Web 看板**取代原 tkinter 窗口与系统托盘
- ✨ 实时 MJPEG 预览、图片画廊（缩略图/灯箱/下载/删除）、GIF 在线预览
- ✨ 网页内配置编辑（含时间段/固定时间动态表单）、启停控制、开机自启、桌面快捷方式
- 🔧 `--port` / `--host` / `--no-browser`；`--hidden` 重定义为无头 Web 服务
- 🐛 修复线程安全、配置深拷贝、跨平台兼容等多个问题

### v2.x（旧版本）

- tkinter 配置窗口 + 系统托盘图标
- 智能摄像头管理、GIF 生成、隐私保护

## 注意事项

1. **法律合规**：请在合法合规前提下使用本工具。
2. **隐私尊重**：尊重他人隐私，避免在敏感区域使用。
3. **数据安全**：定期清理不需要的照片。
4. **资源占用**：长时间运行会占用系统资源，请合理配置抓拍间隔。

---

**⚠️ 重要提示**：本工具仅供合法用途，使用者应遵守当地法律法规。
