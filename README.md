# 🚀 Randomdice-monolith-co-op-auto-bot

## 📌 Overview

This project is an **automation bot** built with:

* Python
* OpenCV
* ADB (Android Debug Bridge)

It automatically detects the game board and performs **swipe actions** to attack enemies.

---

## 🎯 Features

* 🎮 Real-time **image recognition**
* 🤖 Automatic **attack execution**
* 🔄 Dual-mode support:

  * `preview` (practice mode)
  * `run` (co-op mode)
* 🧠 Noise reduction with **voting mechanism**
* 💾 Persistent settings via configuration file
* 🖥️ GUI control panel

---

## 🖥️ Environment

* OS: Windows
* Emulator: BlueStacks
* Python: 3.x
* ADB path example:

  ```
  C:\platform-tools\adb.exe
  ```

---

## ⚙️ Environment Setup (Step-by-Step Guide)

This project requires **BlueStacks + ADB + Python environment setup** before running.

---

## 🖥️ Step 1 — Install BlueStacks

1. Download from the official website:
   👉 https://www.bluestacks.com/

2. Install and launch BlueStacks

3. Make sure your game can run properly

---

## 🔧 Step 2 — Enable ADB (VERY IMPORTANT)

Inside BlueStacks:

```
Settings
→ Advanced
→ Enable Android Debug Bridge (ADB)
```

✅ This must be enabled for Python to control the emulator

---

## 📡 Step 3 — Get ADB_SERIAL

### Method 1 (Recommended)

Open Command Prompt and run:

```bash
adb devices
```

You should see:

```
List of devices attached
127.0.0.1:5555 device
```

👉 This means:

```text
ADB_SERIAL = "127.0.0.1:5555"
```

---

### Method 2 (If nothing shows)

Connect manually:

```bash
adb connect 127.0.0.1:5555
```

Then run again:

```bash
adb devices
```

---

## 📁 Step 4 — Get ADB_PATH

ADB is an executable file (`adb.exe`)

### Common location:

```text
C:\platform-tools\adb.exe
```

👉 So your config should be:

```python
ADB_PATH = r"C:\platform-tools\adb.exe"
```

---

### If you don't have ADB

Download Android Platform Tools:

👉 https://developer.android.com/tools/releases/platform-tools

Extract and use directly

---

## 🐍 Step 5 — Install Python Dependencies

```bash
pip install opencv-python numpy mss pygetwindow
```

---

## 🧪 Step 6 — Test ADB Connection

```bash
adb devices
```

✅ Expected output:

```
127.0.0.1:5555 device
```

---

## 🚀 Step 7 — Run the Program

```bash
python main.py
```

---

## 🧠 Common Issues

### ❌ Device not found

👉 Fix:

```bash
adb connect 127.0.0.1:5555
```

---

### ❌ Multiple devices error

👉 Fix:

```bash
adb -s 127.0.0.1:5555 devices
```

Or set in code:

```python
ADB_SERIAL = "127.0.0.1:5555"
```

---
