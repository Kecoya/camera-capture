#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理脚本 - 管理摄像头抓拍工具的配置
"""

import json
import os
import sys
import copy
from datetime import time as dt_time
from camera_capture import CameraCapture


class ConfigManager:
    def __init__(self):
        self.config_file = "camera_config.json"
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
            "enable_timestamp": True,
            "timestamp_color": [0, 0, 255],
            "timestamp_scale": 1.0,
            "timestamp_thickness": 2
        }

    def show_menu(self):
        """显示主菜单"""
        print("\n" + "=" * 50)
        print("摄像头抓拍工具 - 配置管理")
        print("=" * 50)
        print("1. 查看当前配置")
        print("2. 编辑配置")
        print("3. 创建新配置")
        print("4. 导入配置")
        print("5. 导出配置")
        print("6. 测试配置")
        print("7. 创建系统服务")
        print("0. 退出")
        print("-" * 50)

    def show_current_config(self):
        """显示当前配置"""
        if not os.path.exists(self.config_file):
            print("当前没有配置文件")
            return

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            print(f"\n当前配置文件：{self.config_file}")
            print("-" * 30)
            print(json.dumps(config, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"读取配置文件失败：{e}")

    def edit_config(self):
        """编辑配置"""
        if not os.path.exists(self.config_file):
            print("配置文件不存在，将创建新配置")
            config = copy.deepcopy(self.default_config)
        else:
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            except Exception as e:
                print(f"读取配置文件失败：{e}，使用默认配置")
                config = copy.deepcopy(self.default_config)

        print("\n配置编辑（直接回车保持原值）：")

        # 编辑摄像头ID
        current_id = config.get("camera_id", 0)
        new_id = input(f"摄像头ID（当前：{current_id}）: ").strip()
        if new_id:
            try:
                config["camera_id"] = int(new_id)
            except ValueError:
                print("输入无效，保持原值")

        # 编辑临时目录
        current_temp = config.get("temporary_dir", "temp_captures")
        new_temp = input(f"临时照片目录（当前：{current_temp}）: ").strip()
        if new_temp:
            config["temporary_dir"] = new_temp

        # 编辑永久目录
        current_permanent = config.get("permanent_dir", "permanent_captures")
        new_permanent = input(f"永久照片目录（当前：{current_permanent}）: ").strip()
        if new_permanent:
            config["permanent_dir"] = new_permanent

        # 编辑最大临时照片数量
        current_max = config.get("max_temp_captures", 1000)
        new_max = input(f"最大临时照片数量（当前：{current_max}）: ").strip()
        if new_max:
            try:
                config["max_temp_captures"] = int(new_max)
            except ValueError:
                print("输入无效，保持原值")

        # 编辑自动清理
        current_cleanup = config.get("auto_cleanup", True)
        new_cleanup = input(f"自动清理过期照片（当前：{current_cleanup}，y/n）: ").strip().lower()
        if new_cleanup:
            config["auto_cleanup"] = new_cleanup in ['y', 'yes', '是']

        # 编辑清理天数
        if config["auto_cleanup"]:
            current_days = config.get("cleanup_days", 7)
            new_days = input(f"清理天数（当前：{current_days}）: ").strip()
            if new_days:
                try:
                    config["cleanup_days"] = int(new_days)
                except ValueError:
                    print("输入无效，保持原值")

        # 编辑时间段
        edit_ranges = input("是否编辑抓拍时间段？(y/n): ").strip().lower()
        if edit_ranges in ['y', 'yes', '是']:
            config["time_ranges"] = self.edit_time_ranges(config.get("time_ranges", []))

        # 编辑固定时间点
        edit_fixed = input("是否编辑固定时间拍照点？(y/n): ").strip().lower()
        if edit_fixed in ['y', 'yes', '是']:
            config["fixed_times"] = self.edit_fixed_times(config.get("fixed_times", []))

        # 保存配置
        self.save_config(config)

    def edit_time_ranges(self, current_ranges):
        """编辑时间段"""
        print(f"\n当前时间段（共{len(current_ranges)}个）：")
        for i, time_range in enumerate(current_ranges, 1):
            print(f"  {i}. {time_range['start']}-{time_range['end']}，间隔{time_range['interval']}秒")

        print("\n选择操作：")
        print("1. 添加时间段")
        print("2. 修改时间段")
        print("3. 删除时间段")
        print("4. 返回")

        choice = input("请选择（1-4）: ").strip()

        if choice == "1":
            return self.add_time_range(current_ranges)
        elif choice == "2":
            return self.modify_time_range(current_ranges)
        elif choice == "3":
            return self.delete_time_range(current_ranges)
        else:
            return current_ranges

    def add_time_range(self, ranges):
        """添加时间段"""
        print("\n添加新时间段：")

        # 开始时间
        while True:
            start_time_str = input("  请输入开始时间（格式：HH:MM）: ")
            try:
                hour, minute = map(int, start_time_str.split(':'))
                start_time = dt_time(hour, minute)
                break
            except (ValueError, IndexError):
                print("  时间格式错误，请使用 HH:MM 格式")

        # 结束时间
        while True:
            end_time_str = input("  请输入结束时间（格式：HH:MM）: ")
            try:
                hour, minute = map(int, end_time_str.split(':'))
                end_time = dt_time(hour, minute)
                break
            except (ValueError, IndexError):
                print("  时间格式错误，请使用 HH:MM 格式")

        # 间隔
        while True:
            try:
                interval = int(input("  请输入抓拍间隔（秒）: "))
                if interval <= 0:
                    print("  间隔时间必须大于0")
                    continue
                break
            except ValueError:
                print("  请输入有效的数字")

        ranges.append({
            "start": start_time.strftime('%H:%M'),
            "end": end_time.strftime('%H:%M'),
            "interval": interval
        })

        print("时间段已添加")
        return ranges

    def modify_time_range(self, ranges):
        """修改时间段"""
        if not ranges:
            print("没有可修改的时间段")
            return ranges

        print(f"\n选择要修改的时间段：")
        for i, time_range in enumerate(ranges, 1):
            print(f"  {i}. {time_range['start']}-{time_range['end']}，间隔{time_range['interval']}秒")

        try:
            index = int(input("请选择时间段编号：")) - 1
            if 0 <= index < len(ranges):
                print(f"当前时间段：{ranges[index]['start']}-{ranges[index]['end']}，间隔{ranges[index]['interval']}秒")

                # 修改各项
                new_start = input(f"新的开始时间（当前：{ranges[index]['start']}，回车保持）: ").strip()
                if new_start:
                    try:
                        hour, minute = map(int, new_start.split(':'))
                        ranges[index]['start'] = dt_time(hour, minute).strftime('%H:%M')
                    except ValueError:
                        print("时间格式错误，保持原值")

                new_end = input(f"新的结束时间（当前：{ranges[index]['end']}，回车保持）: ").strip()
                if new_end:
                    try:
                        hour, minute = map(int, new_end.split(':'))
                        ranges[index]['end'] = dt_time(hour, minute).strftime('%H:%M')
                    except ValueError:
                        print("时间格式错误，保持原值")

                new_interval = input(f"新的间隔时间（当前：{ranges[index]['interval']}，回车保持）: ").strip()
                if new_interval:
                    try:
                        ranges[index]['interval'] = int(new_interval)
                    except ValueError:
                        print("输入无效，保持原值")

                print("时间段已修改")
            else:
                print("编号无效")
        except ValueError:
            print("请输入有效的编号")

        return ranges

    def delete_time_range(self, ranges):
        """删除时间段"""
        if not ranges:
            print("没有可删除的时间段")
            return ranges

        print(f"\n选择要删除的时间段：")
        for i, time_range in enumerate(ranges, 1):
            print(f"  {i}. {time_range['start']}-{time_range['end']}，间隔{time_range['interval']}秒")

        try:
            index = int(input("请选择时间段编号：")) - 1
            if 0 <= index < len(ranges):
                deleted = ranges.pop(index)
                print(f"已删除时间段：{deleted['start']}-{deleted['end']}")
            else:
                print("编号无效")
        except ValueError:
            print("请输入有效的编号")

        return ranges

    def edit_fixed_times(self, current_times):
        """编辑固定时间拍照点"""
        print(f"\n当前固定时间拍照点（共{len(current_times)}个）：")
        for i, fixed_time in enumerate(current_times, 1):
            print(f"  {i}. {fixed_time['time']} - {fixed_time['description']}")

        print("\n选择操作：")
        print("1. 添加固定时间点")
        print("2. 修改固定时间点")
        print("3. 删除固定时间点")
        print("4. 返回")

        choice = input("请选择（1-4）: ").strip()

        if choice == "1":
            return self.add_fixed_time(current_times)
        elif choice == "2":
            return self.modify_fixed_time(current_times)
        elif choice == "3":
            return self.delete_fixed_time(current_times)
        else:
            return current_times

    def add_fixed_time(self, times):
        """添加固定时间点"""
        print("\n添加新固定时间点：")

        # 时间
        while True:
            time_str = input("  请输入拍照时间（格式：HH:MM）: ")
            try:
                hour, minute = map(int, time_str.split(':'))
                photo_time = dt_time(hour, minute)
                break
            except (ValueError, IndexError):
                print("  时间格式错误，请使用 HH:MM 格式")

        # 描述
        description = input("  请输入描述: ") or "定时拍照"

        times.append({
            "time": photo_time.strftime('%H:%M'),
            "description": description
        })

        print("固定时间点已添加")
        return times

    def modify_fixed_time(self, times):
        """修改固定时间点"""
        if not times:
            print("没有可修改的固定时间点")
            return times

        print(f"\n选择要修改的固定时间点：")
        for i, fixed_time in enumerate(times, 1):
            print(f"  {i}. {fixed_time['time']} - {fixed_time['description']}")

        try:
            index = int(input("请选择编号：")) - 1
            if 0 <= index < len(times):
                print(f"当前固定时间点：{times[index]['time']} - {times[index]['description']}")

                # 修改时间
                new_time = input(f"新的时间（当前：{times[index]['time']}，回车保持）: ").strip()
                if new_time:
                    try:
                        hour, minute = map(int, new_time.split(':'))
                        times[index]['time'] = dt_time(hour, minute).strftime('%H:%M')
                    except ValueError:
                        print("时间格式错误，保持原值")

                # 修改描述
                new_desc = input(f"新的描述（当前：{times[index]['description']}，回车保持）: ").strip()
                if new_desc:
                    times[index]['description'] = new_desc

                print("固定时间点已修改")
            else:
                print("编号无效")
        except ValueError:
            print("请输入有效的编号")

        return times

    def delete_fixed_time(self, times):
        """删除固定时间点"""
        if not times:
            print("没有可删除的固定时间点")
            return times

        print(f"\n选择要删除的固定时间点：")
        for i, fixed_time in enumerate(times, 1):
            print(f"  {i}. {fixed_time['time']} - {fixed_time['description']}")

        try:
            index = int(input("请选择编号：")) - 1
            if 0 <= index < len(times):
                deleted = times.pop(index)
                print(f"已删除固定时间点：{deleted['time']} - {deleted['description']}")
            else:
                print("编号无效")
        except ValueError:
            print("请输入有效的编号")

        return times

    def save_config(self, config):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            print(f"配置已保存到 {self.config_file}")
        except Exception as e:
            print(f"保存配置失败：{e}")

    def create_new_config(self):
        """创建新配置"""
        filename = input("请输入新配置文件名：").strip()
        if not filename:
            filename = "new_camera_config.json"

        if not filename.endswith('.json'):
            filename += '.json'

        # 创建新的配置管理器实例
        new_manager = ConfigManager()
        new_manager.config_file = filename

        # 使用默认配置
        config = copy.deepcopy(self.default_config)

        # 让用户选择是否立即编辑
        edit_now = input("是否立即编辑新配置？(y/n): ").strip().lower()
        if edit_now in ['y', 'yes', '是']:
            # 临时切换配置文件
            old_config_file = self.config_file
            self.config_file = filename
            self.edit_config()
            self.config_file = old_config_file
        else:
            new_manager.save_config(config)

        print(f"新配置文件已创建：{filename}")

    def import_config(self):
        """导入配置"""
        filename = input("请输入要导入的配置文件名：").strip()
        if not os.path.exists(filename):
            print("文件不存在")
            return

        try:
            with open(filename, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # 验证配置格式
            required_keys = ["camera_id", "temporary_dir", "permanent_dir", "time_ranges", "fixed_times"]
            for key in required_keys:
                if key not in config:
                    print(f"配置文件格式错误，缺少必要字段：{key}")
                    return

            # 复制到当前配置文件
            self.save_config(config)
            print("配置导入成功")
        except Exception as e:
            print(f"导入配置失败：{e}")

    def export_config(self):
        """导出配置"""
        if not os.path.exists(self.config_file):
            print("当前没有配置文件")
            return

        filename = input("请输入导出的配置文件名：").strip()
        if not filename:
            filename = "exported_camera_config.json"

        if not filename.endswith('.json'):
            filename += '.json'

        try:
            with open(self.config_file, 'r', encoding='utf-8') as src:
                config = json.load(src)

            with open(filename, 'w', encoding='utf-8') as dst:
                json.dump(config, dst, ensure_ascii=False, indent=2)

            print(f"配置已导出到：{filename}")
        except Exception as e:
            print(f"导出配置失败：{e}")

    def test_config(self):
        """测试配置"""
        print("\n正在测试配置...")

        # 测试摄像头
        capture_tool = CameraCapture(self.config_file)
        if capture_tool.initialize_camera():
            print("✓ 摄像头初始化成功")
            capture_tool.stop_capture()
        else:
            print("✗ 摄像头初始化失败")

        # 测试目录创建
        config = capture_tool.config
        try:
            os.makedirs(config["temporary_dir"], exist_ok=True)
            os.makedirs(config["permanent_dir"], exist_ok=True)
            print("✓ 目录创建成功")
        except Exception as e:
            print(f"✗ 目录创建失败：{e}")

        # 测试时间格式
        try:
            for time_range in config["time_ranges"]:
                dt_time.fromisoformat(time_range["start"])
                dt_time.fromisoformat(time_range["end"])
            for fixed_time in config["fixed_times"]:
                dt_time.fromisoformat(fixed_time["time"])
            print("✓ 时间格式验证通过")
        except Exception as e:
            print(f"✗ 时间格式验证失败：{e}")

        print("配置测试完成")

    def create_service(self):
        """创建系统服务"""
        capture_tool = CameraCapture(self.config_file)
        capture_tool.create_service_file()

    def run(self):
        """运行配置管理器"""
        while True:
            self.show_menu()
            choice = input("请选择（0-7）: ").strip()

            if choice == "0":
                print("退出配置管理")
                break
            elif choice == "1":
                self.show_current_config()
            elif choice == "2":
                self.edit_config()
            elif choice == "3":
                self.create_new_config()
            elif choice == "4":
                self.import_config()
            elif choice == "5":
                self.export_config()
            elif choice == "6":
                self.test_config()
            elif choice == "7":
                self.create_service()
            else:
                print("选择无效，请重新选择")

            input("\n按回车继续...")


if __name__ == "__main__":
    manager = ConfigManager()
    manager.run()