import cv2
import numpy as np
import subprocess
import time
import math
import re
import os
import json
import mss
import pygetwindow as gw
import tkinter as tk
from tkinter import messagebox, ttk

# cd C:\platform-tools
# adb connect 127.0.0.1:5555
# adb devices

# =========================
# ADB / 視窗設定（可由 GUI 輸入）
# =========================
ADB_PATH = r"C:\platform-tools\adb.exe"
ADB_SERIAL = "127.0.0.1:5555"
WINDOW_TITLE_KEYWORD = "BlueStacks App Player"
CONFIG_FILE = "bot_config.json"
# =========================
# BlueStacks 視窗設定
# =========================
# 先抓整個視窗，再裁掉不需要的部分
CONTENT_CROP_LEFT = 0
CONTENT_CROP_TOP = 33
CONTENT_CROP_RIGHT = 34
CONTENT_CROP_BOTTOM = 0

# 再切出真正 Android 顯示區
DEVICE_VIEW_LEFT = 0
DEVICE_VIEW_TOP = 0
DEVICE_VIEW_RIGHT = 0
DEVICE_VIEW_BOTTOM = 0

# =========================
# 模式
# preview = 練習模式（只初始化、顯示配對，不攻擊）
# run     = 實戰模式（初始化後固定輪流拖曳，不再截圖）
# =========================
MODE = "run"
VERBOSE = False

# =========================
# 3x5 區域比例
# 必須基於 capture_bluestacks_screen() 最終回傳的 img
# =========================
BOARD_X_RATIO = 0.212037
BOARD_Y_RATIO = 0.503646
BOARD_W_RATIO = 0.575926
BOARD_H_RATIO = 0.187500

# 練習模式盤面比例
PRACTICE_BOARD_X_RATIO = 0.212037
PRACTICE_BOARD_Y_RATIO = 0.553646
PRACTICE_BOARD_W_RATIO = 0.578704
PRACTICE_BOARD_H_RATIO = 0.187500

# 實戰模式盤面比例
LIVE_BOARD_X_RATIO = 0.212037
LIVE_BOARD_Y_RATIO = 0.503646
LIVE_BOARD_W_RATIO = 0.575926
LIVE_BOARD_H_RATIO = 0.187500

# =========================
# 顏色標準（OpenCV 用 BGR）
# =========================
RED_BGR = (111, 23, 199)
BLUE_BGR = (122, 100, 0)

# =========================
# 斷線重連偵測（只在初始化時檢查）
# =========================
RECONNECT_X_RATIO = 0.569767
RECONNECT_Y_RATIO = 0.621212
RECONNECT_BGR = (12, 179, 247)
RECONNECT_COLOR_THRESHOLD = 900
RECONNECT_CLICK_DELAY = 0.0
RECONNECT_MAX_RETRY = 20

# =========================
# 顏色距離門檻
# =========================
NONE_THRESHOLD_SQUARED = 4200

# =========================
# 盤面規格
# =========================
ROWS = 3
COLS = 5

# =========================
# 初始化黑名單功能
# =========================
INIT_SCAN_COUNT = 5
INIT_SCAN_INTERVAL_SEC = 0.08
INIT_VALID_THRESHOLD = 0.25

invalid_cells = set()
invalid_cells_locked = False

# =========================
# 多次掃描投票（初始化）
# =========================
VOTE_SCAN_COUNT = 5
VOTE_SCAN_INTERVAL_SEC = 0.03

# =========================
# 固定配對設定
# =========================
FIXED_RED_COUNT = 6
FIXED_BLUE_COUNT = 6

# 每幾秒做一次拖曳
PAIR_ATTACK_INTERVAL_SEC = 0.5

# 單次拖曳時間
SWIPE_DURATION_MS = 1

# =========================
# 顯示設定
# =========================
SHOW_DEBUG_WINDOW = False
SAVE_DEBUG_IMAGE_EACH_LOOP = False

# 最近一次操作的可視化資訊
last_action_debug = None

# =========================
# 快取
# =========================
board_cell_cache = None
board_cell_cache_shape = None

# =========================
# 初始化後的固定盤面 / 固定配對
# =========================
initial_board_cells = None
fixed_reds = []
fixed_blues = []
fixed_pairs = []

# pair 結構：
# {
#   "id": 0,
#   "blue": {...},
#   "red": {...},
#   "distance": xxx
# }

# =========================
# ADB 螢幕大小
# =========================
ADB_SCREEN_W = None
ADB_SCREEN_H = None


def show_startup_config_ui():
    global ADB_PATH, ADB_SERIAL, WINDOW_TITLE_KEYWORD, MODE

    load_saved_config()

    result = {
        "confirmed": False,
        "adb_path": ADB_PATH,
        "adb_serial": ADB_SERIAL,
        "window_title_keyword": WINDOW_TITLE_KEYWORD,
        "mode": MODE
    }

    root = tk.Tk()
    root.title("Bot 啟動設定")
    root.geometry("560x340")
    root.resizable(False, False)

    try:
        root.eval("tk::PlaceWindow . center")
    except Exception:
        pass

    title_label = tk.Label(
        root,
        text="請輸入啟動設定",
        font=("Microsoft JhengHei UI", 14, "bold")
    )
    title_label.pack(pady=(15, 10))

    frame = tk.Frame(root, padx=20, pady=10)
    frame.pack(fill="both", expand=True)

    tk.Label(frame, text="WINDOW_TITLE_KEYWORD", anchor="w", width=22).grid(row=0, column=0, sticky="w", pady=6)
    entry_window_title = tk.Entry(frame, width=45)
    entry_window_title.grid(row=0, column=1, pady=6, sticky="w")
    entry_window_title.insert(0, WINDOW_TITLE_KEYWORD)

    tk.Label(frame, text="ADB_SERIAL", anchor="w", width=22).grid(row=1, column=0, sticky="w", pady=6)
    entry_adb_serial = tk.Entry(frame, width=45)
    entry_adb_serial.grid(row=1, column=1, pady=6, sticky="w")
    entry_adb_serial.insert(0, ADB_SERIAL)

    tk.Label(frame, text="ADB_PATH", anchor="w", width=22).grid(row=2, column=0, sticky="w", pady=6)
    entry_adb_path = tk.Entry(frame, width=45)
    entry_adb_path.grid(row=2, column=1, pady=6, sticky="w")
    entry_adb_path.insert(0, ADB_PATH)

    tk.Label(frame, text="模式", anchor="w", width=22).grid(row=3, column=0, sticky="w", pady=6)
    combo_mode = ttk.Combobox(frame, width=42, state="readonly")
    combo_mode["values"] = ("preview", "run")
    combo_mode.grid(row=3, column=1, pady=6, sticky="w")
    combo_mode.set(MODE)

    mode_hint = tk.Label(
        frame,
        text="preview = 練習模式 / run = 實戰模式",
        anchor="w",
        fg="gray"
    )
    mode_hint.grid(row=4, column=1, sticky="w", pady=(0, 6))

    status_label = tk.Label(
        root,
        text="",
        fg="green",
        font=("Microsoft JhengHei UI", 9)
    )
    status_label.pack(pady=(0, 5))

    button_frame = tk.Frame(root)
    button_frame.pack(pady=(5, 15))

    def get_current_values():
        window_title = entry_window_title.get().strip()
        adb_serial = entry_adb_serial.get().strip()
        adb_path = entry_adb_path.get().strip()
        mode_value = combo_mode.get().strip()
        return window_title, adb_serial, adb_path, mode_value

    def validate_values(window_title, adb_serial, adb_path, mode_value):
        if not window_title:
            messagebox.showerror("錯誤", "WINDOW_TITLE_KEYWORD 不能為空")
            return False

        if not adb_serial:
            messagebox.showerror("錯誤", "ADB_SERIAL 不能為空")
            return False

        if not adb_path:
            messagebox.showerror("錯誤", "ADB_PATH 不能為空")
            return False

        if mode_value not in ("preview", "run"):
            messagebox.showerror("錯誤", "模式只能是 preview 或 run")
            return False

        return True

    def on_apply():
        window_title, adb_serial, adb_path, mode_value = get_current_values()

        if not validate_values(window_title, adb_serial, adb_path, mode_value):
            return

        ok = save_current_config(window_title, adb_serial, adb_path, mode_value)
        if ok:
            status_label.config(text="已套用並儲存設定")
            messagebox.showinfo("成功", "設定已儲存，下次啟動會自動套用。")
        else:
            status_label.config(text="儲存失敗", fg="red")
            messagebox.showerror("錯誤", "設定儲存失敗。")

    def on_start():
        window_title, adb_serial, adb_path, mode_value = get_current_values()

        if not validate_values(window_title, adb_serial, adb_path, mode_value):
            return

        result["confirmed"] = True
        result["window_title_keyword"] = window_title
        result["adb_serial"] = adb_serial
        result["adb_path"] = adb_path
        result["mode"] = mode_value

        root.destroy()

    def on_cancel():
        result["confirmed"] = False
        root.destroy()

    start_btn = tk.Button(button_frame, text="開始執行", width=12, command=on_start)
    start_btn.grid(row=0, column=0, padx=8)

    apply_btn = tk.Button(button_frame, text="套用", width=12, command=on_apply)
    apply_btn.grid(row=0, column=1, padx=8)

    cancel_btn = tk.Button(button_frame, text="取消", width=12, command=on_cancel)
    cancel_btn.grid(row=0, column=2, padx=8)

    root.protocol("WM_DELETE_WINDOW", on_cancel)
    root.mainloop()

    if not result["confirmed"]:
        return False

    ADB_PATH = result["adb_path"]
    ADB_SERIAL = result["adb_serial"]
    WINDOW_TITLE_KEYWORD = result["window_title_keyword"]
    MODE = result["mode"]
    return True

def apply_mode_board_ratios():
    global BOARD_X_RATIO, BOARD_Y_RATIO, BOARD_W_RATIO, BOARD_H_RATIO

    if MODE == "preview":
        BOARD_X_RATIO = PRACTICE_BOARD_X_RATIO
        BOARD_Y_RATIO = PRACTICE_BOARD_Y_RATIO
        BOARD_W_RATIO = PRACTICE_BOARD_W_RATIO
        BOARD_H_RATIO = PRACTICE_BOARD_H_RATIO
        print("[MODE] 練習模式：已套用 practice board ratios")
    elif MODE == "run":
        BOARD_X_RATIO = LIVE_BOARD_X_RATIO
        BOARD_Y_RATIO = LIVE_BOARD_Y_RATIO
        BOARD_W_RATIO = LIVE_BOARD_W_RATIO
        BOARD_H_RATIO = LIVE_BOARD_H_RATIO
        print("[MODE] 實戰模式：已套用 live board ratios")
    else:
        print(f"[MODE] 未知模式：{MODE}，改用實戰模式參數")
        BOARD_X_RATIO = LIVE_BOARD_X_RATIO
        BOARD_Y_RATIO = LIVE_BOARD_Y_RATIO
        BOARD_W_RATIO = LIVE_BOARD_W_RATIO
        BOARD_H_RATIO = LIVE_BOARD_H_RATIO

    print(
        f"[BOARD] X={BOARD_X_RATIO:.6f} "
        f"Y={BOARD_Y_RATIO:.6f} "
        f"W={BOARD_W_RATIO:.6f} "
        f"H={BOARD_H_RATIO:.6f}"
    )


def clamp(v, low, high):
    return max(low, min(v, high))


def adb_run(args, capture_output=True):
    cmd = [ADB_PATH, "-s", ADB_SERIAL] + args
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE if capture_output else None,
        stderr=subprocess.PIPE if capture_output else None
    )
    return result


def get_adb_screen_size():
    result = adb_run(["shell", "wm", "size"], capture_output=True)
    if result.returncode != 0:
        print("取得 ADB 螢幕尺寸失敗")
        if result.stderr:
            print(result.stderr.decode("utf-8", errors="ignore"))
        return None, None

    text = result.stdout.decode("utf-8", errors="ignore")
    m = re.search(r"Physical size:\s*(\d+)x(\d+)", text)
    if not m:
        m = re.search(r"Override size:\s*(\d+)x(\d+)", text)

    if not m:
        print("無法解析 wm size 輸出：")
        print(text)
        return None, None

    w = int(m.group(1))
    h = int(m.group(2))
    return w, h


def find_bluestacks_window():
    windows = gw.getAllWindows()

    matched = []
    for w in windows:
        try:
            title = w.title or ""
            if WINDOW_TITLE_KEYWORD.lower() in title.lower() and w.width > 0 and w.height > 0:
                matched.append(w)
        except Exception:
            pass

    if not matched:
        return None

    matched.sort(key=lambda w: (w.width * w.height), reverse=True)
    return matched[0]


def crop_bgr_image(img, left, top, right, bottom):
    h, w = img.shape[:2]

    x1 = clamp(left, 0, w)
    y1 = clamp(top, 0, h)
    x2 = clamp(w - right, x1 + 1, w)
    y2 = clamp(h - bottom, y1 + 1, h)

    return img[y1:y2, x1:x2].copy()


def capture_bluestacks_screen():
    t0 = time.perf_counter()

    win = find_bluestacks_window()
    if win is None:
        print(f"找不到視窗：{WINDOW_TITLE_KEYWORD}")
        return None

    left = int(win.left)
    top = int(win.top)
    width = int(win.width)
    height = int(win.height)

    if width <= 0 or height <= 0:
        print("BlueStacks 視窗大小異常")
        return None

    monitor = {
        "left": left,
        "top": top,
        "width": width,
        "height": height
    }

    with mss.mss() as sct:
        raw = np.array(sct.grab(monitor))

    t1 = time.perf_counter()

    if raw is None or raw.size == 0:
        print("mss 視窗截圖失敗")
        return None

    img = cv2.cvtColor(raw, cv2.COLOR_BGRA2BGR)

    img = crop_bgr_image(
        img,
        CONTENT_CROP_LEFT,
        CONTENT_CROP_TOP,
        CONTENT_CROP_RIGHT,
        CONTENT_CROP_BOTTOM
    )

    img = crop_bgr_image(
        img,
        DEVICE_VIEW_LEFT,
        DEVICE_VIEW_TOP,
        DEVICE_VIEW_RIGHT,
        DEVICE_VIEW_BOTTOM
    )

    t2 = time.perf_counter()

    if img is None or img.size == 0:
        print("裁切後畫面為空")
        return None

    if VERBOSE:
        print(f"[TIME] window_capture={t1 - t0:.3f}s crop={t2 - t1:.3f}s total={t2 - t0:.3f}s")
        print(f"[CAPTURE] final_img_size = {img.shape[1]}x{img.shape[0]}")

    return img


def set_last_action_debug(action_type, img_point=None, adb_point=None, img_point2=None, adb_point2=None, note=""):
    global last_action_debug
    last_action_debug = {
        "type": action_type,
        "img_point": img_point,
        "adb_point": adb_point,
        "img_point2": img_point2,
        "adb_point2": adb_point2,
        "note": note,
        "ts": time.time()
    }


def image_to_adb_xy(x, y, img_w, img_h):
    if ADB_SCREEN_W is None or ADB_SCREEN_H is None:
        return int(x), int(y)

    if ADB_SCREEN_W > ADB_SCREEN_H and img_h > img_w:
        target_w = ADB_SCREEN_H
        target_h = ADB_SCREEN_W
    else:
        target_w = ADB_SCREEN_W
        target_h = ADB_SCREEN_H

    adb_x = int(round(x * target_w / img_w))
    adb_y = int(round(y * target_h / img_h))

    adb_x = clamp(adb_x, 0, target_w - 1)
    adb_y = clamp(adb_y, 0, target_h - 1)

    return adb_x, adb_y


def get_board_rect(img_w, img_h):
    board_x = int(img_w * BOARD_X_RATIO)
    board_y = int(img_h * BOARD_Y_RATIO)
    board_w = int(img_w * BOARD_W_RATIO)
    board_h = int(img_h * BOARD_H_RATIO)

    board_x = clamp(board_x, 0, img_w - 1)
    board_y = clamp(board_y, 0, img_h - 1)
    board_w = clamp(board_w, 1, img_w - board_x)
    board_h = clamp(board_h, 1, img_h - board_y)

    return board_x, board_y, board_w, board_h


def color_distance_squared(bgr1, bgr2):
    db = int(bgr1[0]) - int(bgr2[0])
    dg = int(bgr1[1]) - int(bgr2[1])
    dr = int(bgr1[2]) - int(bgr2[2])
    return db * db + dg * dg + dr * dr
def load_saved_config():
    global ADB_PATH, ADB_SERIAL, WINDOW_TITLE_KEYWORD, MODE

    if not os.path.exists(CONFIG_FILE):
        return

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        ADB_PATH = data.get("ADB_PATH", ADB_PATH)
        ADB_SERIAL = data.get("ADB_SERIAL", ADB_SERIAL)
        WINDOW_TITLE_KEYWORD = data.get("WINDOW_TITLE_KEYWORD", WINDOW_TITLE_KEYWORD)
        MODE = data.get("MODE", MODE)

        print(f"[CONFIG] 已載入設定檔：{CONFIG_FILE}")
    except Exception as e:
        print(f"[CONFIG] 載入設定檔失敗：{e}")


def save_current_config(window_title, adb_serial, adb_path, mode_value):
    data = {
        "WINDOW_TITLE_KEYWORD": window_title,
        "ADB_SERIAL": adb_serial,
        "ADB_PATH": adb_path,
        "MODE": mode_value
    }

    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"[CONFIG] 已儲存設定檔：{CONFIG_FILE}")
        return True
    except Exception as e:
        print(f"[CONFIG] 儲存設定檔失敗：{e}")
        return False

def classify_center_bgr(center_bgr):
    dist_red = color_distance_squared(center_bgr, RED_BGR)
    dist_blue = color_distance_squared(center_bgr, BLUE_BGR)

    nearest_dist = min(dist_red, dist_blue)

    if nearest_dist > NONE_THRESHOLD_SQUARED:
        result = "None"
    elif dist_red < dist_blue:
        result = "R"
    else:
        result = "B"

    return result, dist_red, dist_blue


def build_board_cell_cache(img_w, img_h):
    board_x, board_y, board_w, board_h = get_board_rect(img_w, img_h)

    cell_w = board_w / COLS
    cell_h = board_h / ROWS

    cells = []
    for r in range(ROWS):
        row_cells = []
        for c in range(COLS):
            x1 = int(board_x + c * cell_w)
            y1 = int(board_y + r * cell_h)
            x2 = int(board_x + (c + 1) * cell_w)
            y2 = int(board_y + (r + 1) * cell_h)

            x1 = clamp(x1, 0, img_w - 1)
            y1 = clamp(y1, 0, img_h - 1)
            x2 = clamp(x2, x1 + 1, img_w)
            y2 = clamp(y2, y1 + 1, img_h)

            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2
            cx = clamp(cx, x1, x2 - 1)
            cy = clamp(cy, y1, y2 - 1)

            row_cells.append({
                "row": r,
                "col": c,
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
                "cx": cx,
                "cy": cy
            })
        cells.append(row_cells)

    return cells


def ensure_board_cell_cache(img):
    global board_cell_cache, board_cell_cache_shape
    h, w = img.shape[:2]

    if board_cell_cache is None or board_cell_cache_shape != (w, h):
        board_cell_cache = build_board_cell_cache(w, h)
        board_cell_cache_shape = (w, h)
        if VERBOSE:
            print(f"[CACHE] rebuild board_cell_cache for size {w}x{h}")


def analyze_board(img):
    ensure_board_cell_cache(img)

    board_cells = []

    for r in range(ROWS):
        row_cells = []

        for c in range(COLS):
            base = board_cell_cache[r][c]
            x1, y1, x2, y2 = base["x1"], base["y1"], base["x2"], base["y2"]
            cx, cy = base["cx"], base["cy"]

            if (r, c) in invalid_cells:
                row_cells.append({
                    "type": "Blocked",
                    "cx": cx,
                    "cy": cy,
                    "row": r,
                    "col": c,
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2,
                    "center_bgr": (0, 0, 0),
                    "dist_red": None,
                    "dist_blue": None
                })
                continue

            center_bgr = tuple(int(v) for v in img[cy, cx])
            cell_type, dist_red, dist_blue = classify_center_bgr(center_bgr)

            row_cells.append({
                "type": cell_type,
                "cx": cx,
                "cy": cy,
                "row": r,
                "col": c,
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
                "center_bgr": center_bgr,
                "dist_red": dist_red,
                "dist_blue": dist_blue
            })

        board_cells.append(row_cells)

    return board_cells


def vote_type_list(type_list):
    counts = {"R": 0, "B": 0, "None": 0, "Blocked": 0}
    for t in type_list:
        if t in counts:
            counts[t] += 1
    best_type = max(counts, key=counts.get)
    return best_type, counts


def initialize_invalid_cells():
    global invalid_cells, invalid_cells_locked

    if invalid_cells_locked:
        print("invalid_cells 已鎖定，略過初始化")
        return

    counts = {}
    for r in range(ROWS):
        for c in range(COLS):
            counts[(r, c)] = {"R": 0, "B": 0, "None": 0}

    print("開始初始化無效格掃描...")

    for i in range(INIT_SCAN_COUNT):
        img = capture_bluestacks_screen()
        if img is None:
            time.sleep(INIT_SCAN_INTERVAL_SEC)
            continue

        reconnect_handled, img = try_handle_reconnect_popup(img)
        if reconnect_handled and img is None:
            time.sleep(INIT_SCAN_INTERVAL_SEC)
            continue

        board_cells = analyze_board(img)

        for r in range(ROWS):
            for c in range(COLS):
                t = board_cells[r][c]["type"]
                if t in ("R", "B", "None"):
                    counts[(r, c)][t] += 1

        print(f"初始化掃描 {i + 1}/{INIT_SCAN_COUNT}")
        time.sleep(INIT_SCAN_INTERVAL_SEC)

    invalid_cells.clear()

    for r in range(ROWS):
        for c in range(COLS):
            rb_count = counts[(r, c)]["R"] + counts[(r, c)]["B"]
            ratio = rb_count / INIT_SCAN_COUNT
            if ratio < INIT_VALID_THRESHOLD:
                invalid_cells.add((r, c))

    invalid_cells_locked = True

    print("初始化完成")
    print("invalid_cells =", invalid_cells)


def analyze_board_by_voting():
    vote_counts = {}
    last_cells = None
    last_img = None

    for r in range(ROWS):
        for c in range(COLS):
            vote_counts[(r, c)] = {"R": 0, "B": 0, "None": 0, "Blocked": 0}

    for i in range(VOTE_SCAN_COUNT):
        img = capture_bluestacks_screen()
        if img is None:
            time.sleep(VOTE_SCAN_INTERVAL_SEC)
            continue

        reconnect_handled, img = try_handle_reconnect_popup(img)
        if reconnect_handled and img is None:
            time.sleep(VOTE_SCAN_INTERVAL_SEC)
            continue

        board_cells = analyze_board(img)
        last_cells = board_cells
        last_img = img

        for r in range(ROWS):
            for c in range(COLS):
                t = board_cells[r][c]["type"]
                if t in vote_counts[(r, c)]:
                    vote_counts[(r, c)][t] += 1

        if i != VOTE_SCAN_COUNT - 1:
            time.sleep(VOTE_SCAN_INTERVAL_SEC)

    if last_cells is None:
        return None, None

    final_cells = []
    for r in range(ROWS):
        row_cells = []
        for c in range(COLS):
            cell = dict(last_cells[r][c])
            votes = vote_counts[(r, c)]
            final_type = max(votes, key=votes.get)
            cell["type"] = final_type
            row_cells.append(cell)
        final_cells.append(row_cells)

    return final_cells, last_img


def detect_reconnect_popup(img):
    h, w = img.shape[:2]

    x = int(w * RECONNECT_X_RATIO)
    y = int(h * RECONNECT_Y_RATIO)

    x = clamp(x, 0, w - 1)
    y = clamp(y, 0, h - 1)

    bgr = tuple(int(v) for v in img[y, x])
    dist = color_distance_squared(bgr, RECONNECT_BGR)

    if dist < RECONNECT_COLOR_THRESHOLD:
        return True, x, y

    return False, x, y


def click_reconnect(img, x, y):
    img_h, img_w = img.shape[:2]
    adb_x, adb_y = image_to_adb_xy(x, y, img_w, img_h)

    print(f"[RECONNECT] img_point=({x},{y}) img_size=({img_w},{img_h})")
    print(f"[RECONNECT] adb_point=({adb_x},{adb_y}) adb_size=({ADB_SCREEN_W},{ADB_SCREEN_H})")

    set_last_action_debug(
        action_type="tap",
        img_point=(x, y),
        adb_point=(adb_x, adb_y),
        note="RECONNECT TAP"
    )

    adb_run([
        "shell", "input", "tap",
        str(adb_x),
        str(adb_y)
    ], capture_output=False)

    time.sleep(RECONNECT_CLICK_DELAY)


def try_handle_reconnect_popup(img):
    reconnect, rx, ry = detect_reconnect_popup(img)
    if not reconnect:
        return False, img

    print("[RECONNECT] popup detected -> start auto clicking")
    count = 0
    latest_img = img

    while True:
        click_reconnect(latest_img, rx, ry)
        time.sleep(0.1)

        latest_img = capture_bluestacks_screen()
        if latest_img is None:
            count += 1
            if count >= RECONNECT_MAX_RETRY:
                print("[RECONNECT] retry limit reached (capture failed)")
                return True, None
            continue

        reconnect, rx, ry = detect_reconnect_popup(latest_img)
        if not reconnect:
            print("[RECONNECT] popup cleared")
            return True, latest_img

        count += 1
        if count >= RECONNECT_MAX_RETRY:
            print("[RECONNECT] retry limit reached")
            return True, latest_img


def get_cell_lists(board_cells):
    reds = []
    blues = []

    for r in range(ROWS):
        for c in range(COLS):
            cell = board_cells[r][c]
            if cell["type"] == "R":
                reds.append(cell)
            elif cell["type"] == "B":
                blues.append(cell)

    return reds, blues


def cell_distance(a, b):
    dx = a["cx"] - b["cx"]
    dy = a["cy"] - b["cy"]
    return math.hypot(dx, dy)


def build_fixed_pairs(reds, blues, red_limit=6, blue_limit=6):
    if len(reds) < red_limit or len(blues) < blue_limit:
        return None, f"初始化盤面不足：red={len(reds)} blue={len(blues)}，至少需要 {red_limit}/{blue_limit}"

    chosen_reds = reds[:red_limit]
    chosen_blues = blues[:blue_limit]

    remaining_reds = chosen_reds[:]
    remaining_blues = chosen_blues[:]

    pairs = []
    pair_id = 0

    while remaining_reds and remaining_blues:
        best = None
        best_score = None

        for b in remaining_blues:
            for r in remaining_reds:
                dist = cell_distance(b, r)
                if best_score is None or dist < best_score:
                    best_score = dist
                    best = (b, r)

        blue, red = best
        pairs.append({
            "id": pair_id,
            "blue": blue,
            "red": red,
            "distance": best_score
        })
        pair_id += 1

        remaining_blues.remove(blue)
        remaining_reds.remove(red)

    return pairs, "OK"


def adb_swipe(x1, y1, x2, y2, duration_ms):
    t0 = time.perf_counter()

    args = [
        "shell", "input", "swipe",
        str(int(x1)), str(int(y1)),
        str(int(x2)), str(int(y2)),
        str(int(duration_ms))
    ]
    result = adb_run(args, capture_output=True)

    t1 = time.perf_counter()

    if VERBOSE:
        print(f"[TIME] swipe total={t1 - t0:.3f}s")
        print(f"[ADB] swipe ({x1},{y1}) -> ({x2},{y2}) duration={duration_ms}ms")

    if result.returncode != 0:
        print("ADB swipe 失敗")
        if result.stderr:
            print(result.stderr.decode("utf-8", errors="ignore"))


def attack_fixed_pair(pair, img_shape):
    img_h, img_w = img_shape[:2]

    blue = pair["blue"]
    red = pair["red"]

    # 第一下：藍 -> 紅
    adb_x1, adb_y1 = image_to_adb_xy(blue["cx"], blue["cy"], img_w, img_h)
    adb_x2, adb_y2 = image_to_adb_xy(red["cx"], red["cy"], img_w, img_h)

    set_last_action_debug(
        action_type="swipe",
        img_point=(blue["cx"], blue["cy"]),
        adb_point=(adb_x1, adb_y1),
        img_point2=(red["cx"], red["cy"]),
        adb_point2=(adb_x2, adb_y2),
        note=f"PAIR#{pair['id']} B[{blue['row']},{blue['col']}] -> R[{red['row']},{red['col']}]"
    )

    print(
        f"[PAIR] #{pair['id']} "
        f"B[{blue['row']},{blue['col']}] -> R[{red['row']},{red['col']}] "
        f"dist={pair['distance']:.2f}"
    )
    adb_swipe(adb_x1, adb_y1, adb_x2, adb_y2, SWIPE_DURATION_MS)

    # 第二下：紅 -> 藍
    adb_x3, adb_y3 = image_to_adb_xy(red["cx"], red["cy"], img_w, img_h)
    adb_x4, adb_y4 = image_to_adb_xy(blue["cx"], blue["cy"], img_w, img_h)

    set_last_action_debug(
        action_type="swipe",
        img_point=(red["cx"], red["cy"]),
        adb_point=(adb_x3, adb_y3),
        img_point2=(blue["cx"], blue["cy"]),
        adb_point2=(adb_x4, adb_y4),
        note=f"PAIR#{pair['id']} R[{red['row']},{red['col']}] -> B[{blue['row']},{blue['col']}]"
    )

    print(
        f"[PAIR] #{pair['id']} "
        f"R[{red['row']},{red['col']}] -> B[{blue['row']},{blue['col']}] "
        f"dist={pair['distance']:.2f}"
    )
    adb_swipe(adb_x3, adb_y3, adb_x4, adb_y4, SWIPE_DURATION_MS)


def draw_debug(img, board_cells, pairs=None, active_pair_idx=None):
    img_h, img_w = img.shape[:2]
    board_x, board_y, board_w, board_h = get_board_rect(img_w, img_h)

    output = img.copy()

    cv2.rectangle(
        output,
        (board_x, board_y),
        (board_x + board_w, board_y + board_h),
        (0, 255, 0),
        3
    )

    for r in range(ROWS):
        for c in range(COLS):
            cell = board_cells[r][c]
            x1, y1, x2, y2 = cell["x1"], cell["y1"], cell["x2"], cell["y2"]
            cx, cy = cell["cx"], cell["cy"]

            if cell["type"] == "R":
                color = (0, 0, 255)
            elif cell["type"] == "B":
                color = (255, 0, 0)
            elif cell["type"] == "Blocked":
                color = (0, 255, 255)
            else:
                color = (180, 180, 180)

            cv2.rectangle(output, (x1, y1), (x2, y2), (0, 255, 255), 2)
            cv2.circle(output, (cx, cy), 5, color, -1)

            label1 = f"{r},{c} {cell['type']}"
            label2 = f"BGR={cell['center_bgr']}"

            cv2.putText(
                output,
                label1,
                (x1 + 4, y1 + 18),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.42,
                color,
                2
            )
            cv2.putText(
                output,
                label2,
                (x1 + 4, y1 + 34),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.30,
                color,
                1
            )

    if pairs is not None:
        for i, pair in enumerate(pairs):
            b = pair["blue"]
            r = pair["red"]

            color = (0, 255, 0)
            thickness = 2

            if active_pair_idx is not None and i == active_pair_idx:
                color = (0, 255, 255)
                thickness = 4

            cv2.line(output, (b["cx"], b["cy"]), (r["cx"], r["cy"]), color, thickness)

            mid_x = (b["cx"] + r["cx"]) // 2
            mid_y = (b["cy"] + r["cy"]) // 2

            cv2.putText(
                output,
                f"P{i}",
                (mid_x + 4, mid_y - 4),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2
            )

    rx = int(img_w * RECONNECT_X_RATIO)
    ry = int(img_h * RECONNECT_Y_RATIO)
    rx = clamp(rx, 0, img_w - 1)
    ry = clamp(ry, 0, img_h - 1)

    cv2.circle(output, (rx, ry), 8, (0, 255, 255), 2)
    cv2.putText(
        output,
        "RECONNECT_CHECK",
        (rx + 10, ry - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 255, 255),
        2
    )

    global last_action_debug
    if last_action_debug is not None:
        action_type = last_action_debug.get("type")
        p1 = last_action_debug.get("img_point")
        p2 = last_action_debug.get("img_point2")
        adb_p1 = last_action_debug.get("adb_point")
        adb_p2 = last_action_debug.get("adb_point2")
        note = last_action_debug.get("note", "")
        age = time.time() - last_action_debug.get("ts", time.time())

        if p1 is not None:
            cv2.circle(output, p1, 12, (0, 255, 255), 3)
            cv2.putText(
                output,
                f"LAST {action_type.upper()} P1 img={p1} adb={adb_p1}",
                (20, img_h - 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 255),
                2
            )

        if action_type == "swipe" and p1 is not None and p2 is not None:
            cv2.arrowedLine(output, p1, p2, (255, 255, 0), 3, tipLength=0.2)
            cv2.circle(output, p2, 12, (255, 255, 0), 3)
            cv2.putText(
                output,
                f"P2 img={p2} adb={adb_p2}",
                (20, img_h - 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 0),
                2
            )

        cv2.putText(
            output,
            f"age={age:.2f}s  {note}",
            (20, img_h - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )

    return output


def print_pairs(pairs):
    print("\n===== 固定配對結果 =====")
    for pair in pairs:
        b = pair["blue"]
        r = pair["red"]
        print(
            f"PAIR #{pair['id']}: "
            f"B[{b['row']},{b['col']}] ({b['cx']},{b['cy']}) <-> "
            f"R[{r['row']},{r['col']}] ({r['cx']},{r['cy']}) "
            f"distance={pair['distance']:.2f}"
        )


def initialize_fixed_pairs():
    global initial_board_cells, fixed_reds, fixed_blues, fixed_pairs

    print("開始初始化盤面並建立固定 6紅6藍 配對...")

    board_cells, last_img = analyze_board_by_voting()
    if board_cells is None or last_img is None:
        print("初始化失敗：無法取得盤面")
        return False, None

    reds, blues = get_cell_lists(board_cells)

    print(f"初始化盤面結果：red={len(reds)} blue={len(blues)}")

    pairs, msg = build_fixed_pairs(
        reds,
        blues,
        red_limit=FIXED_RED_COUNT,
        blue_limit=FIXED_BLUE_COUNT
    )

    if pairs is None:
        print(f"建立固定配對失敗：{msg}")
        return False, last_img

    initial_board_cells = board_cells
    fixed_reds = reds[:FIXED_RED_COUNT]
    fixed_blues = blues[:FIXED_BLUE_COUNT]
    fixed_pairs = pairs

    print_pairs(fixed_pairs)
    return True, last_img


def preview_loop(base_img):
    if not fixed_pairs:
        print("沒有固定配對，無法執行")
        return

    active_pair_idx = 0
    next_attack_ts = time.perf_counter()

    while True:
        now = time.perf_counter()

        if now >= next_attack_ts:
            pair = fixed_pairs[active_pair_idx]
            attack_fixed_pair(pair, base_img.shape)

            active_pair_idx = (active_pair_idx + 1) % len(fixed_pairs)
            next_attack_ts += PAIR_ATTACK_INTERVAL_SEC

            # 防止嚴重落後時時間越積越偏
            if now - next_attack_ts > PAIR_ATTACK_INTERVAL_SEC:
                next_attack_ts = now + PAIR_ATTACK_INTERVAL_SEC

        debug_img = draw_debug(base_img, initial_board_cells, fixed_pairs, active_pair_idx)
        cv2.imshow("Preview", debug_img)

        if SAVE_DEBUG_IMAGE_EACH_LOOP:
            cv2.imwrite("preview_debug.png", debug_img)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break

        time.sleep(0.001)

    cv2.destroyAllWindows()

def run_loop(base_img):
    if not fixed_pairs:
        print("沒有固定配對，無法執行")
        return

    pair_index = 0
    next_attack_ts = time.perf_counter()

    while True:
        now = time.perf_counter()

        if now >= next_attack_ts:
            pair = fixed_pairs[pair_index]
            attack_fixed_pair(pair, base_img.shape)

            pair_index = (pair_index + 1) % len(fixed_pairs)
            next_attack_ts += PAIR_ATTACK_INTERVAL_SEC

            if now - next_attack_ts > PAIR_ATTACK_INTERVAL_SEC:
                next_attack_ts = now + PAIR_ATTACK_INTERVAL_SEC

        if SHOW_DEBUG_WINDOW:
            active_pair_idx = pair_index % len(fixed_pairs)
            debug_img = draw_debug(base_img, initial_board_cells, fixed_pairs, active_pair_idx)
            cv2.imshow("Run", debug_img)

            if SAVE_DEBUG_IMAGE_EACH_LOOP:
                cv2.imwrite("run_debug.png", debug_img)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
        else:
            time.sleep(0.001)

    cv2.destroyAllWindows()


def main():
    global ADB_SCREEN_W, ADB_SCREEN_H

    if not show_startup_config_ui():
        print("使用者取消啟動")
        return

    apply_mode_board_ratios()

    print("===== Bot 啟動 =====")
    print(f"MODE = {MODE}")
    print(f"WINDOW_TITLE_KEYWORD = {WINDOW_TITLE_KEYWORD}")
    print(f"ADB_SERIAL = {ADB_SERIAL}")
    print(f"ADB_PATH = {ADB_PATH}")
    print("策略：初始化一次 -> 固定 6紅 6藍 -> 最近距離兩兩配對 -> 不再截圖 -> 每 0.5 秒輪流拖曳一組，且同組來回互拖")
    print("目前使用 Windows window capture + ADB swipe")
    print("按視窗內 q 可結束")
    print()

    ADB_SCREEN_W, ADB_SCREEN_H = get_adb_screen_size()
    if ADB_SCREEN_W is None or ADB_SCREEN_H is None:
        print("ADB 螢幕尺寸初始化失敗")
        return

    print(f"ADB screen size = {ADB_SCREEN_W}x{ADB_SCREEN_H}")

    first_img = capture_bluestacks_screen()
    if first_img is None:
        print("初始化截圖失敗")
        return

    reconnect_handled, first_img = try_handle_reconnect_popup(first_img)
    if reconnect_handled and first_img is None:
        print("重連後仍無法取得畫面")
        return

    ensure_board_cell_cache(first_img)
    initialize_invalid_cells()

    ok, base_img = initialize_fixed_pairs()
    if not ok:
        print("固定配對初始化失敗，程式結束")
        return

    if base_img is None:
        print("base_img 為空，程式結束")
        return

    if MODE == "preview":
        preview_loop(base_img)
    elif MODE == "run":
        run_loop(base_img)
    else:
        print("MODE 只能是 'preview' 或 'run'")


if __name__ == "__main__":
    main()