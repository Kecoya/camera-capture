#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web 看板 - Flask 应用
为摄像头抓拍工具提供 Web 界面：实时预览 / 配置 / 控制 / 图片画廊 / GIF / 启动设置。

线程模型：
- Flask 主线程跑 app.run(threaded=True, use_reloader=False)。
- 抓拍引擎（start_all_capture，阻塞循环）跑在 daemon 线程里。
- 单摄像头、单 camera_lock：MJPEG 预览 / 手动抓拍 / 抓拍 worker 全部经锁串行。
"""

import os
import sys
import copy
import time
import glob
import shutil
import threading
from datetime import datetime

import cv2
import numpy as np
from flask import (Flask, Response, request, jsonify, render_template,
                   send_from_directory)

app = Flask(__name__)

# 由 run_app() 注入的抓拍引擎实例
CAPTURE = None

THUMB_MAX_WIDTH = 240      # 缩略图最大宽度
PREVIEW_FPS = 10           # MJPEG 预览帧率上限（节流 CPU 与锁竞争）


# ---------------------------------------------------------------------------
# 抓拍线程编排
# ---------------------------------------------------------------------------

def _start_capture_thread():
    """在 daemon 线程中启动抓拍（start_all_capture 是阻塞循环，不能在请求/主线程里直接调用）。"""
    if CAPTURE is None or CAPTURE.is_running:
        return
    threading.Thread(target=_safe_start_capture, daemon=True).start()


def _safe_start_capture():
    try:
        CAPTURE.start_all_capture()
    except Exception as e:
        print(f"[Web] 启动抓拍失败：{e}")


# ---------------------------------------------------------------------------
# 服务启动入口
# ---------------------------------------------------------------------------

def run_app(capture, host="127.0.0.1", port=5000, open_browser=True):
    """启动 Flask Web 看板。

    Args:
        capture: CameraCapture 实例
        host: 绑定地址（默认 127.0.0.1，仅本机访问）
        port: 端口（默认 5000）
        open_browser: 是否自动打开浏览器
    """
    global CAPTURE
    CAPTURE = capture

    # 沿用旧行为：服务启动即开始抓拍（失败仅记日志，不影响 Web 服务）
    _start_capture_thread()

    if open_browser:
        url = f"http://{host}:{port}/"
        threading.Thread(target=_delayed_open_browser, args=(url,), daemon=True).start()

    print(f"Web 看板已启动：http://{host}:{port}/  （在终端按 Ctrl+C 退出）")
    try:
        # use_reloader=False：避免子进程重复打开摄像头
        # threaded=True：MJPEG 长连接不阻塞其它请求
        app.run(host=host, port=port, threaded=True, debug=False, use_reloader=False)
    except OSError as e:
        print(f"启动 Web 服务失败（端口 {port} 可能被占用）：{e}")
        print("请使用 --port 指定其他端口后重试。")


def _delayed_open_browser(url, delay=1.5):
    """延迟打开浏览器，等服务起来。"""
    time.sleep(delay)
    try:
        import webbrowser
        webbrowser.open(url)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# 目录与路径校验
# ---------------------------------------------------------------------------

def _dir_for_type(type_name):
    """根据类型返回对应目录的绝对路径。"""
    if type_name == "permanent":
        return os.path.abspath(CAPTURE.config["permanent_dir"])
    return os.path.abspath(CAPTURE.config["temporary_dir"])


def _safe_resolve(base_dir, name):
    """拼接并校验路径，防止路径穿越。返回绝对路径或 None。"""
    if not name or "/" in name or "\\" in name or ".." in name:
        return None
    base_real = os.path.realpath(base_dir)
    full = os.path.realpath(os.path.join(base_real, name))
    try:
        if os.path.commonpath([base_real, full]) != base_real:
            return None
    except ValueError:
        return None
    return full if os.path.isfile(full) else None


_IMAGE_EXTS = (".jpg", ".jpeg", ".png")


def _is_image_name(name):
    """仅允许常见图片扩展名，避免在抓拍目录里被投毒的 .svg 等被当作图片服务。"""
    return name.lower().endswith(_IMAGE_EXTS)


def _list_dir(dir_path, pattern="*.jpg"):
    """列出目录下匹配文件，返回 [(abs_path, mtime, size), ...]，按 mtime 倒序。"""
    items = []
    for fp in glob.glob(os.path.join(dir_path, pattern)):
        try:
            st = os.stat(fp)
            items.append((fp, st.st_mtime, st.st_size))
        except OSError:
            continue
    items.sort(key=lambda x: x[1], reverse=True)
    return items


def _count(dir_path, pattern):
    return len(glob.glob(os.path.join(dir_path, pattern)))


def _dir_stats(dir_path, pattern="*.jpg"):
    """单次遍历返回 (数量, 最新 mtime 或 None)，避免状态接口做全量排序。"""
    count = 0
    newest = None
    for fp in glob.glob(os.path.join(dir_path, pattern)):
        try:
            mtime = os.path.getmtime(fp)
        except OSError:
            continue
        count += 1
        if newest is None or mtime > newest:
            newest = mtime
    return count, newest


def _fmt_mtime(ts):
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


# ---------------------------------------------------------------------------
# 配置校验工具（web_app 不依赖 camera_capture，避免循环导入）
# ---------------------------------------------------------------------------

def _parse_hhmm(value):
    """校验 HH:MM，返回 (hour, minute)；非法抛 ValueError。"""
    parts = str(value).strip().split(":")
    if len(parts) != 2:
        raise ValueError("时间格式应为 HH:MM")
    hour, minute = int(parts[0]), int(parts[1])
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError("时间超出范围（小时 0-23，分钟 0-59）")
    return hour, minute


def _require_int(value, lo, hi, label):
    v = int(value)
    if not (lo <= v <= hi):
        raise ValueError(f"{label} 需在 {lo}-{hi} 之间")
    return v


def _require_float(value, lo, hi, label):
    v = float(value)
    if not (lo <= v <= hi):
        raise ValueError(f"{label} 需在 {lo}-{hi} 之间")
    return v


# ---------------------------------------------------------------------------
# 页面
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


# ---------------------------------------------------------------------------
# 状态 / 配置 / 控制
# ---------------------------------------------------------------------------

@app.route("/api/status")
def api_status():
    in_range, time_range = False, None
    try:
        in_range, time_range = CAPTURE.is_within_time_ranges()
    except Exception:
        pass

    temp_dir = os.path.abspath(CAPTURE.config["temporary_dir"])
    perm_dir = os.path.abspath(CAPTURE.config["permanent_dir"])
    gif_dir = os.path.abspath(CAPTURE.config["gif_dir"])

    temp_count, temp_newest = _dir_stats(temp_dir)
    perm_count, perm_newest = _dir_stats(perm_dir)
    last = max(filter(lambda x: x is not None, (temp_newest, perm_newest)), default=None)

    disk = None
    try:
        du = shutil.disk_usage(perm_dir)
        disk = {"total": du.total, "used": du.used, "free": du.free}
    except Exception:
        pass

    startup_enabled = False
    try:
        startup_enabled = CAPTURE.is_startup_enabled()
    except Exception:
        pass

    return jsonify({
        "is_running": CAPTURE.is_running,
        "camera_id": CAPTURE.config.get("camera_id", 0),
        "in_range": in_range,
        "current_range": time_range,
        "counts": {
            "temp": temp_count,
            "permanent": perm_count,
            "gif": _count(gif_dir, "*.gif"),
        },
        "last_capture": _fmt_mtime(last) if last else None,
        "disk": disk,
        "startup_enabled": startup_enabled,
        "config_file": os.path.abspath(CAPTURE.config_file),
    })


@app.route("/api/config", methods=["GET"])
def api_config_get():
    return jsonify(CAPTURE.config)


@app.route("/api/config", methods=["POST"])
def api_config_post():
    data = request.get_json(silent=True) or {}
    # 在副本上修改：全部校验通过、目录可创建、文件可写后，才原子替换 live 配置，避免半截写入
    cfg = copy.deepcopy(CAPTURE.config)

    try:
        if "camera_id" in data:
            cfg["camera_id"] = _require_int(data["camera_id"], 0, 20, "摄像头ID")
        for key in ("temporary_dir", "permanent_dir", "gif_dir"):
            if key in data:
                val = str(data[key]).strip()
                if not val:
                    raise ValueError(f"{key} 不能为空")
                cfg[key] = val
        if "max_temp_captures" in data:
            cfg["max_temp_captures"] = _require_int(data["max_temp_captures"], 1, 100000, "最大临时照片数")
        if "auto_cleanup" in data:
            cfg["auto_cleanup"] = bool(data["auto_cleanup"])
        if "cleanup_days" in data:
            cfg["cleanup_days"] = _require_int(data["cleanup_days"], 1, 36500, "清理天数")
        if "gif_fps" in data:
            cfg["gif_fps"] = _require_int(data["gif_fps"], 1, 60, "GIF帧率")
        if "gif_duration" in data:
            cfg["gif_duration"] = _require_float(data["gif_duration"], 0.1, 60.0, "GIF时长")
        if "enable_timestamp" in data:
            cfg["enable_timestamp"] = bool(data["enable_timestamp"])
        if "timestamp_scale" in data:
            cfg["timestamp_scale"] = _require_float(data["timestamp_scale"], 0.1, 10.0, "时间戳大小")
        if "timestamp_thickness" in data:
            cfg["timestamp_thickness"] = _require_int(data["timestamp_thickness"], 1, 20, "时间戳粗细")
        if "timestamp_color" in data:
            color = data["timestamp_color"]
            if not (isinstance(color, (list, tuple)) and len(color) == 3):
                raise ValueError("时间戳颜色需为 3 个整数(BGR)")
            cfg["timestamp_color"] = [int(c) for c in color]
    except (ValueError, TypeError) as e:
        return jsonify({"ok": False, "error": f"字段错误：{e}"}), 400

    # 时间段
    if "time_ranges" in data:
        if not isinstance(data["time_ranges"], list):
            return jsonify({"ok": False, "error": "time_ranges 必须是数组"}), 400
        ranges = []
        for r in data["time_ranges"]:
            try:
                sh, sm = _parse_hhmm(r["start"])
                eh, em = _parse_hhmm(r["end"])
                interval = _require_int(r["interval"], 1, 86400, "间隔")
            except (ValueError, TypeError, KeyError) as e:
                return jsonify({"ok": False, "error": f"时间段格式错误：{e}"}), 400
            ranges.append({"start": f"{sh:02d}:{sm:02d}", "end": f"{eh:02d}:{em:02d}", "interval": interval})
        cfg["time_ranges"] = ranges

    # 固定时间点
    if "fixed_times" in data:
        if not isinstance(data["fixed_times"], list):
            return jsonify({"ok": False, "error": "fixed_times 必须是数组"}), 400
        fts = []
        for f in data["fixed_times"]:
            try:
                hh, mm = _parse_hhmm(f["time"])
            except (ValueError, TypeError, KeyError) as e:
                return jsonify({"ok": False, "error": f"固定时间格式错误：{e}"}), 400
            fts.append({"time": f"{hh:02d}:{mm:02d}", "description": str(f.get("description", "定时拍照"))})
        cfg["fixed_times"] = fts

    # 先建目录、再写文件；全部成功后才原子替换 live 配置
    try:
        for key in ("temporary_dir", "permanent_dir", "gif_dir"):
            os.makedirs(cfg[key], exist_ok=True)
        if not CAPTURE.save_config(cfg):
            return jsonify({"ok": False, "error": "写入配置文件失败"}), 500
    except Exception as e:
        return jsonify({"ok": False, "error": f"保存失败：{e}"}), 500

    CAPTURE.config = cfg

    # 若抓拍正在运行，重启使新调度生效
    was_running = CAPTURE.is_running
    if was_running:
        try:
            CAPTURE.stop_capture()
        except Exception:
            pass
        _start_capture_thread()

    return jsonify({"ok": True, "restarted": was_running})


@app.route("/api/capture/start", methods=["POST"])
def api_capture_start():
    _start_capture_thread()
    return jsonify({"ok": True, "is_running": CAPTURE.is_running})


@app.route("/api/capture/stop", methods=["POST"])
def api_capture_stop():
    try:
        CAPTURE.stop_capture()
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
    return jsonify({"ok": True, "is_running": CAPTURE.is_running})


@app.route("/api/capture/manual", methods=["POST"])
def api_capture_manual():
    """立即抓拍一张临时照片（会写盘，故仅限 POST，避免 GET 误触发）。

    capture_image() 返回原始帧；save_image() 内部会调用 add_timestamp，
    所以这里不重复加时间戳。释放条件：抓拍引擎未运行时才释放——引擎运行
    时由主循环按调度统一管理释放，避免与正在抓拍的 worker 抢占设备。
    """
    try:
        if not CAPTURE.initialize_camera():
            return jsonify({"ok": False, "error": "摄像头初始化失败"}), 500

        frame = CAPTURE.capture_image()
        path = CAPTURE.save_image(frame, is_permanent=False) if frame is not None else None

        if not CAPTURE.is_running:
            CAPTURE.release_camera()

        if path:
            return jsonify({"ok": True, "path": os.path.basename(path)})
        return jsonify({"ok": False, "error": "抓拍失败（无画面或保存失败）"}), 500
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ---------------------------------------------------------------------------
# 实时预览 MJPEG
# ---------------------------------------------------------------------------

def _camera_ready():
    return CAPTURE.camera is not None and CAPTURE.camera.isOpened()


def _placeholder_frame(text):
    """生成一张带提示文字的占位 JPEG（摄像头不可用时用，避免浏览器 <img> 永久挂起）。"""
    img = np.zeros((240, 480, 3), dtype=np.uint8)
    cv2.putText(img, text, (40, 120), cv2.FONT_HERSHEY_SIMPLEX, 1.0,
                (200, 200, 200), 2, cv2.LINE_AA)
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 70])
    return buf.tobytes() if ok else b""


def gen_mjpeg():
    """MJPEG 帧生成器。

    死锁规避铁律：initialize_camera() / capture_image() 内部都会取 camera_lock，
    所以生成器【绝不在持有锁时】调用它们；只在【持锁状态】做 camera.read()。
    """
    initialized_here = False
    last = 0.0
    frame_interval = 1.0 / PREVIEW_FPS
    try:
        while True:
            now = time.time()
            if now - last < frame_interval:
                time.sleep(0.02)
                continue

            # 初始化摄像头（不在持锁状态调用，initialize_camera 内部会取锁）
            if not _camera_ready():
                if not CAPTURE.initialize_camera():
                    # 摄像头不可用：输出占位帧，避免浏览器 <img> 永久挂起
                    jpg = _placeholder_frame("Camera unavailable")
                    last = time.time()
                    if jpg:
                        yield (b"--frame\r\n"
                               b"Content-Type: image/jpeg\r\n\r\n" + jpg + b"\r\n")
                    time.sleep(1)
                    continue
                initialized_here = True

            # 读帧——必须持锁，与抓拍 worker 串行
            frame = None
            with CAPTURE.camera_lock:
                if _camera_ready():
                    ok, f = CAPTURE.camera.read()
                    if ok:
                        frame = f
            last = time.time()
            if frame is None:
                time.sleep(0.05)
                continue

            # 预览叠加时间戳（add_timestamp 在禁用时会原样返回）
            try:
                frame = CAPTURE.add_timestamp(frame)
            except Exception:
                pass

            ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            if not ok:
                continue

            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n" + buf.tobytes() + b"\r\n")
    except GeneratorExit:
        pass
    finally:
        # 只释放「自己开、且当前没有抓拍 worker 在用」的摄像头
        if initialized_here and not CAPTURE.is_running:
            try:
                CAPTURE.release_camera()
            except Exception:
                pass


@app.route("/video_feed")
def video_feed():
    return Response(gen_mjpeg(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")


# ---------------------------------------------------------------------------
# 图片画廊 / 缩略图 / 下载 / 删除
# ---------------------------------------------------------------------------

@app.route("/api/images")
def api_images():
    type_name = request.args.get("type", "temp")
    if type_name not in ("temp", "permanent"):
        return jsonify({"ok": False, "error": "type 非法"}), 400
    page = max(1, request.args.get("page", default=1, type=int))
    size = max(1, min(200, request.args.get("size", default=24, type=int)))

    dir_path = _dir_for_type(type_name)
    items = _list_dir(dir_path, "*.jpg")
    total = len(items)
    start = (page - 1) * size
    page_items = items[start:start + size]

    result = [{
        "name": os.path.basename(fp),
        "mtime": _fmt_mtime(mtime),
        "size": fsize,
        "thumbnail": f"/api/thumbnail/{type_name}/{os.path.basename(fp)}",
        "full": f"/image/{type_name}/{os.path.basename(fp)}",
    } for fp, mtime, fsize in page_items]

    return jsonify({
        "items": result,
        "total": total,
        "page": page,
        "size": size,
        "total_pages": (total + size - 1) // size,
    })


@app.route("/api/thumbnail/<type_name>/<name>")
def api_thumbnail(type_name, name):
    if type_name not in ("temp", "permanent") or not _is_image_name(name):
        return "bad request", 400
    dir_path = _dir_for_type(type_name)
    full = _safe_resolve(dir_path, name)
    if not full:
        return "not found", 404
    img = cv2.imread(full)
    if img is None:
        return "decode failed", 500
    h, w = img.shape[:2]
    if w > THUMB_MAX_WIDTH:
        new_w = THUMB_MAX_WIDTH
        new_h = max(1, int(h * THUMB_MAX_WIDTH / w))
        img = cv2.resize(img, (new_w, new_h))
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 80])
    if not ok:
        return "encode failed", 500
    resp = Response(buf.tobytes(), mimetype="image/jpeg")
    resp.headers["Cache-Control"] = "public, max-age=3600"
    return resp


@app.route("/image/<type_name>/<name>")
def image_full(type_name, name):
    if type_name not in ("temp", "permanent") or not _is_image_name(name):
        return "bad request", 400
    dir_path = _dir_for_type(type_name)
    full = _safe_resolve(dir_path, name)
    if not full:
        return "not found", 404
    return send_from_directory(dir_path, name)


@app.route("/api/gifs")
def api_gifs():
    gif_dir = os.path.abspath(CAPTURE.config["gif_dir"])
    items = _list_dir(gif_dir, "*.gif")
    result = [{
        "name": os.path.basename(fp),
        "mtime": _fmt_mtime(mtime),
        "size": fsize,
        "preview": f"/gif/{os.path.basename(fp)}",
    } for fp, mtime, fsize in items]
    return jsonify({"items": result, "total": len(result)})


@app.route("/gif/<name>")
def gif_file(name):
    gif_dir = os.path.abspath(CAPTURE.config["gif_dir"])
    full = _safe_resolve(gif_dir, name)
    if not full:
        return "not found", 404
    return send_from_directory(gif_dir, name, mimetype="image/gif")


@app.route("/api/image/delete", methods=["POST"])
def api_image_delete():
    data = request.get_json(silent=True) or {}
    type_name = data.get("type")
    name = data.get("name")
    if type_name == "gif":
        dir_path = os.path.abspath(CAPTURE.config["gif_dir"])
    elif type_name in ("temp", "permanent"):
        dir_path = _dir_for_type(type_name)
    else:
        return jsonify({"ok": False, "error": "type 非法"}), 400
    full = _safe_resolve(dir_path, name)
    if not full:
        return jsonify({"ok": False, "error": "文件不存在"}), 404
    try:
        os.remove(full)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
    return jsonify({"ok": True})


# ---------------------------------------------------------------------------
# 开机启动 / 桌面快捷方式 / 退出
# ---------------------------------------------------------------------------

@app.route("/api/startup")
def api_startup_get():
    try:
        return jsonify({"enabled": CAPTURE.is_startup_enabled()})
    except Exception as e:
        return jsonify({"enabled": False, "error": str(e)})


@app.route("/api/startup", methods=["POST"])
def api_startup_post():
    data = request.get_json(silent=True) or {}
    enable = bool(data.get("enable", False))
    try:
        ok = CAPTURE.enable_startup(hidden=True) if enable else CAPTURE.disable_startup()
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
    enabled_now = enable
    try:
        enabled_now = CAPTURE.is_startup_enabled()
    except Exception:
        pass
    return jsonify({"ok": ok, "enabled": enabled_now})


@app.route("/api/desktop-shortcut", methods=["POST"])
def api_desktop_shortcut():
    """创建桌面快捷方式（指向 Web 看板）。仅 Windows。"""
    import platform as _pf
    if _pf.system().lower() != "windows":
        return jsonify({"ok": False, "error": "仅支持 Windows"}), 400
    try:
        import winshell
        from win32com.client import Dispatch
    except ImportError:
        return jsonify({"ok": False, "error": "需要 winshell 和 pywin32"}), 500

    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        target = os.path.join(script_dir, "camera_capture.py")
        desktop = winshell.desktop()
        path = os.path.join(desktop, "摄像头抓拍工具.lnk")
        shell = Dispatch("WScript.Shell")
        sc = shell.CreateShortCut(path)
        sc.Targetpath = sys.executable
        sc.Arguments = f'"{target}"'
        sc.WorkingDirectory = script_dir
        sc.IconLocation = target
        sc.save()
        return jsonify({"ok": True, "path": path})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/shutdown", methods=["POST"])
def api_shutdown():
    """停止抓拍并退出 Web 服务。"""
    try:
        CAPTURE.stop_capture()
    except Exception:
        pass
    # 在请求上下文内取出关闭钩子，再交给后台线程执行
    shutdown_func = None
    try:
        shutdown_func = request.environ.get("werkzeug.server.shutdown")
    except Exception:
        pass

    def _quit():
        time.sleep(0.2)
        if shutdown_func is not None:
            try:
                shutdown_func()
                return
            except Exception:
                pass
        os._exit(0)

    threading.Thread(target=_quit, daemon=True).start()
    return jsonify({"ok": True})
