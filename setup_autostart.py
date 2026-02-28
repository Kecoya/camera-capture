"""
Windows 自启动配置脚本
将摄像头抓拍工具设置为开机自启动
"""
import os
import sys
import win32com.client
from pathlib import Path

def setup_autostart():
    """设置开机自启动"""
    try:
        # 获取当前脚本路径
        script_dir = Path(__file__).parent.absolute()
        launcher_script = script_dir / "silent_launcher.py"
        python_exe = sys.executable

        # 优先使用 pythonw.exe（无窗口版本）
        pythonw_exe = python_exe.replace("python.exe", "pythonw.exe")
        if not os.path.exists(pythonw_exe):
            pythonw_exe = python_exe  # 如果没有pythonw.exe，使用python.exe

        # 创建启动快捷方式
        startup_folder = Path(os.path.expanduser(
            "~\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup"
        ))

        shortcut_path = startup_folder / "CameraCapture.lnk"

        # 使用win32com创建快捷方式
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(str(shortcut_path))

        # 设置快捷方式属性
        shortcut.TargetPath = pythonw_exe
        shortcut.Arguments = f'"{launcher_script}"'
        shortcut.WorkingDirectory = str(script_dir)
        shortcut.Description = "摄像头抓拍工具"
        shortcut.IconLocation = pythonw_exe
        # 隐藏命令行窗口 (window style 0 = hidden)
        shortcut.WindowStyle = 0

        # 保存快捷方式
        shortcut.save()

        print(f"✅ 成功设置开机自启动！")
        print(f"   快捷方式位置: {shortcut_path}")
        print(f"   启动器: {launcher_script}")
        print(f"   Python解释器: {pythonw_exe}")
        print(f"\n🔕 程序将在下次开机时静默启动（无窗口）")

        return True

    except Exception as e:
        print(f"❌ 设置自启动失败: {e}")
        print(f"\n请确保：")
        print(f"1. 以管理员身份运行此脚本")
        print(f"2. 已安装 pywin32 库 (pip install pywin32)")
        return False


def remove_autostart():
    """移除开机自启动"""
    try:
        startup_folder = Path(os.path.expanduser(
            "~\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup"
        ))

        shortcut_path = startup_folder / "CameraCapture.lnk"

        if shortcut_path.exists():
            os.remove(shortcut_path)
            print(f"✅ 已移除开机自启动！")
            return True
        else:
            print(f"ℹ️ 未找到自启动配置")
            return False

    except Exception as e:
        print(f"❌ 移除自启动失败: {e}")
        return False


def check_autostart():
    """检查自启动状态"""
    startup_folder = Path(os.path.expanduser(
        "~\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup"
    ))

    shortcut_path = startup_folder / "CameraCapture.lnk"

    if shortcut_path.exists():
        print(f"✅ 已配置开机自启动")
        print(f"   快捷方式位置: {shortcut_path}")
        return True
    else:
        print(f"❌ 未配置开机自启动")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("摄像头抓拍工具 - 自启动配置")
    print("=" * 60)
    print()

    print("请选择操作：")
    print("1. 设置开机自启动")
    print("2. 移除开机自启动")
    print("3. 检查自启动状态")
    print("4. 退出")
    print()

    choice = input("请输入选项 (1-4): ").strip()

    if choice == '1':
        print("\n正在设置开机自启动...")
        setup_autostart()
    elif choice == '2':
        print("\n正在移除开机自启动...")
        remove_autostart()
    elif choice == '3':
        print("\n检查自启动状态...")
        check_autostart()
    elif choice == '4':
        print("退出")
        return
    else:
        print("无效的选项")

    print()
    input("按 Enter 键退出...")


if __name__ == '__main__':
    main()
