# 摄像头定时抓拍工具

一个功能强大的Python工具，支持多种抓拍模式和自动服务配置。

## 功能特点

### 基础功能

- ✅ **多时间段抓拍**：支持配置多个不同的抓拍时间段
- ✅ **固定时间拍照**：可在指定时间点拍照并永久保存
- ✅ **照片分类存储**：自动区分临时照片和永久照片
- ✅ **跨天时间段**：支持跨天的时间段配置
- ✅ **自动清理**：定期清理过期的临时照片
- ✅ **多摄像头支持**：可选择不同的摄像头设备

### 高级功能

- ✅ **系统服务**：支持创建自启动服务（Windows/Linux/macOS）
- ✅ **配置管理**：图形化配置管理界面
- ✅ **配置导入导出**：支持配置文件的导入和导出
- ✅ **配置验证**：自动验证配置文件的正确性

## 安装依赖

```bash
pip install -r requirements.txt
```

## 快速开始

### 方式一：交互式配置（推荐）

```bash
python quick_start.py
```

通过友好的交互界面配置所有参数。

### 方式二：使用默认配置

```bash
python camera_capture.py
```

使用默认配置直接启动抓拍。

### 方式三：配置管理

```bash
python config_manager.py
```

打开配置管理界面，可以查看、编辑、导入导出配置。

## 使用方法

### 主要功能

#### 基本语法

```bash
python camera_capture.py [--config CONFIG_FILE] [其他选项]
```

#### 参数说明

- `--config, -c`: 配置文件路径，默认为 `camera_config.json`
- `--create-service`: 创建系统服务文件
- `--edit-config`: 编辑配置文件

#### 使用示例

1. **使用默认配置启动**

   ```bash
   python camera_capture.py
   ```
2. **使用自定义配置文件**

   ```bash
   python camera_capture.py --config my_config.json
   ```
3. **创建系统服务**

   ```bash
   python camera_capture.py --create-service
   ```

## 配置文件格式

工具使用JSON配置文件，默认为 `camera_config.json`：

```json
{
  "camera_id": 0,
  "temporary_dir": "temp_captures",
  "permanent_dir": "permanent_captures",
  "time_ranges": [
    {
      "start": "09:00",
      "end": "12:00",
      "interval": 30
    },
    {
      "start": "14:00",
      "end": "18:00",
      "interval": 60
    }
  ],
  "fixed_times": [
    {
      "time": "08:00",
      "description": "早晨拍照"
    },
    {
      "time": "20:00",
      "description": "晚上拍照"
    }
  ],
  "max_temp_captures": 1000,
  "auto_cleanup": true,
  "cleanup_days": 7
}
```

### 配置说明

- **camera_id**: 摄像头设备ID
- **temporary_dir**: 临时照片保存目录
- **permanent_dir**: 永久照片保存目录
- **time_ranges**: 抓拍时间段配置
  - start: 开始时间
  - end: 结束时间
  - interval: 抓拍间隔（秒）
- **fixed_times**: 固定时间拍照点
  - time: 拍照时间
  - description: 描述信息
- **max_temp_captures**: 最大临时照片数量
- **auto_cleanup**: 是否自动清理过期照片
- **cleanup_days**: 清理多少天前的照片

## 输出文件

### 临时照片

- 保存目录：`temporary_dir`（默认：`temp_captures`）
- 文件命名格式：`temp_YYYYMMDD_HHMMSS.jpg`
- 自动清理过期文件

### 永久照片

- 保存目录：`permanent_dir`（默认：`permanent_captures`）
- 文件命名格式：`permanent_YYYYMMDD_HHMMSS.jpg`
- 不会自动清理

## 系统服务配置

### Windows

1. 运行创建服务命令：
   ```bash
   python camera_capture.py --create-service
   ```
2. 将生成的 `start_camera_capture_hidden.vbs`复制到启动文件夹

### Linux

1. 创建systemd服务文件
2. 安装并启用服务：
   ```bash
   sudo systemctl enable camera-capture.service
   sudo systemctl start camera-capture.service
   ```

### macOS

1. 创建LaunchAgent文件
2. 加载服务：
   ```bash
   launchctl load ~/Library/LaunchAgents/com.user.camera-capture.plist
   ```

## 停止抓拍

按 `Ctrl+C` 可以随时停止抓拍任务。

## 注意事项

1. 确保摄像头设备正常工作
2. 检查摄像头权限（特别是笔记本电脑）
3. 确保有足够的磁盘空间存储图片
4. 如果找不到摄像头，尝试更改camera_id参数（0, 1, 2等）

## 故障排除

- **无法打开摄像头**：检查摄像头是否被其他程序占用，尝试更换camera_id
- **权限错误**：以管理员权限运行脚本
- **依赖安装失败**：确保Python版本兼容，尝试使用虚拟环境

## 系统要求

- Python 3.6+
- OpenCV 4.5.0+
- 摄像头设备
