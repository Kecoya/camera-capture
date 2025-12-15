# 摄像头定时抓拍工具

一个功能强大的Python工具，支持智能摄像头管理、时间段抓拍生成GIF动图、固定时间点永久保存等多种抓拍模式。

## 功能特点

### 基础功能

- ✅ **智能摄像头管理**：按需初始化/释放摄像头，无需长时间占用
- ✅ **多时间段抓拍**：支持配置多个不同的抓拍时间段
- ✅ **GIF动图生成**：自动将时间段内的临时照片生成GIF动图
- ✅ **固定时间拍照**：可在指定时间点拍照并永久保存
- ✅ **照片分类存储**：自动区分临时照片、永久照片和GIF动图
- ✅ **带时间戳**：自动在照片上添加时间水印
- ✅ **自动清理**：定期清理过期的临时照片
- ✅ **多摄像头支持**：可选择不同的摄像头设备

### 高级功能

- ✅ **系统托盘图标**：支持最小化到系统托盘，右键菜单操作
- ✅ **隐藏模式**：无窗口后台运行，支持开机启动
- ✅ **图形化配置**：直观的GUI配置界面
- ✅ **配置管理**：查看、编辑、导入导出配置
- ✅ **系统服务**：支持创建自启动服务（Windows/Linux/macOS）
- ✅ **隐私保护**：图像文件自动加入Git忽略列表

## 项目结构

```
├── camera_capture.py     # 主程序（889行，核心功能）
├── config_manager.py     # 配置管理器（交互式配置）
├── setup_and_run.py      # GUI安装和启动界面
├── quick_start.py        # 快速启动脚本
├── camera_config.json    # 配置文件
├── requirements.txt      # 依赖包列表
├── .gitignore           # Git忽略规则（保护隐私）
└── README.md            # 本文档
```

## 安装依赖

```bash
pip install -r requirements.txt
```

或使用GUI安装：

```bash
python setup_and_run.py
```

## 快速开始

### 方式一：GUI图形界面（推荐）

#### 1. 安装配置界面

```bash
python setup_and_run.py
```

点击"安装依赖包"和"创建桌面快捷方式"进行初始化。

#### 2. 配置界面

```bash
python camera_capture.py --gui
```

或点击"显示配置窗口"进行参数设置。

#### 3. 隐藏模式运行（最小化到托盘）

```bash
python camera_capture.py --hidden
```

或点击"隐藏模式运行"，程序将在后台运行并显示托盘图标。

### 方式二：配置管理工具

```bash
python config_manager.py
```

打开交互式配置管理界面，可以：

- 查看当前配置
- 编辑配置参数
- 创建新配置
- 导入/导出配置
- 测试配置有效性
- 创建系统服务

### 方式三：命令行模式

#### 启动抓拍

```bash
python camera_capture.py
```

#### 隐藏模式启动

```bash
python camera_capture.py --hidden
```

#### 指定配置文件

```bash
python camera_capture.py --config my_config.json
```

#### 启用开机启动

```bash
python camera_capture.py --enable-startup        # 隐藏模式
python camera_capture.py --enable-startup --startup-visible  # 可见模式
```

#### 禁用开机启动

```bash
python camera_capture.py --disable-startup
```

#### 创建系统服务文件

```bash
python camera_capture.py --create-service
```

## 配置说明

### 配置文件（camera_config.json）

```json
{
  "camera_id": 0,
  "temporary_dir": "temp_captures",
  "permanent_dir": "permanent_captures",
  "gif_dir": "gif_animations",
  "time_ranges": [
    {
      "start": "11:30",
      "end": "14:30",
      "interval": 60
    }
  ],
  "fixed_times": [
    {
      "time": "08:50",
      "description": "早晨拍照"
    }
  ],
  "max_temp_captures": 1000,
  "auto_cleanup": true,
  "cleanup_days": 7,
  "gif_fps": 24,
  "enable_timestamp": true,
  "timestamp_color": [0, 0, 255],
  "timestamp_scale": 1.0,
  "timestamp_thickness": 2
}
```

### 配置参数说明

| 参数名                  | 说明                   | 默认值                 |
| ----------------------- | ---------------------- | ---------------------- |
| `camera_id`           | 摄像头设备ID           | 0                      |
| `temporary_dir`       | 临时照片保存目录       | `temp_captures`      |
| `permanent_dir`       | 永久照片保存目录       | `permanent_captures` |
| `gif_dir`             | GIF动图保存目录        | `gif_animations`     |
| `time_ranges`         | 抓拍时间段配置（数组） | -                      |
| ├─`start`           | 开始时间（HH:MM格式）  | -                      |
| ├─`end`             | 结束时间（HH:MM格式）  | -                      |
| └─`interval`        | 抓拍间隔（秒）         | 60                     |
| `fixed_times`         | 固定时间拍照点（数组） | -                      |
| ├─`time`            | 拍照时间（HH:MM格式）  | -                      |
| └─`description`     | 描述信息               | -                      |
| `max_temp_captures`   | 最大临时照片数量       | 1000                   |
| `auto_cleanup`        | 是否自动清理过期照片   | true                   |
| `cleanup_days`        | 清理多少天前的照片     | 7                      |
| `gif_fps`             | GIF动图帧率            | 24                     |
| `enable_timestamp`    | 是否在照片上添加时间戳 | true                   |
| `timestamp_color`     | 时间戳颜色（BGR格式）  | [0, 0, 255]（红色）    |
| `timestamp_scale`     | 时间戳字体大小         | 1.0                    |
| `timestamp_thickness` | 时间戳字体粗细         | 2                      |

### 抓拍模式详解

#### 1. 时间段抓拍（生成临时照片和GIF）

在配置的时间段内，程序会：

- 按指定间隔抓拍照片（保存为临时照片）
- 时间段结束时自动生成GIF动图
- 示例：`11:30-14:30`期间每60秒抓一次，结束后生成GIF

#### 2. 固定时间点拍照（永久保存）

在指定时间点拍照并永久保存：

- 照片保存到 `permanent_dir`
- 不会被自动清理
- 示例：每天 `08:50` 拍照保存为永久照片

#### 3. 智能摄像头管理

- **按需使用摄像头**：只在需要拍照时初始化摄像头
- **自动释放**：拍照完成后自动释放摄像头资源
- **避免占用**：不会在后台持续占用摄像头

## 输出文件

### 临时照片

- **目录**：`temp_captures/`
- **格式**：`temp_YYYYMMDD_HHMMSS.jpg`
- **作用**：用于生成GIF的源素材
- **清理**：自动清理过期文件

### 永久照片

- **目录**：`permanent_captures/`
- **格式**：`permanent_YYYYMMDD_HHMMSS.jpg`
- **作用**：固定时间点的重要拍照
- **清理**：不会自动删除

### GIF动图

- **目录**：`gif_animations/`
- **格式**：`gif_YYYYMMDD_starttime_endtime.gif`
- **作用**：汇总时间段内的抓拍照片
- **清理**：与临时照片关联，不会被清理

## GUI界面使用指南

### 配置窗口

配置窗口分为三个选项卡：

#### 1. 基本设置

- 摄像头ID选择
- 照片存储目录设置
- GIF参数配置
- 时间戳样式设置

#### 2. 抓拍设置

- 添加/编辑时间段
- 添加/编辑固定时间
- 查看抓拍历史

#### 3. 启动设置

- 开机启动开关
- 启动模式选择（隐藏/可见）
- 当前运行状态显示

### 系统托盘图标

右键托盘图标可进行以下操作：

- 显示配置窗口
- 启动/停止抓拍
- 启用/禁用开机启动
- 打开抓拍文件夹
- 退出程序

## 系统服务配置

### Windows系统

#### 方法1：使用配置界面

1. 打开配置窗口：`python camera_capture.py --gui`
2. 进入"启动设置"选项卡
3. 勾选"开机自动启动"
4. 点击"应用启动设置"

#### 方法2：手动配置

1. 创建服务文件：
   ```bash
   python camera_capture.py --create-service
   ```
2. 将生成的 `start_camera_capture_hidden.vbs` 复制到启动文件夹：
   - 按 `Win + R`
   - 输入 `shell:startup`
   - 将文件粘贴到打开的文件夹

#### 开机启动模式

- **隐藏模式**：程序无窗口，只在系统托盘显示图标
- **可见模式**：程序启动时显示配置窗口

### Linux系统

1. 创建服务文件：
   ```bash
   python camera_capture.py --create-service
   ```
2. 安装并启动服务：
   ```bash
   sudo cp camera-capture.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable camera-capture.service
   sudo systemctl start camera-capture.service
   ```

### macOS系统

1. 创建LaunchAgent文件：
   ```bash
   python camera_capture.py --create-service
   ```
2. 加载服务：
   ```bash
   cp com.user.camera-capture.plist ~/Library/LaunchAgents/
   launchctl load ~/Library/LaunchAgents/com.user.camera-capture.plist
   ```

## 隐私保护

本工具自动为图像文件配置Git隐私保护，确保敏感照片不会意外提交到版本控制系统。

### Git忽略配置（.gitignore）

以下文件/目录会自动被Git忽略：

- `temp_captures/` - 临时照片目录
- `gif_animations/` - GIF动图目录
- `permanent_captures/` - 永久照片目录
- 所有图像格式：*.jpg, *.jpeg, *.png, *.gif, *.bmp, *.tiff, *.webp, *.svg等

### 安全性建议

1. **配置权限**：建议设置相机配置文件仅当前用户可读
2. **定期备份**：重要照片（永久目录）建议定期备份到安全位置
3. **访问控制**：照片存储目录应设置适当的访问权限
4. **加密存储**：如涉及敏感内容，考虑使用加密存储方案

## 故障排除

### 常见问题

#### 摄像头无法打开

- 检查摄像头是否被其他程序占用
- 尝试更改 `camera_id` 参数（0, 1, 2...）
- 检查摄像头驱动是否正常
- 以管理员权限运行

#### 程序启动后立即退出

- 检查配置文件格式是否正确
- 确认所有依赖已正确安装
- 查看错误日志信息

#### 照片无法保存

- 检查磁盘空间是否充足
- 确认照片目录有写入权限
- 检查路径是否包含非法字符

#### 开机启动不生效

- 确认已启用开机启动：`python camera_capture.py --enable-startup`
- 检查注册表项是否存在
- 尝试手动创建启动快捷方式

#### GIF生成失败

- 确保时间段内有足够照片（至少2张）
- 检查 `gif_fps` 设置是否合理
- 确认 `gif_dir` 目录存在且可写入

### 调试模式

启动时添加详细输出：

```bash
python camera_capture.py --verbose
```

检查配置文件格式：

```bash
python camera_capture.py --edit-config
```

测试摄像头连接：

```bash
python camera_capture.py --test-camera
```

## 系统要求

### 软件要求

- **Python版本**：3.7+
- **操作系统**：Windows 7+ / Linux / macOS
- **依赖库**：
  - OpenCV 4.5.0+
  - Pillow 8.0+
  - schedule 1.1.0+
  - pystray 0.8.0+

### 硬件要求

- **摄像头**：内置或外接USB摄像头
- **存储空间**：至少1GB可用空间（建议5GB+）
- **内存**：1GB RAM（建议2GB+）
- **CPU**：双核1.5GHz（建议双核2.4GHz+）

## 版本历史

### v2.0（当前版本）

- ✨ 全新GUI配置界面
- ✨ 系统托盘图标支持
- ✨ 隐藏模式运行
- ✨ 智能摄像头管理
- ✨ 自动生成GIF动图
- ✨ 隐私保护（Git忽略）
- 🐛 修复摄像头占用问题
- 🐛 优化内存使用

### v1.x（旧版本）

- 基础抓拍功能
- 命令行配置
- 系统服务支持

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 贡献

欢迎提交Issue和Pull Request！

## 联系方式

如有问题或建议，请提交GitHub Issue。

## 注意事项

1. **法律合规**：请确保在合法合规的前提下使用本工具
2. **隐私尊重**：尊重他人隐私，避免在敏感区域使用
3. **数据安全**：定期清理不需要的照片，保护个人隐私
4. **资源占用**：长时间运行会占用系统资源，请合理配置抓拍间隔

---

**⚠️ 重要提示**：本工具仅供合法用途，使用者应遵守当地法律法规。不当使用可能导致法律风险。
