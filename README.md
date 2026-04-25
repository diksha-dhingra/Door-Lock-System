<div align="center">

# 🔐 Smart Multi-Factor Access Control System

### Face Recognition → RFID Card → PIN Keypad

[![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Arduino](https://img.shields.io/badge/Arduino-Uno_R3-00979D?style=for-the-badge&logo=arduino&logoColor=white)](https://arduino.cc)
[![DeepFace](https://img.shields.io/badge/DeepFace-Facenet512-FF6F00?style=for-the-badge&logo=tensorflow&logoColor=white)](https://github.com/serengil/deepface)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.x-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)](https://opencv.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

<br>

A **three-stage security system** that combines AI-powered face recognition, RFID card scanning, and PIN entry — all working together as a single, seamless access control pipeline. Built with Python + Arduino.

<br>

```
┌──────────────┐     Serial 'F'/'D'     ┌─────────────────────────────────────┐
│  Python (PC) │ ─────────────────────► │            Arduino Uno               │
│  DeepFace AI │                        │  RFID Reader → Keypad → Servo Lock  │
│  Webcam      │ ◄───────────────────── │  OLED Display + Buzzer Feedback     │
└──────────────┘                        └─────────────────────────────────────┘
```

</div>

---

## 📋 Table of Contents

- [How It Works](#-how-it-works)
- [Features](#-features)
- [System Architecture](#-system-architecture)
- [Hardware Requirements](#-hardware-requirements)
- [Circuit Wiring](#-circuit-wiring)
- [Software Requirements](#-software-requirements)
- [Installation & Setup](#-installation--setup)
- [Configuration](#-configuration)
- [Project Structure](#-project-structure)
- [Security Layers Explained](#-security-layers-explained)
- [Troubleshooting](#-troubleshooting)
- [Future Improvements](#-future-improvements)

---

## ⚙️ How It Works

The system enforces **three consecutive security gates**. Failing any one of them immediately denies access — all three must pass in order.

```
 👤 Person stands at door
         │
         ▼
 ┌───────────────────┐
 │  STAGE 1          │  Python webcam captures face
 │  Face Recognition │  DeepFace / Facenet512 matches against known_faces/
 └────────┬──────────┘
          │ ✅ Match found → sends 'F' to Arduino
          │ ❌ Timeout (15s) → sends 'D' → ACCESS DENIED
          ▼
 ┌───────────────────┐
 │  STAGE 2          │  Arduino prompts "Scan Your Card"
 │  RFID Card Scan   │  MFRC522 reads UID, compares to authorised UID
 └────────┬──────────┘
          │ ✅ Card matches → prompts PIN
          │ ❌ Wrong card / timeout → ACCESS DENIED
          ▼
 ┌───────────────────┐
 │  STAGE 3          │  4×3 keypad, PIN hidden as ****
 │  PIN Entry        │  Stored securely in PROGMEM (flash, not RAM)
 └────────┬──────────┘
          │ ✅ Correct PIN
          ▼
 🔓 SERVO UNLOCKS → Door opens for 4 seconds → Re-locks automatically
```

---

## ✨ Features

- **🤖 AI Face Recognition** — Uses DeepFace with the Facenet512 model (512-dimensional embeddings) for high-accuracy face matching with cosine distance metric
- **🧵 Threaded Verification** — Face recognition runs in a background thread, keeping the camera feed smooth and lag-free at all times
- **📡 RFID Authentication** — MFRC522 module reads card UID over SPI; only pre-approved cards pass
- **🔢 Secure PIN Entry** — Matrix keypad with asterisk masking; PIN stored in flash (PROGMEM) to protect Arduino's 2KB SRAM
- **🖥️ OLED Feedback** — SSD1306 128×64 display shows real-time status at every stage
- **🔔 Audio Cues** — Distinct buzzer patterns for key presses, card scan, success, and error
- **🔒 Auto-Locking** — Servo returns to locked position after 4 seconds automatically
- **♻️ Auto-Reset** — System resets cleanly after every attempt, granted or denied
- **⏱️ Timeouts** — 15-second face scan timeout, 15-second RFID timeout, 10-second PIN timeout — fully configurable

---

## 🏗️ System Architecture

The design is split into two subsystems connected via USB serial at 9600 baud:

```
╔══════════════════════════════════════╗     USB Serial      ╔══════════════════════════════════════╗
║         PC SUBSYSTEM (Python)        ║ ──────────────────► ║     MICROCONTROLLER (Arduino Uno)    ║
║                                      ║   'F' = Verified    ║                                      ║
║  • Captures webcam @ 30fps           ║   'D' = Denied      ║  • Listens on Serial port            ║
║  • Every 8th frame → verify thread  ║                     ║  • RFID scan over SPI                ║
║  • DeepFace.verify() with            ║ ◄────────────────── ║  • PIN via matrix keypad             ║
║    Facenet512 + cosine distance      ║                     ║  • OLED display (I2C)                ║
║  • Shows live camera with UI         ║                     ║  • Servo motor control (PWM)         ║
║  • Sends decision via pyserial       ║                     ║  • Buzzer audio feedback             ║
╚══════════════════════════════════════╝                     ╚══════════════════════════════════════╝
```

**Why split between PC and Arduino?**
> Face recognition via deep learning needs a CPU with sufficient power — not feasible on an ATmega328P. The Arduino excels at real-time I/O (servo PWM, SPI, I2C, keypad scanning). Splitting the work this way gets the best from both platforms.

---

## 🔧 Hardware Requirements

| Component | Specification | Qty |
|-----------|--------------|-----|
| Arduino Uno R3 | ATmega328P @ 16 MHz | 1 |
| USB Webcam | Min. 640×480 @ 30fps | 1 |
| MFRC522 RFID Reader | 13.56 MHz, SPI interface | 1 |
| RFID Card / Tag | Mifare 1K or compatible, 4-byte UID | 1+ |
| SSD1306 OLED Display | 128×64 px, I2C @ 0x3C, 3.3V–5V | 1 |
| 4×3 Matrix Keypad | Membrane type, 7-pin | 1 |
| Servo Motor | SG90 / MG90S, PWM | 1 |
| Piezo Buzzer | 5V passive | 1 |
| Jumper Wires | Male-to-male, Male-to-female | Assorted |
| Breadboard | Standard 830-point | 1 |
| USB Cable (Type-B) | Arduino ↔ PC | 1 |

---

## 🔌 Circuit Wiring

### Arduino Pin Mapping

```
MFRC522 RFID Reader (SPI)          SSD1306 OLED (I2C)
─────────────────────────          ──────────────────
MFRC522 SDA  → Arduino Pin 10      OLED SDA → Arduino A4
MFRC522 SCK  → Arduino Pin 13      OLED SCL → Arduino A5
MFRC522 MOSI → Arduino Pin 11      OLED VCC → 3.3V
MFRC522 MISO → Arduino Pin 12      OLED GND → GND
MFRC522 RST  → Arduino Pin 9
MFRC522 VCC  → 3.3V
MFRC522 GND  → GND

Servo Motor (PWM)                  Piezo Buzzer
─────────────────                  ─────────────
Servo Signal → Arduino A0          Buzzer (+) → Arduino A1
Servo VCC    → 5V                  Buzzer (-) → GND
Servo GND    → GND

4×3 Matrix Keypad
──────────────────────────────────────────────────
ROW 1 → Pin 8   ROW 2 → Pin 7   ROW 3 → Pin 6   ROW 4 → Pin 5
COL 1 → Pin 2   COL 2 → Pin 3   COL 3 → Pin 4

Layout:  [ 1 ][ 2 ][ 3 ]
         [ 4 ][ 5 ][ 6 ]
         [ 7 ][ 8 ][ 9 ]
         [ * ][ 0 ][ # ]    ← '#' = Confirm  |  '*' = Clear
```

### Full Wiring Diagram

```
                     SMART LOCK – SYSTEM WIRING OVERVIEW

  +------------------+        USB/Serial (9600 baud)       +----------------+
  |   Python (PC)    |<=====================================>| Arduino Uno R3 |
  |  face_lock.py    |    'F' = Face Verified               +-------+--------+
  |  DeepFace AI     |    'D' = Denied                              |
  |  Webcam Feed     |                         +--------------------+--------------------+
  +------------------+                         |                    |                    |
                                        SPI Bus             I2C (0x3C)             PWM A0
                                               |                    |                    |
                                    +----------+------+   +---------+--------+   +-------+------+
                                    |  MFRC522        |   |  SSD1306 OLED    |   |  Servo Motor |
                                    |  RFID Reader    |   |  128x64 Display  |   |  0°  = Lock  |
                                    |  SDA → Pin 10   |   |  SDA → A4        |   |  90° = Open  |
                                    |  RST → Pin 9    |   |  SCL → A5        |   +--------------+
                                    +-----------------+   +------------------+
                                                                           Pin A1
                                                                               |
                                                                  +------------+--------+
                                                                  |    Piezo Buzzer     |
                                                                  +---------------------+
```

---

## 💻 Software Requirements

### Python Side (PC)

```bash
pip install deepface opencv-python pyserial numpy tf-keras
```

| Library | Version | Purpose |
|---------|---------|---------|
| `deepface` | Latest | Face detection + Facenet512 recognition |
| `opencv-python` | 4.x | Webcam capture and live video display |
| `pyserial` | 3.x | USB serial communication with Arduino |
| `numpy` | Latest | Image array operations |
| `tf-keras` | Latest | TensorFlow backend for DeepFace |

### Arduino Side (Arduino IDE)

Install these libraries via **Sketch → Include Library → Manage Libraries**:

| Library | Install Name | Purpose |
|---------|-------------|---------|
| Adafruit SSD1306 | `Adafruit SSD1306` | OLED display driver |
| Adafruit GFX | `Adafruit GFX Library` | Graphics primitives |
| MFRC522 | `MFRC522` by GithubCommunity | RFID reader driver |
| Keypad | `Keypad` by Mark Stanley | Matrix keypad scanning |
| Servo | Built-in | Servo motor PWM control |
| Wire | Built-in | I2C communication |
| SPI | Built-in | SPI communication |

---

## 🚀 Installation & Setup

### Step 1 — Clone the Repository

```bash
git clone https://github.com/yourusername/smart-lock-system.git
cd smart-lock-system
```

### Step 2 — Install Python Dependencies

```bash
pip install deepface opencv-python pyserial numpy tf-keras
```

### Step 3 — Add Your Face Photos

Create a folder called `known_faces/` in the same directory as `face_lock.py` and add clear, front-facing photos of all authorised people:

```
smart-lock-system/
├── known_faces/
│   ├── your_name.jpg       ← clear front-facing photo
│   ├── person2.png
│   └── ...
├── face_lock.py
└── smart_lock.ino
```

> **Tips for best accuracy:**
> - Use well-lit, frontal face photos
> - One photo per person is enough (Facenet512 handles variation well)
> - Supported formats: `.jpg`, `.jpeg`, `.png`

### Step 4 — Find Your RFID Card UID

Upload this temporary sketch to your Arduino to read your card's UID:

```cpp
#include <SPI.h>
#include <MFRC522.h>
MFRC522 rfid(10, 9);
void setup() { Serial.begin(9600); SPI.begin(); rfid.PCD_Init(); }
void loop() {
  if (!rfid.PICC_IsNewCardPresent() || !rfid.PICC_ReadCardSerial()) return;
  Serial.print("UID: ");
  for (byte i = 0; i < rfid.uid.size; i++) Serial.print(rfid.uid.uidByte[i], HEX);
  Serial.println();
  rfid.PICC_HaltA();
}
```

Note the 4 hex bytes printed in Serial Monitor.

### Step 5 — Configure the Arduino Sketch

Open `smart_lock.ino` and update these two lines:

```cpp
// Line ~20: Replace with your card's UID bytes from Step 4
byte authorizedUID[] = {0x0D, 0x22, 0xD2, 0x06};

// Line ~24: Change to your desired PIN
const char masterPassword[] PROGMEM = "1234";
```

### Step 6 — Upload Arduino Sketch

1. Open `smart_lock.ino` in Arduino IDE
2. Select **Tools → Board → Arduino Uno**
3. Select **Tools → Port → COMx** (your Arduino's port)
4. Click **Upload**

### Step 7 — Configure and Run Python

Open `face_lock.py` and set the correct serial port:

```python
# Line 13 — match this to your Arduino's COM port
SERIAL_PORT = "COM8"      # Windows:  "COM3", "COM8", etc.
                           # Linux:    "/dev/ttyUSB0" or "/dev/ttyACM0"
                           # macOS:    "/dev/cu.usbmodem..."
```

Then run:

```bash
python face_lock.py
```

A camera window will open. Stand in front of the webcam — the system will start verifying automatically.

---

## ⚙️ Configuration

All tunable parameters are at the top of `face_lock.py`:

```python
# -------- CONFIG --------
SERIAL_PORT       = "COM8"    # Arduino serial port
BAUD_RATE         = 9600      # Must match Arduino sketch
KNOWN_FACES_DIR   = "known_faces"  # Folder with authorised face photos
FRAMES_TO_CONFIRM = 1         # Consecutive matches needed before granting
SCAN_TIMEOUT      = 15        # Seconds before face scan times out → DENIED
VERIFY_EVERY_N    = 8         # Run DeepFace every N frames (higher = smoother camera)
# ------------------------
```

| Parameter | Default | Effect |
|-----------|---------|--------|
| `FRAMES_TO_CONFIRM` | `1` | Increase to `3`–`5` for stricter matching (reduces false positives) |
| `SCAN_TIMEOUT` | `15s` | How long to wait for a face match before denying |
| `VERIFY_EVERY_N` | `8` | Lower = more frequent checks (higher CPU), higher = smoother video |

---

## 📁 Project Structure

```
smart-lock-system/
│
├── face_lock.py          # Python: webcam + DeepFace + serial control
├── smart_lock.ino        # Arduino: RFID + keypad + servo + OLED + buzzer
│
├── known_faces/          # 📂 Put authorised face images here
│   └── your_photo.jpg
│
└── README.md
```

---

## 🛡️ Security Layers Explained

### Layer 1 — Face Recognition (DeepFace + Facenet512)

DeepFace extracts a **512-dimensional embedding vector** from the detected face using the Facenet512 neural network. It then computes the **cosine distance** between this vector and all stored reference embeddings. Cosine distance measures the angle between vectors, making it robust to lighting and scale variation.

```python
result = DeepFace.verify(
    frame_copy,
    img_path,
    model_name="Facenet512",    # ← 512-dim embeddings, high accuracy
    enforce_detection=False,
    distance_metric="cosine"    # ← angle-based, lighting-robust
)
```

### Layer 2 — RFID UID Check

The MFRC522 reads the card's 4-byte unique identifier over SPI. The Arduino compares it byte-by-byte against the hardcoded `authorizedUID[]`. Any mismatch immediately denies and resets.

```cpp
byte authorizedUID[] = {0x0D, 0x22, 0xD2, 0x06};
```

### Layer 3 — PIN (Stored in Flash / PROGMEM)

The PIN is stored with the `PROGMEM` keyword, keeping it in the 32KB flash rather than the 2KB SRAM. This avoids RAM overflow on the ATmega328P and is retrieved only during comparison:

```cpp
const char masterPassword[] PROGMEM = "1234";
// ...
char pwd[10];
strcpy_P(pwd, masterPassword);   // copy from flash to RAM only for compare
return (input == String(pwd));
```

---

## 🔊 Buzzer Patterns

| Event | Pattern |
|-------|---------|
| System Start | High-Low-High (welcome melody) |
| Key Pressed | Short 2kHz beep (80ms) |
| Card Scanned | Medium 1kHz beep (150ms) |
| Access Granted | Melodic 4-tone success sequence |
| Access Denied | Two descending low tones |

---

## 🖥️ Camera UI Elements

While running, the camera window shows:

- **Progress bar** — fills as consecutive face matches accumulate
- **Match counter** — `Verifying X / Y` (current / required matches)
- **Countdown timer** — seconds remaining in the scan window
- **"Analysing..."** indicator — shown while DeepFace is processing in background
- **Green overlay** — flashes on GRANTED
- **Red overlay** — flashes on DENIED

---

## 🐛 Troubleshooting

| Problem | Likely Cause | Fix |
|---------|-------------|-----|
| `[ERROR] Serial: ...` | Wrong COM port | Check Device Manager / `ls /dev/tty*` and update `SERIAL_PORT` |
| `[ERROR] No images in known_faces/` | Empty folder | Add `.jpg` or `.png` face photos |
| Face never matches | Poor lighting or angle | Use a clear, well-lit frontal photo; check `FRAMES_TO_CONFIRM` setting |
| `OLED FAIL` on Arduino | Wiring issue or wrong I2C address | Check SDA/SCL connections; try address `0x3D` instead of `0x3C` |
| RFID not reading | SPI wiring issue | Double-check all 6 MFRC522 wires, especially MOSI/MISO/SCK |
| Camera lag | CPU overloaded | Increase `VERIFY_EVERY_N` (e.g. from 8 to 15) |
| `pip install deepface` fails | Missing build tools | Install Visual C++ Build Tools (Windows) or `build-essential` (Linux) |
| Servo not moving | Power issue | Servo draws ~200mA peak; power it from 5V pin, not through breadboard rails |

---

## 🔮 Future Improvements

- [ ] **Liveness Detection** — Blink or head-turn detection to prevent photo spoofing
- [ ] **Encrypted RFID** — Use MIFARE authentication instead of plain UID matching
- [ ] **Brute-force Lockout** — Lock keypad after 3 wrong PIN attempts
- [ ] **Multiple Users** — Support multiple RFID UIDs and face profiles with name-tagged logs
- [ ] **Wi-Fi Alerts** — ESP8266/ESP32 integration for push notifications on access events
- [ ] **Access Logging** — Timestamped logs saved to SD card or cloud database
- [ ] **Raspberry Pi Port** — Run the Python side on a Raspberry Pi 4 for a fully standalone system
- [ ] **Mobile App** — BLE or Wi-Fi based temporary access codes via smartphone

---



<div align="center">

Built with ❤️ using Python, Arduino, DeepFace, and OpenCV

**If you found this useful, please ⭐ star the repository!**

</div>
