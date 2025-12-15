#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
摄像头定时抓拍工具
功能：
1. 支持多个抓拍时间段
2. 固定时间点拍照（永久保存）
3. 区分临时照片和永久照片存储
4. 支持自启动服务
"""

import cv2
import os
import argparse
import time
import json
import threading
import sys
import schedule
from datetime import datetime, time as dt_time, timedelta
import platform
import subprocess
import signal
import winreg
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pystray
from PIL import Image, ImageDraw
import webbrowser
import glob


class CameraCapture:
    def __init__(self, config_file="camera_config.json"):
        """
        初始化摄像头抓拍工具

        Args:
            config_file (str): 配置文件路径
        """
        self.config_file = config_file
        self.camera = None
        self.is_running = False
        self.capture_threads = []
        self.schedule_threads = []
        self.is_hidden = False
        self.tray_icon = None
        self.config_window = None

        # 默认配置
        self.default_config = {
            "camera_id": 0,
            "temporary_dir": "temp_captures",
            "permanent_dir": "permanent_captures",
            "gif_dir": "gif_animations",
            "time_ranges": [
                {"start": "09:00", "end": "12:00", "interval": 30},
                {"start": "14:00", "end": "18:00", "interval": 60}
            ],
            "fixed_times": [
                {"time": "08:00", "description": "早晨拍照"},
                {"time": "20:00", "description": "晚上拍照"}
            ],
            "max_temp_captures": 1000,
            "auto_cleanup": True,
            "cleanup_days": 7,
            "gif_fps": 24,
            "gif_duration": 2.0,
            "enable_timestamp": True,
            "timestamp_color": [0, 0, 255],  # 红色 (BGR格式)
            "timestamp_scale": 1.0,
            "timestamp_thickness": 2
        }

        # 加载或创建配置
        self.config = self.load_config()

        # 创建输出目录
        os.makedirs(self.config["temporary_dir"], exist_ok=True)
        os.makedirs(self.config["permanent_dir"], exist_ok=True)
        os.makedirs(self.config["gif_dir"], exist_ok=True)

    def load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                print(f"配置已从 {self.config_file} 加载")
                return config
            except Exception as e:
                print(f"加载配置文件失败：{e}，使用默认配置")
                return self.default_config.copy()
        else:
            # 创建默认配置文件
            self.save_config(self.default_config)
            print(f"已创建默认配置文件：{self.config_file}")
            return self.default_config.copy()

    def save_config(self, config=None):
        """保存配置文件"""
        if config is None:
            config = self.config

        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            print(f"配置已保存到 {self.config_file}")
            return True
        except Exception as e:
            print(f"保存配置文件失败：{e}")
            return False

    def initialize_camera(self):
        """初始化摄像头"""
        # 如果摄像头已经初始化，直接返回成功
        if self.camera and self.camera.isOpened():
            return True

        try:
            self.camera = cv2.VideoCapture(self.config["camera_id"])
            if not self.camera.isOpened():
                print(f"错误：无法打开摄像头 {self.config['camera_id']}")
                self.camera = None
                return False

            # 设置摄像头参数
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self.camera.set(cv2.CAP_PROP_FPS, 30)

            print(f"摄像头 {self.config['camera_id']} 初始化成功")
            return True

        except Exception as e:
            print(f"摄像头初始化失败：{e}")
            self.camera = None
            return False

    def release_camera(self):
        """释放摄像头资源"""
        if self.camera:
            try:
                self.camera.release()
                print("摄像头资源已释放")
            except Exception as e:
                print(f"释放摄像头时出错：{e}")
            finally:
                self.camera = None

    def capture_image(self):
        """抓拍一张图片"""
        if not self.camera or not self.camera.isOpened():
            print("错误：摄像头未初始化")
            return None

        ret, frame = self.camera.read()
        if not ret:
            print("错误：无法读取摄像头画面")
            return None

        return frame

    def add_timestamp(self, frame, timestamp=None):
        """
        在图片上添加时间戳

        Args:
            frame: 图片帧
            timestamp: 时间戳，如果为None则使用当前时间

        Returns:
            numpy.ndarray: 添加了时间戳的图片帧
        """
        if not self.config.get("enable_timestamp", True):
            return frame

        if timestamp is None:
            timestamp = datetime.now()

        # 复制图片以避免修改原始帧
        frame_with_timestamp = frame.copy()

        # 获取配置
        timestamp_color = tuple(self.config.get("timestamp_color", [0, 0, 255]))
        timestamp_scale = self.config.get("timestamp_scale", 1.0)
        timestamp_thickness = self.config.get("timestamp_thickness", 2)

        # 生成时间戳文本
        timestamp_text = timestamp.strftime('%Y-%m-%d %H:%M:%S')

        # 计算文本大小
        font = cv2.FONT_HERSHEY_SIMPLEX
        (text_width, text_height), baseline = cv2.getTextSize(
            timestamp_text, font, timestamp_scale, timestamp_thickness
        )

        # 设置边距
        margin = 10
        x = frame.shape[1] - text_width - margin
        y = text_height + margin

        # 添加文本背景（可选，提高可读性）
        padding = 5
        cv2.rectangle(
            frame_with_timestamp,
            (x - padding, y - text_height - padding),
            (x + text_width + padding, y + baseline + padding),
            (0, 0, 0),  # 黑色背景
            -1  # 填充
        )

        # 添加时间戳文本
        cv2.putText(
            frame_with_timestamp,
            timestamp_text,
            (x, y),
            font,
            timestamp_scale,
            timestamp_color,
            timestamp_thickness,
            cv2.LINE_AA
        )

        return frame_with_timestamp

    def save_image(self, frame, timestamp=None, is_permanent=False):
        """
        保存图片到本地

        Args:
            frame: 图片帧
            timestamp: 时间戳，如果为None则使用当前时间
            is_permanent: 是否为永久保存

        Returns:
            str: 保存的文件路径
        """
        if timestamp is None:
            timestamp = datetime.now()

        # 添加时间戳
        frame_with_timestamp = self.add_timestamp(frame, timestamp)

        # 选择保存目录
        save_dir = self.config["permanent_dir"] if is_permanent else self.config["temporary_dir"]

        # 生成文件名
        prefix = "permanent" if is_permanent else "temp"
        filename = f"{prefix}_{timestamp.strftime('%Y%m%d_%H%M%S')}.jpg"
        filepath = os.path.join(save_dir, filename)

        try:
            cv2.imwrite(filepath, frame_with_timestamp)
            save_type = "永久" if is_permanent else "临时"
            print(f"{save_type}图片已保存：{filepath}")
            return filepath
        except Exception as e:
            print(f"保存图片失败：{e}")
            return None

    def create_gif_from_images(self, time_range, session_start):
        """
        从临时图片创建GIF动图

        Args:
            time_range: 时间范围配置
            session_start: 会话开始时间

        Returns:
            str: 生成的GIF文件路径，如果失败则返回None
        """
        try:
            print(f"开始生成GIF，时间段：{time_range['start']}-{time_range['end']}")
            print(f"临时图片目录：{self.config['temporary_dir']}")

            # 查找该时间段内的临时图片
            pattern = os.path.join(self.config["temporary_dir"],
                                  f"temp_{session_start.strftime('%Y%m%d')}*.jpg")
            print(f"搜索模式：{pattern}")

            image_files = glob.glob(pattern)
            print(f"找到 {len(image_files)} 个临时图片文件")

            # 按文件名排序（时间顺序）
            image_files.sort()

            # 输出找到的文件（调试用）
            for i, filepath in enumerate(image_files[:5]):  # 只显示前5个
                print(f"  文件 {i+1}: {os.path.basename(filepath)}")
            if len(image_files) > 5:
                print(f"  ... 还有 {len(image_files) - 5} 个文件")

            if len(image_files) < 2:
                print(f"时间段 {time_range['start']}-{time_range['end']} 图片数量不足，无法生成GIF")
                return None

            # 过滤出该时间段内的图片
            start_time = dt_time.fromisoformat(time_range["start"])
            end_time = dt_time.fromisoformat(time_range["end"])
            print(f"时间范围过滤：{start_time} - {end_time}")

            filtered_files = []
            for filepath in image_files:
                try:
                    filename = os.path.basename(filepath)
                    print(f"处理文件：{filename}")

                    # 修正文件名解析逻辑
                    if filename.startswith('temp_') and filename.endswith('.jpg'):
                        time_part = filename[5:-4]  # 去掉 'temp_' 和 '.jpg'
                        print(f"时间部分：{time_part}")

                        file_datetime = datetime.strptime(time_part, '%Y%m%d_%H%M%S')
                        file_time = file_datetime.time()
                        file_date = file_datetime.date()

                        session_date = session_start.date()

                        # 检查日期是否匹配且时间在范围内
                        if file_date == session_date and start_time <= file_time <= end_time:
                            filtered_files.append(filepath)
                            print(f"  -> 符合条件，已添加")
                        else:
                            print(f"  -> 不符合条件（日期:{file_date}!=_session_date:{session_date} 或 时间:{file_time} 不在范围内）")
                    else:
                        print(f"  -> 文件名格式不匹配")
                except (IndexError, ValueError) as e:
                    print(f"  -> 解析文件名时出错：{e}")
                    continue

            print(f"过滤后符合条件的文件数：{len(filtered_files)}")

            if len(filtered_files) < 2:
                print(f"时间段 {time_range['start']}-{time_range['end']} 有效图片数量不足，无法生成GIF")
                return None

            # 读取图片并转换为PIL格式
            images = []
            print("开始读取和转换图片...")
            for i, filepath in enumerate(filtered_files):
                try:
                    print(f"处理图片 {i+1}/{len(filtered_files)}: {os.path.basename(filepath)}")

                    # 使用OpenCV读取图片
                    cv_img = cv2.imread(filepath)
                    if cv_img is not None:
                        print(f"  -> OpenCV读取成功，尺寸: {cv_img.shape}")

                        # 转换BGR到RGB
                        rgb_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)

                        # 转换为PIL Image
                        pil_img = Image.fromarray(rgb_img)
                        print(f"  -> PIL转换成功，尺寸: {pil_img.size}")

                        # 可选：调整图片大小以减小GIF文件大小
                        width, height = pil_img.size
                        if width > 800:
                            new_width = 800
                            new_height = int(height * new_width / width)
                            pil_img = pil_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                            print(f"  -> 已调整大小为: {pil_img.size}")

                        images.append(pil_img)
                        print(f"  -> 图片已添加到GIF序列")
                    else:
                        print(f"  -> OpenCV读取失败")
                except Exception as e:
                    print(f"  -> 处理图片时出错：{e}")
                    continue

            print(f"成功处理的图片数：{len(images)}")

            if len(images) < 2:
                print(f"时间段 {time_range['start']}-{time_range['end']} 有效图片数量不足，无法生成GIF")
                return None

            # 生成GIF文件名
            gif_filename = f"gif_{session_start.strftime('%Y%m%d')}_{time_range['start'].replace(':', '')}_{time_range['end'].replace(':', '')}.gif"
            gif_filepath = os.path.join(self.config["gif_dir"], gif_filename)

            print(f"准备生成GIF文件：{gif_filepath}")

            # 计算帧间隔
            gif_fps = self.config.get("gif_fps", 10)
            duration = int(1000 / gif_fps)  # 毫秒
            print(f"GIF帧率：{gif_fps} FPS，帧间隔：{duration}ms")

            # 保存GIF
            print("开始保存GIF...")
            images[0].save(
                gif_filepath,
                format='GIF',
                append_images=images[1:],
                save_all=True,
                duration=duration,
                loop=0
            )

            print(f"GIF动图已生成：{gif_filepath} (包含 {len(images)} 帧图片)")
            return gif_filepath

        except Exception as e:
            print(f"生成GIF时出错：{e}")
            import traceback
            traceback.print_exc()
            return None

    def is_within_time_ranges(self):
        """检查当前时间是否在任何配置的时间段内"""
        current_time = datetime.now().time()

        for time_range in self.config["time_ranges"]:
            start_time = dt_time.fromisoformat(time_range["start"])
            end_time = dt_time.fromisoformat(time_range["end"])

            # 处理跨天的情况
            if start_time > end_time:
                if current_time >= start_time or current_time <= end_time:
                    return True, time_range
            else:
                if start_time <= current_time <= end_time:
                    return True, time_range

        return False, None

    def cleanup_old_files(self):
        """清理过期的临时文件"""
        if not self.config["auto_cleanup"]:
            return

        cutoff_date = datetime.now() - timedelta(days=self.config["cleanup_days"])
        deleted_count = 0

        try:
            # 清理临时图片目录
            for filename in os.listdir(self.config["temporary_dir"]):
                filepath = os.path.join(self.config["temporary_dir"], filename)
                if os.path.isfile(filepath):
                    # 从文件名提取时间戳
                    try:
                        # 假设文件名格式为 temp_YYYYMMDD_HHMMSS.jpg
                        date_part = filename.split('_')[1:3]
                        file_date = datetime.strptime('_'.join(date_part), '%Y%m%d_%H%M%S')

                        if file_date < cutoff_date:
                            os.remove(filepath)
                            deleted_count += 1
                    except (IndexError, ValueError):
                        continue

            # 注意：GIF文件不会被清理，因为它们保存在单独的gif_dir目录中
            # GIF文件是永久保存的，不会被自动清理

            if deleted_count > 0:
                print(f"已清理 {deleted_count} 个过期临时文件")

        except Exception as e:
            print(f"清理文件时出错：{e}")

    def temporary_capture_worker(self, time_range):
        """临时抓拍工作线程"""
        interval = time_range["interval"]
        capture_count = 0
        max_captures = self.config.get("max_temp_captures", 1000)
        session_start = datetime.now()

        print(f"开始时间段抓拍：{time_range['start']}-{time_range['end']}，间隔{interval}秒")
        print(f"会话开始时间：{session_start.strftime('%Y-%m-%d %H:%M:%S')}")

        # 在时间段开始时初始化摄像头
        if not self.initialize_camera():
            print(f"摄像头初始化失败，跳过时间段 {time_range['start']}-{time_range['end']}")
            return

        try:
            while self.is_running:
                # 检查是否仍在时间段内
                in_range, current_range = self.is_within_time_ranges()
                if not in_range or current_range["start"] != time_range["start"]:
                    print(f"时间段 {time_range['start']}-{time_range['end']} 结束")
                    break

                # 检查最大抓拍数量
                if capture_count >= max_captures:
                    print(f"已达到最大临时抓拍数量 {max_captures}")
                    break

                # 执行抓拍
                frame = self.capture_image()
                if frame is not None:
                    self.save_image(frame, is_permanent=False)
                    capture_count += 1

                # 等待下一次抓拍
                time.sleep(interval)

        finally:
            # 时间段结束时释放摄像头
            self.release_camera()
            print(f"摄像头已释放（时间段 {time_range['start']}-{time_range['end']} 结束）")

            # 生成GIF动图
            if capture_count >= 2:  # 至少需要2张图片才能生成GIF
                print(f"开始为时间段 {time_range['start']}-{time_range['end']} 生成GIF动图...")
                gif_path = self.create_gif_from_images(time_range, session_start)
                if gif_path:
                    print(f"时间段 {time_range['start']}-{time_range['end']} 的GIF动图已保存")
                else:
                    print(f"时间段 {time_range['start']}-{time_range['end']} GIF生成失败")
            else:
                print(f"时间段 {time_range['start']}-{time_range['end']} 图片数量不足，跳过GIF生成")

    def fixed_time_capture(self, time_info):
        """固定时间点拍照"""
        print(f"执行固定时间拍照：{time_info['time']} - {time_info['description']}")

        # 临时初始化摄像头进行拍照
        if self.initialize_camera():
            try:
                frame = self.capture_image()
                if frame is not None:
                    self.save_image(frame, is_permanent=True)
            finally:
                # 拍照完成后立即释放摄像头
                self.release_camera()
                print(f"固定时间拍照完成，摄像头已释放")
        else:
            print(f"摄像头初始化失败，跳过固定时间拍照：{time_info['time']}")

    def setup_schedule(self):
        """设置固定时间拍照计划"""
        schedule.clear()

        for time_info in self.config["fixed_times"]:
            schedule.every().day.at(time_info["time"]).do(
                self.fixed_time_capture, time_info=time_info
            )
            print(f"已设置固定拍照时间：{time_info['time']} - {time_info['description']}")

    def schedule_worker(self):
        """调度工作线程"""
        while self.is_running:
            schedule.run_pending()
            time.sleep(1)

    def start_all_capture(self):
        """启动所有抓拍任务"""
        self.is_running = True

        # 设置固定时间拍照
        self.setup_schedule()
        schedule_thread = threading.Thread(target=self.schedule_worker, daemon=True)
        schedule_thread.start()
        self.schedule_threads.append(schedule_thread)

        print("抓拍任务调度器已启动（智能摄像头管理）")
        print("摄像头将在需要时自动初始化，不需要时自动释放")
        print("按 Ctrl+C 停止抓拍")

        try:
            while self.is_running:
                # 检查是否在任何时间段内
                in_range, time_range = self.is_within_time_ranges()

                if in_range:
                    # 检查是否已经有该时间段的线程在运行
                    thread_already_running = any(
                        t.is_alive() for t in self.capture_threads
                        if hasattr(t, 'time_range_start') and t.time_range_start == time_range["start"]
                    )

                    if not thread_already_running:
                        print(f"进入抓拍时间段 {time_range['start']}-{time_range['end']}，准备启动摄像头")
                        # 启动新的时间段抓拍线程
                        thread = threading.Thread(
                            target=self.temporary_capture_worker,
                            args=(time_range,),
                            daemon=True
                        )
                        thread.time_range_start = time_range["start"]
                        thread.start()
                        self.capture_threads.append(thread)
                else:
                    # 不在任何时间段内，确保摄像头已释放
                    if self.camera:
                        print("当前不在抓拍时间段，释放摄像头资源")
                        self.release_camera()

                # 定期清理过期文件（每小时一次）
                current_min = datetime.now().minute
                if current_min == 0:  # 整点时清理
                    self.cleanup_old_files()

                time.sleep(30)  # 每30秒检查一次时间段状态

        except KeyboardInterrupt:
            print("\n用户中断，停止抓拍")
        finally:
            self.stop_capture()

        return True

    def stop_capture(self):
        """停止抓拍并释放资源"""
        self.is_running = False

        # 等待所有线程结束
        for thread in self.capture_threads + self.schedule_threads:
            if thread.is_alive():
                thread.join(timeout=2)

        # 释放摄像头资源
        self.release_camera()

        # 关闭所有OpenCV窗口
        cv2.destroyAllWindows()

        print("所有抓拍任务已停止，摄像头已释放")

    def create_service_file(self):
        """创建系统服务文件"""
        system = platform.system().lower()

        if system == "linux":
            return self.create_linux_service()
        elif system == "darwin":  # macOS
            return self.create_macos_service()
        elif system == "windows":
            return self.create_windows_service()
        else:
            print(f"不支持的操作系统：{system}")
            return False

    def create_linux_service(self):
        """创建Linux systemd服务"""
        service_content = f"""[Unit]
Description=Camera Capture Service
After=network.target

[Service]
Type=simple
User={os.getenv('USER', 'root')}
WorkingDirectory={os.getcwd()}
ExecStart={sys.executable} {os.path.abspath(__file__)} --config {self.config_file}
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""

        service_file = "/etc/systemd/system/camera-capture.service"

        try:
            with open("camera-capture.service", 'w') as f:
                f.write(service_content)

            print(f"Linux服务文件已创建：camera-capture.service")
            print("请执行以下命令安装服务：")
            print(f"  sudo cp camera-capture.service {service_file}")
            print("  sudo systemctl daemon-reload")
            print("  sudo systemctl enable camera-capture.service")
            print("  sudo systemctl start camera-capture.service")
            return True
        except Exception as e:
            print(f"创建服务文件失败：{e}")
            return False

    def create_macos_service(self):
        """创建macOS LaunchAgent"""
        plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.camera-capture</string>
    <key>ProgramArguments</key>
    <array>
        <string>{sys.executable}</string>
        <string>{os.path.abspath(__file__)}</string>
        <string>--config</string>
        <string>{os.path.abspath(self.config_file)}</string>
    </array>
    <key>WorkingDirectory</key>
    <string>{os.getcwd()}</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/camera-capture.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/camera-capture.error.log</string>
</dict>
</plist>
"""

        try:
            with open("com.user.camera-capture.plist", 'w') as f:
                f.write(plist_content)

            print(f"macOS LaunchAgent文件已创建：com.user.camera-capture.plist")
            print("请执行以下命令安装服务：")
            print("  cp com.user.camera-capture.plist ~/Library/LaunchAgents/")
            print("  launchctl load ~/Library/LaunchAgents/com.user.camera-capture.plist")
            return True
        except Exception as e:
            print(f"创建服务文件失败：{e}")
            return False

    def create_windows_service(self):
        """创建Windows服务脚本"""
        bat_content = f"""@echo off
echo Starting Camera Capture Service...
cd /d "{os.getcwd()}"
"{sys.executable}" "{os.path.abspath(__file__)}" --config "{os.path.abspath(self.config_file)}"
pause
"""

        vbs_content = f"""Set WshShell = CreateObject("WScript.Shell")
WshShell.Run chr(34) & "{os.getcwd()}\\start_camera_capture.bat" & chr(34), 0
Set WshShell = Nothing
"""

        try:
            with open("start_camera_capture.bat", 'w') as f:
                f.write(bat_content)

            with open("start_camera_capture_hidden.vbs", 'w') as f:
                f.write(vbs_content)

            print(f"Windows服务脚本已创建：")
            print("  start_camera_capture.bat - 可见窗口启动")
            print("  start_camera_capture_hidden.vbs - 隐藏窗口启动")
            print("\n要开机自启动，请：")
            print("1. Win+R 打开运行对话框")
            print("2. 输入 shell:startup 并回车")
            print("3. 将 start_camera_capture_hidden.vbs 复制到启动文件夹")
            return True
        except Exception as e:
            print(f"创建服务文件失败：{e}")
            return False

    def is_windows(self):
        """检查是否为Windows系统"""
        return platform.system().lower() == "windows"

    def get_startup_registry_key(self):
        """获取Windows启动注册表路径"""
        return winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                              r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
                              0, winreg.KEY_ALL_ACCESS)

    def is_startup_enabled(self):
        """检查是否已设置开机启动"""
        if not self.is_windows():
            return False

        try:
            with self.get_startup_registry_key() as key:
                try:
                    winreg.QueryValueEx(key, "CameraCapture")
                    return True
                except WindowsError:
                    return False
        except Exception as e:
            print(f"检查开机启动状态失败：{e}")
            return False

    def enable_startup(self, hidden=True):
        """启用开机启动"""
        if not self.is_windows():
            print("开机启动功能仅支持Windows系统")
            return False

        try:
            # 获取Python脚本的完整路径
            script_path = os.path.abspath(__file__)
            python_exe = sys.executable

            # 构建启动命令
            if hidden:
                # 隐藏窗口启动，使用VBScript
                vbs_path = os.path.join(os.getcwd(), "start_camera_capture_hidden.vbs")
                command = f'wscript "{vbs_path}"'
            else:
                # 可见窗口启动
                command = f'"{python_exe}" "{script_path}"'

            # 写入注册表
            with self.get_startup_registry_key() as key:
                winreg.SetValueEx(key, "CameraCapture", 0, winreg.REG_SZ, command)

            startup_mode = "隐藏模式" if hidden else "可见模式"
            print(f"开机启动已启用 ({startup_mode})")
            return True

        except Exception as e:
            print(f"启用开机启动失败：{e}")
            return False

    def disable_startup(self):
        """禁用开机启动"""
        if not self.is_windows():
            print("开机启动功能仅支持Windows系统")
            return False

        try:
            with self.get_startup_registry_key() as key:
                try:
                    winreg.DeleteValue(key, "CameraCapture")
                    print("开机启动已禁用")
                    return True
                except WindowsError:
                    print("开机启动项不存在")
                    return False
        except Exception as e:
            print(f"禁用开机启动失败：{e}")
            return False

    def create_tray_icon_image(self):
        """创建托盘图标"""
        # 创建一个简单的相机图标
        image = Image.new('RGB', (64, 64), color='white')
        draw = ImageDraw.Draw(image)

        # 绘制简单的相机形状
        draw.rectangle([10, 15, 54, 45], fill='black', outline='black')
        draw.rectangle([20, 5, 44, 15], fill='black')
        draw.ellipse([25, 20, 39, 34], fill='white', outline='black')
        draw.ellipse([30, 25, 34, 29], fill='black')

        return image

    def setup_tray_icon(self):
        """设置系统托盘图标"""
        if self.tray_icon is not None:
            return

        def show_config(icon, item):
            """显示配置窗口"""
            self.show_config_window()

        def toggle_capture(icon, item):
            """切换抓拍状态"""
            if self.is_running:
                self.stop_capture()
                icon.title = "摄像头抓拍 - 已停止"
            else:
                # 在新线程中启动抓拍
                threading.Thread(target=self.start_all_capture, daemon=True).start()
                icon.title = "摄像头抓拍 - 运行中"

        def open_captured_folder(icon, item):
            """打开抓拍文件夹"""
            temp_dir = os.path.abspath(self.config["temporary_dir"])
            perm_dir = os.path.abspath(self.config["permanent_dir"])
            gif_dir = os.path.abspath(self.config["gif_dir"])

            # 在资源管理器中打开临时文件夹
            if os.path.exists(temp_dir):
                os.startfile(temp_dir)

        def toggle_startup(icon, item):
            """切换开机启动状态"""
            if self.is_startup_enabled():
                if self.disable_startup():
                    messagebox.showinfo("提示", "开机启动已禁用")
                else:
                    messagebox.showerror("错误", "禁用开机启动失败")
            else:
                if self.enable_startup(hidden=True):
                    messagebox.showinfo("提示", "开机启动已启用（隐藏模式）")
                else:
                    messagebox.showerror("错误", "启用开机启动失败")

        def quit_application(icon, item):
            """退出应用程序"""
            self.stop_capture()
            icon.stop()

        # 创建菜单
        menu = pystray.Menu(
            pystray.MenuItem("显示配置窗口", show_config),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("启动/停止抓拍", toggle_capture),
            pystray.MenuItem("开机启动", toggle_startup,
                           checked=lambda item: self.is_startup_enabled()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("打开抓拍文件夹", open_captured_folder),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("退出", quit_application)
        )

        # 创建托盘图标
        self.tray_icon = pystray.Icon(
            "camera_capture",
            self.create_tray_icon_image(),
            "摄像头抓拍工具",
            menu
        )

    def show_config_window(self):
        """显示配置窗口"""
        if self.config_window is not None:
            self.config_window.lift()
            self.config_window.focus()
            return

        self.config_window = tk.Tk()
        self.config_window.title("摄像头抓拍工具配置")
        self.config_window.geometry("600x500")
        self.config_window.resizable(False, False)

        # 创建笔记本（选项卡）
        notebook = ttk.Notebook(self.config_window)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # 基本设置选项卡
        basic_frame = ttk.Frame(notebook)
        notebook.add(basic_frame, text="基本设置")

        # 抓拍设置选项卡
        capture_frame = ttk.Frame(notebook)
        notebook.add(capture_frame, text="抓拍设置")

        # 启动设置选项卡
        startup_frame = ttk.Frame(notebook)
        notebook.add(startup_frame, text="启动设置")

        # 基本设置控件
        ttk.Label(basic_frame, text="摄像头ID:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        camera_id_var = tk.IntVar(value=self.config["camera_id"])
        ttk.Spinbox(basic_frame, from_=0, to=10, textvariable=camera_id_var, width=10).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(basic_frame, text="临时照片目录:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        temp_dir_var = tk.StringVar(value=self.config["temporary_dir"])
        temp_frame = ttk.Frame(basic_frame)
        temp_frame.grid(row=1, column=1, columnspan=2, sticky='ew', padx=5, pady=5)
        ttk.Entry(temp_frame, textvariable=temp_dir_var, width=30).pack(side='left', fill='x', expand=True)
        ttk.Button(temp_frame, text="浏览", command=lambda: self.browse_folder(temp_dir_var)).pack(side='right', padx=(5, 0))

        ttk.Label(basic_frame, text="永久照片目录:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        perm_dir_var = tk.StringVar(value=self.config["permanent_dir"])
        perm_frame = ttk.Frame(basic_frame)
        perm_frame.grid(row=2, column=1, columnspan=2, sticky='ew', padx=5, pady=5)
        ttk.Entry(perm_frame, textvariable=perm_dir_var, width=30).pack(side='left', fill='x', expand=True)
        ttk.Button(perm_frame, text="浏览", command=lambda: self.browse_folder(perm_dir_var)).pack(side='right', padx=(5, 0))

        ttk.Label(basic_frame, text="GIF动图目录:").grid(row=3, column=0, sticky='w', padx=5, pady=5)
        gif_dir_var = tk.StringVar(value=self.config["gif_dir"])
        gif_frame = ttk.Frame(basic_frame)
        gif_frame.grid(row=3, column=1, columnspan=2, sticky='ew', padx=5, pady=5)
        ttk.Entry(gif_frame, textvariable=gif_dir_var, width=30).pack(side='left', fill='x', expand=True)
        ttk.Button(gif_frame, text="浏览", command=lambda: self.browse_folder(gif_dir_var)).pack(side='right', padx=(5, 0))

        ttk.Label(basic_frame, text="最大临时照片数:").grid(row=4, column=0, sticky='w', padx=5, pady=5)
        max_temp_var = tk.IntVar(value=self.config.get("max_temp_captures", 1000))
        ttk.Spinbox(basic_frame, from_=100, to=10000, textvariable=max_temp_var, width=10).grid(row=4, column=1, padx=5, pady=5)

        ttk.Label(basic_frame, text="GIF帧率(FPS):").grid(row=5, column=0, sticky='w', padx=5, pady=5)
        gif_fps_var = tk.IntVar(value=self.config.get("gif_fps", 24))
        ttk.Spinbox(basic_frame, from_=1, to=30, textvariable=gif_fps_var, width=10).grid(row=5, column=1, padx=5, pady=5)

        # 时间戳设置
        ttk.Label(basic_frame, text="启用时间戳:").grid(row=6, column=0, sticky='w', padx=5, pady=5)
        timestamp_enable_var = tk.BooleanVar(value=self.config.get("enable_timestamp", True))
        ttk.Checkbutton(basic_frame, variable=timestamp_enable_var).grid(row=6, column=1, sticky='w', padx=5, pady=5)

        ttk.Label(basic_frame, text="时间戳大小:").grid(row=7, column=0, sticky='w', padx=5, pady=5)
        timestamp_scale_var = tk.DoubleVar(value=self.config.get("timestamp_scale", 1.0))
        ttk.Spinbox(basic_frame, from_=0.5, to=3.0, increment=0.1, textvariable=timestamp_scale_var, width=10).grid(row=7, column=1, padx=5, pady=5)

        # 启动设置控件
        startup_status_var = tk.BooleanVar(value=self.is_startup_enabled())
        ttk.Checkbutton(startup_frame, text="开机自动启动", variable=startup_status_var).grid(row=0, column=0, sticky='w', padx=5, pady=5)

        hidden_startup_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(startup_frame, text="隐藏窗口启动", variable=hidden_startup_var).grid(row=1, column=0, sticky='w', padx=5, pady=5)

        # 状态显示
        status_frame = ttk.LabelFrame(startup_frame, text="当前状态")
        status_frame.grid(row=2, column=0, columnspan=2, sticky='ew', padx=5, pady=10)

        status_text = f"运行状态: {'运行中' if self.is_running else '已停止'}\n"
        status_text += f"开机启动: {'已启用' if self.is_startup_enabled() else '已禁用'}"
        ttk.Label(status_frame, text=status_text, justify='left').pack(padx=5, pady=5)

        # 按钮框架
        button_frame = ttk.Frame(self.config_window)
        button_frame.pack(fill='x', padx=10, pady=10)

        def save_config():
            """保存配置"""
            self.config["camera_id"] = camera_id_var.get()
            self.config["temporary_dir"] = temp_dir_var.get()
            self.config["permanent_dir"] = perm_dir_var.get()
            self.config["gif_dir"] = gif_dir_var.get()
            self.config["max_temp_captures"] = max_temp_var.get()
            self.config["gif_fps"] = gif_fps_var.get()
            self.config["enable_timestamp"] = timestamp_enable_var.get()
            self.config["timestamp_scale"] = timestamp_scale_var.get()

            # 重新创建目录（如果更改了目录）
            os.makedirs(self.config["gif_dir"], exist_ok=True)

            if self.save_config():
                messagebox.showinfo("成功", "配置已保存")
            else:
                messagebox.showerror("错误", "配置保存失败")

        def apply_startup_settings():
            """应用启动设置"""
            if startup_status_var.get():
                if self.enable_startup(hidden=hidden_startup_var.get()):
                    messagebox.showinfo("成功", f"开机启动已启用（{'隐藏' if hidden_startup_var.get() else '可见'}模式）")
                else:
                    messagebox.showerror("错误", "设置开机启动失败")
            else:
                if self.disable_startup():
                    messagebox.showinfo("成功", "开机启动已禁用")
                else:
                    messagebox.showerror("错误", "禁用开机启动失败")

        def start_hidden():
            """隐藏窗口并最小化到托盘"""
            self.config_window.withdraw()
            if self.tray_icon is None:
                self.setup_tray_icon()
                threading.Thread(target=self.tray_icon.run, daemon=True).start()

        ttk.Button(button_frame, text="保存配置", command=save_config).pack(side='left', padx=5)
        ttk.Button(button_frame, text="应用启动设置", command=apply_startup_settings).pack(side='left', padx=5)
        ttk.Button(button_frame, text="隐藏到托盘", command=start_hidden).pack(side='left', padx=5)
        ttk.Button(button_frame, text="关闭", command=self.config_window.destroy).pack(side='right', padx=5)

        def on_closing():
            """窗口关闭事件"""
            self.config_window.destroy()
            self.config_window = None

        self.config_window.protocol("WM_DELETE_WINDOW", on_closing)
        self.config_window.mainloop()

    def browse_folder(self, var):
        """浏览文件夹"""
        folder = filedialog.askdirectory(initialdir=var.get())
        if folder:
            var.set(folder)

    def run_with_tray(self):
        """带托盘图标运行"""
        self.setup_tray_icon()
        self.tray_icon.run()

    def run_hidden(self):
        """隐藏模式运行"""
        self.is_hidden = True
        # 在新线程中启动抓拍
        capture_thread = threading.Thread(target=self.start_all_capture, daemon=True)
        capture_thread.start()

        # 设置托盘图标
        self.setup_tray_icon()
        self.tray_icon.run()


def parse_time_string(time_str):
    """解析时间字符串"""
    try:
        hour, minute = map(int, time_str.split(':'))
        return dt_time(hour, minute)
    except ValueError:
        raise argparse.ArgumentTypeError(f"无效的时间格式：{time_str}，请使用 HH:MM 格式")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="摄像头定时抓拍工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例：
  # 使用默认配置启动
  python camera_capture.py

  # 指定配置文件
  python camera_capture.py --config my_config.json

  # 创建系统服务
  python camera_capture.py --create-service

  # 编辑配置
  python camera_capture.py --edit-config

  # 显示配置窗口
  python camera_capture.py --gui

  # 隐藏模式运行（最小化到托盘）
  python camera_capture.py --hidden

  # 启用开机启动
  python camera_capture.py --enable-startup

  # 禁用开机启动
  python camera_capture.py --disable-startup
        """
    )

    parser.add_argument(
        '--config', '-c',
        type=str,
        default='camera_config.json',
        help='配置文件路径，默认为camera_config.json'
    )

    parser.add_argument(
        '--create-service',
        action='store_true',
        help='创建系统服务文件'
    )

    parser.add_argument(
        '--edit-config',
        action='store_true',
        help='编辑配置文件'
    )

    parser.add_argument(
        '--gui', '--config-window',
        action='store_true',
        help='显示图形配置窗口'
    )

    parser.add_argument(
        '--hidden', '--tray',
        action='store_true',
        help='隐藏模式运行（最小化到系统托盘）'
    )

    parser.add_argument(
        '--enable-startup',
        action='store_true',
        help='启用开机启动（默认隐藏模式）'
    )

    parser.add_argument(
        '--disable-startup',
        action='store_true',
        help='禁用开机启动'
    )

    parser.add_argument(
        '--startup-visible',
        action='store_true',
        help='开机启动时显示窗口（与--enable-startup配合使用）'
    )

    args = parser.parse_args()

    # 创建抓拍工具实例
    capture_tool = CameraCapture(config_file=args.config)

    # 处理开机启动相关命令
    if args.enable_startup:
        hidden_mode = not args.startup_visible
        if capture_tool.enable_startup(hidden=hidden_mode):
            mode_text = "隐藏模式" if hidden_mode else "可见模式"
            print(f"开机启动已启用 ({mode_text})")
        else:
            print("启用开机启动失败")
        return

    if args.disable_startup:
        if capture_tool.disable_startup():
            print("开机启动已禁用")
        else:
            print("禁用开机启动失败")
        return

    # 处理其他命令
    if args.create_service:
        capture_tool.create_service_file()
        return

    if args.edit_config:
        print(f"请编辑配置文件：{args.config}")
        print("配置文件内容示例：")
        print(json.dumps(capture_tool.default_config, ensure_ascii=False, indent=2))
        return

    if args.gui:
        # 显示图形配置窗口
        capture_tool.show_config_window()
        return

    if args.hidden:
        # 隐藏模式运行
        print("以隐藏模式启动...")
        capture_tool.run_hidden()
        return

    # 默认启动抓拍任务
    print("配置信息：")
    print(json.dumps(capture_tool.config, ensure_ascii=False, indent=2))
    print()

    capture_tool.start_all_capture()


if __name__ == "__main__":
    main()