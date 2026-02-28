#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
摄像头抓拍工具安装和配置脚本
"""

import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 7):
        messagebox.showerror("错误", "需要Python 3.7或更高版本")
        return False
    return True

def install_dependencies():
    """安装依赖包"""
    try:
        requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')

        # 使用pip安装依赖
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", requirements_path
        ])

        messagebox.showinfo("成功", "依赖包安装完成")
        return True
    except subprocess.CalledProcessError as e:
        messagebox.showerror("错误", f"安装依赖包失败：{e}")
        return False
    except Exception as e:
        messagebox.showerror("错误", f"读取requirements.txt失败：{e}")
        return False

def create_shortcut():
    """创建桌面快捷方式"""
    try:
        import winshell
        from win32com.client import Dispatch

        desktop = winshell.desktop()
        path = os.path.join(desktop, "摄像头抓拍工具.lnk")
        target = os.path.join(os.path.dirname(__file__), "camera_capture.py")
        wDir = os.path.dirname(__file__)
        icon = target

        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(path)
        shortcut.Targetpath = sys.executable
        shortcut.Arguments = f'"{target}" --gui'
        shortcut.WorkingDirectory = wDir
        shortcut.IconLocation = icon
        shortcut.save()

        messagebox.showinfo("成功", "桌面快捷方式已创建")
        return True
    except ImportError:
        messagebox.showwarning("警告", "创建快捷方式需要winshell和pywin32包")
        return False
    except Exception as e:
        messagebox.showerror("错误", f"创建快捷方式失败：{e}")
        return False

def main():
    """主函数"""
    if not check_python_version():
        return

    root = tk.Tk()
    root.title("摄像头抓拍工具 - 安装配置")
    root.geometry("500x400")
    root.resizable(False, False)

    # 标题
    title_label = tk.Label(root, text="摄像头抓拍工具", font=("Arial", 16, "bold"))
    title_label.pack(pady=10)

    desc_label = tk.Label(root, text="带开机启动和隐藏窗口功能的定时抓拍工具", font=("Arial", 10))
    desc_label.pack(pady=5)

    # 功能说明
    info_frame = ttk.LabelFrame(root, text="主要功能")
    info_frame.pack(fill='x', padx=20, pady=10)

    features = [
        "✓ 定时抓拍（支持时间段和固定时间点）",
        "✓ 开机自动启动（支持隐藏/可见模式）",
        "✓ 系统托盘图标和右键菜单",
        "✓ 图形化配置界面",
        "✓ 临时/永久照片分类存储",
        "✓ 自动清理过期文件"
    ]

    for feature in features:
        tk.Label(info_frame, text=feature, anchor='w').pack(anchor='w', padx=10, pady=2)

    # 操作按钮
    button_frame = ttk.Frame(root)
    button_frame.pack(pady=20)

    def run_config():
        """运行配置界面"""
        try:
            script_path = os.path.join(os.path.dirname(__file__), "camera_capture.py")
            subprocess.Popen([sys.executable, script_path, "--gui"])
        except Exception as e:
            messagebox.showerror("错误", f"启动配置界面失败：{e}")

    def run_hidden():
        """以隐藏模式运行"""
        try:
            script_path = os.path.join(os.path.dirname(__file__), "camera_capture.py")
            subprocess.Popen([sys.executable, script_path, "--hidden"])
            messagebox.showinfo("提示", "程序已在后台运行，请查看系统托盘")
        except Exception as e:
            messagebox.showerror("错误", f"启动隐藏模式失败：{e}")

    def open_folder():
        """打开程序文件夹"""
        folder_path = os.path.dirname(__file__)
        os.startfile(folder_path)

    def manage_startup():
        """管理开机启动设置"""
        try:
            # 导入CameraCapture类以使用其自启动方法
            sys.path.append(os.path.dirname(__file__))
            from camera_capture import CameraCapture

            capture_tool = CameraCapture()

            # 创建子窗口
            startup_window = tk.Toplevel(root)
            startup_window.title("开机启动设置")
            startup_window.geometry("400x250")
            startup_window.resizable(False, False)
            startup_window.transient(root)
            startup_window.grab_set()

            # 获取当前状态
            is_enabled = capture_tool.is_startup_enabled()

            # 状态显示
            status_frame = ttk.LabelFrame(startup_window, text="当前状态")
            status_frame.pack(fill='x', padx=20, pady=20)

            status_text = f"开机启动: {'已启用' if is_enabled else '已禁用'}"
            ttk.Label(status_frame, text=status_text, font=("Arial", 11)).pack(padx=10, pady=10)

            # 选项
            option_frame = ttk.LabelFrame(startup_window, text="启动选项")
            option_frame.pack(fill='x', padx=20, pady=10)

            hidden_var = tk.BooleanVar(value=True)
            ttk.Radiobutton(option_frame, text="隐藏模式启动（推荐）", variable=hidden_var, value=True).pack(anchor='w', padx=10, pady=5)
            ttk.Radiobutton(option_frame, text="显示窗口启动", variable=hidden_var, value=False).pack(anchor='w', padx=10, pady=5)

            # 按钮
            button_frame = ttk.Frame(startup_window)
            button_frame.pack(pady=20)

            def apply_startup():
                """应用启动设置"""
                if is_enabled:
                    # 禁用启动
                    if capture_tool.disable_startup():
                        messagebox.showinfo("成功", "开机启动已禁用")
                        startup_window.destroy()
                    else:
                        messagebox.showerror("错误", "禁用开机启动失败")
                else:
                    # 启用启动
                    if capture_tool.enable_startup(hidden=hidden_var.get()):
                        mode_text = "隐藏模式" if hidden_var.get() else "可见模式"
                        messagebox.showinfo("成功", f"开机启动已启用（{mode_text}）")
                        startup_window.destroy()
                    else:
                        messagebox.showerror("错误", "启用开机启动失败")

            ttk.Button(button_frame, text="应用设置", command=apply_startup, width=15).pack(side='left', padx=5)
            ttk.Button(button_frame, text="取消", command=startup_window.destroy, width=15).pack(side='left', padx=5)

        except ImportError:
            messagebox.showerror("错误", "无法导入camera_capture模块")
        except Exception as e:
            messagebox.showerror("错误", f"管理开机启动失败：{e}")

    ttk.Button(button_frame, text="安装依赖包", command=install_dependencies).pack(side='left', padx=5)
    ttk.Button(button_frame, text="创建桌面快捷方式", command=create_shortcut).pack(side='left', padx=5)
    ttk.Button(button_frame, text="开机启动设置", command=manage_startup).pack(side='left', padx=5)
    ttk.Button(button_frame, text="打开程序文件夹", command=open_folder).pack(side='left', padx=5)

    # 运行按钮
    run_frame = ttk.Frame(root)
    run_frame.pack(pady=10)

    ttk.Button(run_frame, text="显示配置窗口", command=run_config, width=20).pack(side='left', padx=5)
    ttk.Button(run_frame, text="隐藏模式运行", command=run_hidden, width=20).pack(side='left', padx=5)

    # 使用说明
    help_frame = ttk.LabelFrame(root, text="使用说明")
    help_frame.pack(fill='x', padx=20, pady=10)

    help_text = """
1. 首次使用请点击"安装依赖包"
2. 点击"显示配置窗口"进行参数设置
3. 可选择创建桌面快捷方式方便使用
4. 配置开机启动：在配置窗口的"启动设置"选项卡中设置
5. 隐藏模式运行：程序将最小化到系统托盘
6. 右键托盘图标可进行各种操作
    """

    tk.Label(help_frame, text=help_text.strip(), justify='left').pack(padx=10, pady=5)

    # 退出按钮
    ttk.Button(root, text="退出", command=root.destroy, width=20).pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    main()