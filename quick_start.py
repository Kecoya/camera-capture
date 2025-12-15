#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速启动脚本 - 提供交互式界面配置抓拍参数
"""

import os
import sys
import json
from datetime import time as dt_time
from camera_capture import CameraCapture


def get_time_ranges():
    """获取多个抓拍时间段"""
    print("\n=== 配置抓拍时间段 ===")
    time_ranges = []

    while True:
        print(f"\n时间段 {len(time_ranges) + 1}:")

        # 开始时间
        while True:
            start_time_str = input("  请输入开始时间（格式：HH:MM，例如：09:00）: ")
            try:
                hour, minute = map(int, start_time_str.split(':'))
                start_time = dt_time(hour, minute)
                break
            except (ValueError, IndexError):
                print("  时间格式错误，请使用 HH:MM 格式")

        # 结束时间
        while True:
            end_time_str = input("  请输入结束时间（格式：HH:MM，例如：12:00）: ")
            try:
                hour, minute = map(int, end_time_str.split(':'))
                end_time = dt_time(hour, minute)
                break
            except (ValueError, IndexError):
                print("  时间格式错误，请使用 HH:MM 格式")

        # 抓拍间隔
        while True:
            try:
                interval = int(input("  请输入抓拍间隔（秒，默认30）: ") or "30")
                if interval <= 0:
                    print("  间隔时间必须大于0")
                    continue
                break
            except ValueError:
                print("  请输入有效的数字")

        time_ranges.append({
            "start": start_time.strftime('%H:%M'),
            "end": end_time.strftime('%H:%M'),
            "interval": interval
        })

        # 询问是否继续添加时间段
        if input("\n  是否继续添加时间段？(y/n): ").lower() not in ['y', 'yes', '是']:
            break

    return time_ranges


def get_fixed_times():
    """获取固定时间拍照点"""
    print("\n=== 配置固定时间拍照点（永久保存）===")
    fixed_times = []

    while True:
        print(f"\n固定时间点 {len(fixed_times) + 1}:")

        # 时间
        while True:
            time_str = input("  请输入拍照时间（格式：HH:MM，例如：08:00）: ")
            try:
                hour, minute = map(int, time_str.split(':'))
                photo_time = dt_time(hour, minute)
                break
            except (ValueError, IndexError):
                print("  时间格式错误，请使用 HH:MM 格式")

        # 描述
        description = input("  请输入描述（例如：早晨拍照）: ") or "定时拍照"

        fixed_times.append({
            "time": photo_time.strftime('%H:%M'),
            "description": description
        })

        # 询问是否继续添加固定时间点
        if input("\n  是否继续添加固定时间点？(y/n): ").lower() not in ['y', 'yes', '是']:
            break

    return fixed_times


def get_basic_config():
    """获取基本配置"""
    print("=" * 60)
    print("摄像头定时抓拍工具 - 快速配置")
    print("=" * 60)

    config = {}

    # 摄像头ID
    camera_id = 0
    camera_input = input("请输入摄像头ID（默认：0）: ")
    if camera_input.strip():
        try:
            camera_id = int(camera_input)
            if camera_id < 0:
                print("摄像头ID不能为负数，将使用默认值0")
                camera_id = 0
        except ValueError:
            print("输入无效，将使用默认值0")
    config["camera_id"] = camera_id

    # 临时照片目录
    temp_dir = input("请输入临时照片保存目录（默认：temp_captures）: ") or "temp_captures"
    config["temporary_dir"] = temp_dir

    # 永久照片目录
    permanent_dir = input("请输入永久照片保存目录（默认：permanent_captures）: ") or "permanent_captures"
    config["permanent_dir"] = permanent_dir

    # 最大临时照片数量
    max_temp = input("请输入最大临时照片数量（默认：1000）: ")
    if max_temp.strip():
        try:
            max_temp = int(max_temp)
            if max_temp <= 0:
                max_temp = 1000
        except ValueError:
            max_temp = 1000
    else:
        max_temp = 1000
    config["max_temp_captures"] = max_temp

    # 自动清理
    auto_cleanup = input("是否自动清理过期临时照片？(y/n，默认y): ").lower()
    config["auto_cleanup"] = auto_cleanup in ['y', 'yes', '是', '']

    # 清理天数
    if config["auto_cleanup"]:
        cleanup_days = input("请输入清理天数（默认：7天）: ")
        if cleanup_days.strip():
            try:
                cleanup_days = int(cleanup_days)
                if cleanup_days <= 0:
                    cleanup_days = 7
            except ValueError:
                cleanup_days = 7
        else:
            cleanup_days = 7
        config["cleanup_days"] = cleanup_days
    else:
        config["cleanup_days"] = 7

    return config


def confirm_config(config):
    """显示配置信息并确认"""
    print("\n" + "=" * 60)
    print("配置确认")
    print("=" * 60)
    print(f"摄像头ID：{config['camera_id']}")
    print(f"临时照片目录：{os.path.abspath(config['temporary_dir'])}")
    print(f"永久照片目录：{os.path.abspath(config['permanent_dir'])}")
    print(f"最大临时照片数量：{config['max_temp_captures']}")
    print(f"自动清理过期照片：{'是' if config['auto_cleanup'] else '否'}")
    if config['auto_cleanup']:
        print(f"清理天数：{config['cleanup_days']} 天")

    print(f"\n抓拍时间段（共{len(config['time_ranges'])}个）：")
    for i, time_range in enumerate(config['time_ranges'], 1):
        print(f"  {i}. {time_range['start']}-{time_range['end']}，间隔{time_range['interval']}秒")

    print(f"\n固定时间拍照点（共{len(config['fixed_times'])}个）：")
    for i, fixed_time in enumerate(config['fixed_times'], 1):
        print(f"  {i}. {fixed_time['time']} - {fixed_time['description']}")

    confirm = input("\n确认配置并开始抓拍？(y/n): ").lower().strip()
    return confirm in ['y', 'yes', '是', '']


def save_config_to_file(config, filename="camera_config.json"):
    """保存配置到文件"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print(f"配置已保存到：{filename}")
        return True
    except Exception as e:
        print(f"保存配置失败：{e}")
        return False


def main():
    """主函数"""
    try:
        # 获取基本配置
        basic_config = get_basic_config()

        # 获取时间段配置
        time_ranges = get_time_ranges()
        basic_config["time_ranges"] = time_ranges

        # 获取固定时间点配置
        fixed_times = get_fixed_times()
        basic_config["fixed_times"] = fixed_times

        # 确认配置
        if not confirm_config(basic_config):
            print("已取消")
            return

        # 询问是否保存配置
        save_config = input("\n是否保存配置到文件？(y/n): ").lower()
        if save_config in ['y', 'yes', '是']:
            filename = input("请输入配置文件名（默认：camera_config.json）: ") or "camera_config.json"
            save_config_to_file(basic_config, filename)

            # 询问是否立即使用配置启动
            start_now = input("是否立即使用此配置启动抓拍？(y/n): ").lower()
            if start_now not in ['y', 'yes', '是']:
                print("配置已保存，使用以下命令启动：")
                print(f"python camera_capture.py --config {filename}")
                return

            # 使用保存的配置启动
            capture_tool = CameraCapture(config_file=filename)
        else:
            # 直接使用配置启动（不保存）
            capture_tool = CameraCapture()
            capture_tool.config = basic_config

        print("\n开始抓拍任务...")
        capture_tool.start_all_capture()

    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
    except Exception as e:
        print(f"\n程序出错：{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()