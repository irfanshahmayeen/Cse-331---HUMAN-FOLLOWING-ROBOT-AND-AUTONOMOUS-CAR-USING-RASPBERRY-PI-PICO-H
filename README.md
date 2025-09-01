# Human-Following Robot & Autonomous Cart (Raspberry Pi Pico H)

[![YouTube Demo](https://img.shields.io/badge/YouTube-Demo-red.svg)](https://youtu.be/7tj5DYpUOXI?si=-CWaPK44fme6uQhk)
[![Platform](https://img.shields.io/badge/MCU-Raspberry%20Pi%20Pico%20H-00979D.svg)](#)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](#license)

A low-cost robot car that **follows a person/object** and **avoids obstacles** using ultrasonic sensing and simple reactive control on the Raspberry Pi Pico H. Optional Bluetooth control via a mobile app (HC-05/HC-06) lets you **start/stop**, **drive manually**, and **query telemetry** (distance, direction). :contentReference[oaicite:0]{index=0}

> 📄 The repo accompanies the project report with block/circuit diagrams and component notes (see **Figures** and sections cited in the PDF).

---

## Table of Contents

- [Features](#features)
- [Demo](#demo)
- [Hardware](#hardware)
- [Wiring Overview](#wiring-overview)
- [Firmware (MicroPython)](#firmware-micropython)
- [Bluetooth Commands](#bluetooth-commands)
- [Setup](#setup)
- [How It Works](#how-it-works)
- [Mobile App](#mobile-app)
- [Limitations & Future Work](#limitations--future-work)
- [Troubleshooting](#troubleshooting)
- [Figures (from report)](#figures-from-report)
- [License](#license)
- [Citation](#citation)

---

## Features

- Ultrasonic **distance keeping** and **object following**
- **Obstacle avoidance** with reverse & reorient behavior
- **Bluetooth** remote: start/stop, manual drive, distance/direction queries
- **Four DC motors** driven by dual H-bridge drivers (L298N/L293D)
- Simple **reactive control** (no ML/CV required)

References: Methodology, mobile app protocol, and limitations summarized from the project report. :contentReference[oaicite:1]{index=1}

---

## Demo

▶️ **Video:** https://youtu.be/7tj5DYpUOXI?si=-CWaPK44fme6uQhk

---

## Hardware

- **MCU:** Raspberry Pi Pico H (RP2040)
- **Motors:** 4× TT geared DC motors (differential drive)
- **Motor Drivers:** 2× L298N (or 2× L293D)
- **Distance Sensor:** HC-SR04 ultrasonic
- **(Optional) Scanner:** SG90 micro servo (for sensor sweep)
- **Bluetooth:** HC-05 or HC-06 (UART)
- **Power:** 2× 18650 Li-ion packs (≈7.4 V) + 5 V/3.3 V regulation
- **Misc:** Breadboard, jumpers, switch, battery holders

Component behavior and specs are outlined in the report’s component section (Pico I/O, SG90 timing, HC-SR04 timing, L298N pins). :contentReference[oaicite:2]{index=2}

---

## Wiring Overview

> **Note:** Exact GPIO choices are flexible. Keep **common GND** between logic, drivers, sensors, and Bluetooth.

**Suggested pin map (edit as needed):**

| Module        | Signal             | Pico Pin (example) |
|---------------|--------------------|--------------------|
| HC-SR04       | TRIG               | GP3                |
| HC-SR04       | ECHO               | GP2                |
| SG90 (servo)  | PWM signal         | GP4                |
| Driver A      | IN1, IN2, ENA(PWM) | GP6, GP7, GP5      |
| Driver B      | IN3, IN4, ENB(PWM) | GP9, GP10, GP8     |
| Bluetooth     | TXD → Pico RX      | GP1 (UART0 RX)     |
| Bluetooth     | RXD ← Pico TX      | GP0 (UART0 TX)     |
| Power         | 7.4 V → drivers    | VIN of L298N       |
| Logic         | 5 V/3.3 V → Pico   | VBUS/VSYS & 3V3    |

- Drive **ENA/ENB** with PWM for speed control; **INx** set direction. (Driver details in report). :contentReference[oaicite:3]{index=3}
- For HC-SR04: 10 µs pulse on **TRIG**, measure pulse width on **ECHO** and convert to distance. :contentReference[oaicite:4]{index=4}

---

## Firmware (MicroPython)

> Works with **MicroPython** on Pico (flash via **Thonny**). The logic implements **scan → decide → move** loop (see flowchart in report). :contentReference[oaicite:5]{index=5}

Create `main.py`:

```python
# main.py — Human-Following Robot (Pico H + HC-SR04 + L298N + HC-05/06)
# Adjust GPIO numbers to match your wiring.

from machine import Pin, PWM, UART
import time

# ====== Config ======
TARGET_CM      = 50         # desired following distance (cm)
TOLERANCE_CM   = 10         # acceptable +/- range
FOLLOW_DUTY    = 50000      # motor speed (0-65535)
TURN_DUTY      = 45000
SCAN_USE_SERVO = True

# Pins (edit to match Wiring Overview)
TRIG = Pin(3, Pin.OUT)
ECHO = Pin(2, Pin.IN)

servo = PWM(Pin(4)) if SCAN_USE_SERVO else None
if servo:
    servo.freq(50)

# Motor A
ENA = PWM(Pin(5)); ENA.freq(1000)
IN1 = Pin(6, Pin.OUT); IN2 = Pin(7, Pin.OUT)
# Motor B
ENB = PWM(Pin(8)); ENB.freq(1000)
IN3 = Pin(9, Pin.OUT); IN4 = Pin(10, Pin.OUT)

# Bluetooth UART (HC-05/06 default 9600)
uart = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))

# ====== Helpers ======
def set_servo_us(us):
    # 1000us ~ 0°, 1500us ~ 90°, 2000us ~ 180°
    if not servo: return
    duty = int((us/20000.0) * 65535)
    servo.duty_u16(duty)

def angle_to_us(deg):
    return 1000 + int((deg/180.0)*1000)

def pulse_in(pin, level, timeout_us=30000):
    t0 = time.ticks_us()
    while pin.value() != level:
        if time.ticks_diff(time.ticks_us(), t0) > timeout_us:
            return 0
    t1 = time.ticks_us()
    while pin.value() == level:
        if time.ticks_diff(time.ticks_us(), t0) > timeout_us:
            return 0
    return time.ticks_diff(time.ticks_us(), t1)

def read_distance_cm():
    TRIG.low(); time.sleep_us(2)
    TRIG.high(); time.sleep_us(10)
    TRIG.low()
    dur = pulse_in(ECHO, 1, timeout_us=40000)
    if dur == 0: return 999
    # speed of sound ~343 m/s => cm = (us * 0.0343)/2
    return (dur * 0.0343) / 2

def motors_stop():
    ENA.duty_u16(0); ENB.duty_u16(0)
    IN1.low(); IN2.low(); IN3.low(); IN4.low()

def motors_forward(duty):
    IN1.high(); IN2.low()
    IN3.high(); IN4.low()
    ENA.duty_u16(duty); ENB.duty_u16(duty)

def motors_backward(duty):
    IN1.low(); IN2.high()
    IN3.low(); IN4.high()
    ENA.duty_u16(duty); ENB.duty_u16(duty)

def turn_left(duty):
    IN1.low(); IN2.high()
    IN3.high(); IN4.low()
    ENA.duty_u16(duty); ENB.duty_u16(duty)

def turn_right(duty):
    IN1.high(); IN2.low()
    IN3.low(); IN4.high()
    ENA.duty_u16(duty); ENB.duty_u16(duty)

def scan_distances():
    if not servo:
        return {"center": read_distance_cm()}
    readings = {}
    for label, ang in [("left", 150), ("center", 90), ("right", 30)]:
        set_servo_us(angle_to_us(ang)); time.sleep_ms(250)
        readings[label] = read_distance_cm()
    return readings

def closest_direction(readings):
    # returns "left"/"center"/"right" by smallest distance
    return min(readings, key=lambda k: readings[k])

# ====== Bluetooth ======
def bt_send(msg):
    try:
        uart.write((msg + "\n").encode())
    except:
        pass

def handle_bt(cmd):
    cmd = cmd.strip().upper()
    if cmd == "START":
        bt_send("OK START")
        return "START"
    if cmd == "STOP":
        motors_stop(); bt_send("OK STOP")
        return "STOP"
    if cmd in ("LEFT","RIGHT","FWD","REV"):
        bt_send("OK " + cmd)
        return cmd
    if cmd == "DIST?":
        bt_send(f"DIST {int(read_distance_cm())}cm")
    if cmd == "DIR?":
        bt_send("DIR FOLLOW")
    return None

# ====== Main Loop ======
state = "STOP"
bt_send("READY")

try:
    while True:
        # read BT
        if uart.any():
            msg = uart.readline().decode(errors="ignore")
            act = handle_bt(msg)
            if act: state = act

        if state == "STOP":
            motors_stop()
            time.sleep_ms(50)
            continue

        # Manual overrides
        if state == "LEFT":  turn_left(TURN_DUTY);  time.sleep_ms(100); continue
        if state == "RIGHT": turn_right(TURN_DUTY); time.sleep_ms(100); continue
        if state == "FWD":   motors_forward(FOLLOW_DUTY); time.sleep_ms(100); continue
        if state == "REV":   motors_backward(FOLLOW_DUTY); time.sleep_ms(100); continue

        # Autonomous follow
        r = scan_distances()
        dirn = closest_direction(r)
        if dirn == "left":   turn_left(TURN_DUTY);  time.sleep_ms(120); continue
        if dirn == "right":  turn_right(TURN_DUTY); time.sleep_ms(120); continue

        dist = r.get("center", read_distance_cm())

        if dist < (TARGET_CM - TOLERANCE_CM):
            motors_backward(FOLLOW_DUTY)
        elif dist > (TARGET_CM + TOLERANCE_CM) and dist < 300:
            motors_forward(FOLLOW_DUTY)
        else:
            motors_stop()

        time.sleep_ms(60)

except KeyboardInterrupt:
    motors_stop()
