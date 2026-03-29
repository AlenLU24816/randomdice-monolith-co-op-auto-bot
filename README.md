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
  * `run` (real mode)
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

## ⚙️ Installation

### 1️⃣ Install dependencies

```bash
pip install opencv-python numpy mss pygetwindow
```

---

### 2️⃣ Setup ADB

```bash
adb connect 127.0.0.1:5555
adb devices
```

---

## 🚀 Usage

Run the main program:

```bash
python main.py
```

---

## 🖥️ GUI Settings

When starting, a GUI will appear.

You can configure:

* `WINDOW_TITLE_KEYWORD`
* `ADB_SERIAL`
* `ADB_PATH`
* `MODE` (preview / run)

### Buttons:

* **Apply** → Save configuration
* **Start** → Launch bot

---

## 🔄 Modes

### 🔹 Preview Mode

* Uses practice board ratios
* Shows debug view
* ✅ Also performs attacks

---

### 🔹 Run Mode

* Uses real battle ratios
* Executes attacks

---

## 🧠 Core Workflow

```text
Screen Capture (mss)
↓
Crop BlueStacks window
↓
Locate board (ratio)
↓
Sample each cell center (BGR)
↓
Classify R / B / None
↓
Pair targets
↓
ADB swipe execution
```

---

## 🎮 Game Logic

* Grid: `3 × 5`
* Available cells: ~11
* Action:

```
Blue → Red
Red → Blue
```

---

## 🎨 Color Detection

```python
RED_BGR = (111, 23, 199)
BLUE_BGR = (122, 100, 0)
NONE_THRESHOLD_SQUARED = 4200
```

---

## 📐 Board Detection

### Run Mode

```python
BOARD_X_RATIO = 0.212037
BOARD_Y_RATIO = 0.503646
BOARD_W_RATIO = 0.575926
BOARD_H_RATIO = 0.187500
```

### Preview Mode

```python
BOARD_X_RATIO = 0.212037
BOARD_Y_RATIO = 0.553646
BOARD_W_RATIO = 0.578704
BOARD_H_RATIO = 0.187500
```

---

## ⚔️ Attack Strategy

* Select:

  * 6 Reds
  * 6 Blues
* Match using:

```
Greedy shortest distance pairing
```

* Execute:

```
Blue → Red
Red → Blue
```

---

## 📡 ADB Control

```bash
adb shell input swipe x1 y1 x2 y2 duration
```

Key parameters:

```python
SWIPE_DURATION_MS = 180
PAIR_ATTACK_INTERVAL_SEC = 0.5
```

---

## 🧩 Anti-Noise System

### 🔹 Initialization Filter

* Scan 5 times
* Mark unstable cells as Blocked

### 🔹 Voting Mechanism

* Sample multiple frames
* Use majority vote

---

## 💾 Configuration

Saved in:

```
bot_config.json
```

* Auto-load on startup
* Updated via GUI

---

## 🐞 Known Issues & Fixes

### ❌ Swipe not working

**Cause:**

```
SWIPE_DURATION too short
```

**Fix:**

```python
SWIPE_DURATION_MS = 180
```

---

### ❌ Preview mode not attacking

**Fix:**

* Enable attack in preview loop

---

## 📁 Project Structure

```
project/
│── main.py
│── bot_config.json
│── README.md
```

---

## 📌 GitHub Setup

```bash
git init
git add .
git commit -m "initial commit"
git remote add origin <repo_url>
git branch -M main
git push -u origin main
```

---

## 🔮 Future Improvements

* 🔹 Real-time continuous capture
* 🔹 Dynamic pairing (not fixed 6 pairs)
* 🔹 AI-based decision system (maximize DPS)
* 🔹 GUI tuning (swipe speed, delay)

---

## 🌍 Keywords

* Automation bot
* Swipe action
* Image recognition
* Voting mechanism
* Configuration file

---

## ⚠️ Disclaimer

This project is for **educational purposes only**.
Use at your own risk.

---
