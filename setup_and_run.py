#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
摄像头抓拍工具 - 启动器（Web 看板版）

双击运行或在命令行执行本脚本即可启动 Web 看板：
  camera_capture.py 会在后台启动本地 Web 服务并自动打开浏览器。

首次使用可先安装依赖：
  python setup_and_run.py --install-deps
"""

import os
import sys
import subprocess


def here(*parts):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), *parts)


def install_deps():
    """安装 requirements.txt 中的依赖。"""
    req = here("requirements.txt")
    if not os.path.exists(req):
        print(f"找不到依赖清单：{req}")
        return False
    print("正在安装依赖（opencv-python / schedule / pillow / flask / pywin32 / winshell）…")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", req])
        print("✓ 依赖安装完成。")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ 依赖安装失败：{e}")
        return False


def launch():
    """在后台启动 Web 看板（camera_capture.py）。"""
    main_script = here("camera_capture.py")
    if not os.path.exists(main_script):
        print(f"✗ 找不到主程序：{main_script}")
        return

    # 无窗口方式启动主程序，使其作为后台服务运行
    creationflags = 0
    if sys.platform == "win32" and hasattr(subprocess, "CREATE_NO_WINDOW"):
        creationflags = subprocess.CREATE_NO_WINDOW

    print("正在启动 Web 看板…")
    subprocess.Popen(
        [sys.executable, main_script],
        cwd=here(),
        creationflags=creationflags,
    )
    print("✓ 已在后台启动，浏览器将自动打开 http://127.0.0.1:5000/")
    print("  （如未自动打开，请手动访问该地址；关闭请用网页上的「退出服务」按钮。）")


def main():
    if "--install-deps" in sys.argv:
        if not install_deps():
            input("\n按回车退出...")
            return

    launch()

    # 双击运行时让窗口停留一下，便于看到输出
    try:
        input("\n按回车关闭本窗口（Web 服务会在后台继续运行）...")
    except EOFError:
        pass


if __name__ == "__main__":
    main()
