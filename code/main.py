# ============================================================
# Smart Motion-Activated Power Management System
# With Blynk IoT Integration
# Raspberry Pi Pico 2W - MicroPython
# ============================================================
# Blynk Virtual Pins:
#   V0 = Voltage (V)
#   V1 = Current (A)
#   V2 = Power (W)
#   V3 = Energy (Wh)
#   V4 = Motion Status (0/1)
#   V5 = Bulb Status (0/1)
# ============================================================

import machine
import utime
import math
import network
import urequests
import gc
from machine import Pin, ADC, I2C

# ─────────────────────────────────────────
# WiFi & BLYNK CONFIG
# ─────────────────────────────────────────
WIFI_SSID     = "ASSESSMENT_SNPSU"
WIFI_PASSWORD = "SNPSU@123"
BLYNK_TOKEN   = "4HY0bKEWg60z_8ryQDae1ojRQJnIEV0K"
BLYNK_URL     = "http://blynk.cloud/external/api/batch/update"
ALERT_URL     = "http://blynk.cloud/external/api/notify"

# ─────────────────────────────────────────
# PIN CONFIGURATION
# ─────────────────────────────────────────
PIR_PIN    = 15
RELAY_PIN  = 14
BUZZER_PIN = 16
BUTTON_PIN = 18
ACS_PIN    = 26   # Current sensor (ACS712)
ZMPT_PIN   = 27   # Voltage sensor (ZMPT101B)
LCD_SDA    = 0
LCD_SCL    = 1

# ─────────────────────────────────────────
# HARDWARE SETUP
# ─────────────────────────────────────────
pir      = Pin(PIR_PIN, Pin.IN)
relay    = Pin(RELAY_PIN, Pin.OUT)
buzzer   = Pin(BUZZER_PIN, Pin.OUT)
button   = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)
acs_adc  = ADC(Pin(ACS_PIN))
zmpt_adc = ADC(Pin(ZMPT_PIN))

relay.value(1)   # Relay OFF at startup (active-low)
buzzer.value(0)

# ─────────────────────────────────────────
# STATE VARIABLES
# ─────────────────────────────────────────
bulb_on      = False
manual_mode  = False
total_energy = 0.0
TIMEOUT      = 10   # seconds before auto-off
COOLDOWN     = 8    # seconds after bulb OFF before re-trigger

# ─────────────────────────────────────────
# CURRENT SENSOR CALIBRATION
# ─────────────────────────────────────────
# HOW TO CALIBRATE:
#   1. Run with bulb OFF (relay open). Note the printed RAW value.
#   2. Set ACS_NOISE_OFFSET to that idle value.
#   3. Run with bulb ON. Confirm a non-zero current is shown.
#   4. If your ACS712 zero-current output is 2.5V (5V supply, not divided),
#      change ACS_MIDPOINT_V to 2.5 and ACS_SENSITIVITY to match your module:
#        ACS712-05B → 0.185 V/A
#        ACS712-20A → 0.100 V/A
#        ACS712-30A → 0.066 V/A

ACS_MIDPOINT_V   = 1.65    # Change to 2.5 if sensor powered at 5V without divider
ACS_SENSITIVITY  = 2.00   # V/A  — adjust for your ACS712 variant
ACS_NOISE_OFFSET = 0.0     # Subtract idle noise; measure with bulb OFF and set here
ACS_MIN_CURRENT  = 0.05    # Anything below this (after offset) treated as 0 A

# ─────────────────────────────────────────
# LCD SETUP
# ─────────────────────────────────────────
i2c = I2C(0, sda=Pin(LCD_SDA), scl=Pin(LCD_SCL), freq=100000)
LCD_ADDR      = 0x27
LCD_BACKLIGHT = 0x08
ENABLE        = 0b00000100

def write(data):
    i2c.writeto(LCD_ADDR, bytes([data | LCD_BACKLIGHT]))
    utime.sleep_us(200)

def pulse(data):
    write(data | ENABLE)
    utime.sleep_us(600)
    write(data & ~ENABLE)
    utime.sleep_us(600)

def nibble(data):
    write(data)
    pulse(data)

def send(data, mode=0):
    nibble((data & 0xF0) | mode)
    nibble(((data << 4) & 0xF0) | mode)

def lcd_init():
    utime.sleep_ms(100)
    for v in [0x30, 0x30, 0x30, 0x20]:
        nibble(v)
        utime.sleep_ms(10)
    for cmd in [0x28, 0x0C, 0x06, 0x01]:
        send(cmd)
        utime.sleep_ms(10)

def lcd_show(line1, line2=""):
    send(0x01)
    utime.sleep_ms(10)
    send(0x80)
    for c in line1[:16]:
        send(ord(c), 1)
    send(0xC0)
    for c in line2[:16]:
        send(ord(c), 1)

def lcd_off():
    send(0x08)

# ─────────────────────────────────────────
# WiFi CONNECT
# ─────────────────────────────────────────
def connect_wifi():
    lcd_show("Connecting WiFi", "Please wait...")
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    for _ in range(20):
        if wlan.isconnected():
            ip = wlan.ifconfig()[0]
            print("WiFi connected:", ip)
            lcd_show("WiFi Connected!", ip[:16])
            utime.sleep_ms(2000)
            return True
        utime.sleep_ms(1000)
    print("WiFi failed")
    lcd_show("WiFi Failed!   ", "Offline Mode   ")
    utime.sleep_ms(2000)
    return False

def ensure_wifi():
    wlan = network.WLAN(network.STA_IF)
    if not wlan.isconnected():
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        utime.sleep_ms(3000)

# ─────────────────────────────────────────
# BLYNK SEND
# ─────────────────────────────────────────
def blynk_send(volts, amps, watts, energy, motion, bulb):
    try:
        ensure_wifi()
        url = (
            "{}?token={}"
            "&V0={:.1f}&V1={:.2f}&V2={:.1f}"
            "&V3={:.4f}&V4={}&V5={}"
        ).format(
            BLYNK_URL, BLYNK_TOKEN,
            volts, amps, watts,
            energy, motion, bulb
        )
        r = urequests.get(url, timeout=5)
        r.close()
        gc.collect()
        print("Blynk updated")
    except Exception as e:
        print("Blynk error:", e)

def blynk_alert(msg):
    # NOTE: Blynk free tier /notify endpoint often returns ECONNRESET.
    # This is expected — silently ignore connection errors.
    try:
        ensure_wifi()
        url = "{}?token={}&message={}".format(
            ALERT_URL, BLYNK_TOKEN, msg
        )
        r = urequests.get(url, timeout=5)
        r.close()
        gc.collect()
    except Exception:
        pass  # Notify not supported on free tier — suppress error

# ─────────────────────────────────────────
# PIR DEBOUNCE (strict - for initial trigger)
# ─────────────────────────────────────────
def pir_confirmed():
    count = 0
    for _ in range(10):
        if pir.value() == 1:
            count += 1
        utime.sleep_ms(50)
    return count >= 8

# ─────────────────────────────────────────
# PIR ACTIVE CHECK (less strict - to keep bulb ON)
# ─────────────────────────────────────────
def pir_active():
    """Multi-sample PIR check used while bulb is ON.
    Samples 5 times over 500ms — less strict than pir_confirmed()
    but more reliable than a single read."""
    count = 0
    for _ in range(5):
        if pir.value() == 1:
            count += 1
        utime.sleep_ms(100)
    return count >= 2   # 2 out of 5 is enough to stay ON

# ─────────────────────────────────────────
# BUTTON DEBOUNCE
# ─────────────────────────────────────────
def button_pressed():
    if button.value() == 0:
        utime.sleep_ms(50)
        if button.value() == 0:
            while button.value() == 0:
                utime.sleep_ms(10)
            return True
    return False

# ─────────────────────────────────────────
# CURRENT SENSOR (ACS712)
# FIX: Calibrated noise floor instead of hard-coded 5.5A offset.
#      Print raw value so you can tune ACS_NOISE_OFFSET at the top.
# ─────────────────────────────────────────
def read_current():
    samples = []
    for _ in range(200):
        samples.append(acs_adc.read_u16())
        utime.sleep_us(100)

    avg            = sum(samples) / len(samples)
    adc_voltage    = (avg / 65535) * 3.3
    raw_current    = abs((adc_voltage - ACS_MIDPOINT_V) / ACS_SENSITIVITY)

    # Debug print — comment out after calibration

    corrected = raw_current - ACS_NOISE_OFFSET
    return round(corrected, 2) if corrected > ACS_MIN_CURRENT else 0.0

# ─────────────────────────────────────────
# VOLTAGE SENSOR (ZMPT101B)
# ─────────────────────────────────────────
def read_voltage():
    samples = []
    for _ in range(200):
        raw      = zmpt_adc.read_u16()
        voltage  = (raw / 65535) * 3.3
        centered = voltage - 1.65
        samples.append(centered ** 2)
        utime.sleep_us(100)
    rms_raw     = math.sqrt(sum(samples) / len(samples))
    calibration = 23000
    voltage_rms = rms_raw * calibration
    result      = round(min(voltage_rms, 260), 1)
    return result if result > 5.0 else 0.0

def calc_power(v, a):
    return round(v * a, 2)

# ─────────────────────────────────────────
# BEEP
# ─────────────────────────────────────────
def beep(times=1, ms=1000):
    for _ in range(times):
        buzzer.value(1)
        utime.sleep_ms(ms)
        buzzer.value(0)
        utime.sleep_ms(100)

# ─────────────────────────────────────────
# BULB CONTROL
# ─────────────────────────────────────────
def bulb_turn_on(reason="motion"):
    global bulb_on
    bulb_on = True
    relay.value(0)   # Active-low: 0 = relay ON
    beep(2, 150)
    lcd_init()
    if reason == "motion":
        lcd_show("MOTION DETECTED!", "  Bulb ON  [A]  ")
        blynk_send(0, 0, 0, total_energy, 1, 1)
        blynk_alert("Motion Detected! Bulb ON")
    else:
        lcd_show(" Manual Override", "  Bulb ON  [M]  ")
        blynk_send(0, 0, 0, total_energy, 0, 1)
    print("Bulb ON -", reason)

def bulb_turn_off(session_energy):
    global bulb_on, manual_mode
    bulb_on     = False
    manual_mode = False
    relay.value(1)   # Active-low: 1 = relay OFF
    buzzer.value(0)
    lcd_show("  Bulb OFF!    ", "Saved:{:.4f}Wh".format(session_energy))
    blynk_send(0, 0, 0, total_energy, 0, 0)
    print("Bulb OFF | Saved: {:.4f}Wh".format(session_energy))
    utime.sleep_ms(2000)

# ─────────────────────────────────────────
# WAIT FOR TRIGGER (light sleep)
# ─────────────────────────────────────────
def wait_for_trigger():
    lcd_show(" System Ready  ", "Btn=Manual ON  ")
    utime.sleep_ms(1000)
    lcd_off()
    blynk_send(0, 0, 0, total_energy, 0, 0)
    print("Waiting for motion or button...")

    while True:
        machine.lightsleep(100)
        if button_pressed():
            return "button"
        if pir.value() == 1 and pir_confirmed():
            return "motion"

# ─────────────────────────────────────────
# MAIN MONITORING LOOP
# ─────────────────────────────────────────
def monitor_loop(trigger):
    global total_energy, manual_mode, bulb_on

    manual_mode    = (trigger == "button")
    session_energy = 0.0
    blynk_counter  = 0   # Send to Blynk every 5 seconds

    bulb_turn_on(trigger)
    utime.sleep_ms(3000)   # PIR settle time after relay energises

    # Reset timer AFTER the 3s warmup so PIR has time to settle
    last_motion = utime.time()
    print("Monitor started. Auto-off timer reset.")

    while True:
        # ── Button toggle ──────────────────────────────────────────
        if button_pressed():
            if bulb_on:
                print("Button: Bulb OFF")
                beep(1, 200)
                bulb_turn_off(session_energy)
                total_energy += session_energy
                utime.sleep_ms(COOLDOWN * 1000)
                return
            else:
                manual_mode = True
                bulb_turn_on("button")

        # ── PIR refresh (auto mode only) ───────────────────────────
        if not manual_mode:
            if pir_active():
                last_motion = utime.time()
                print("Motion still active — timer reset")

        # ── Read sensors (only when relay is ON / bulb is ON) ──────
        if relay.value() == 0:
            amps  = read_current()
            volts = read_voltage()
            watts = calc_power(volts, amps)
        else:
            amps  = 0.0
            volts = 0.0
            watts = 0.0

        # ── Energy tracking ────────────────────────────────────────
        session_energy += watts / 3600   # Wh accumulated per second
        total_energy   += watts / 3600

        # ── LCD Display ────────────────────────────────────────────
        line1 = "V:{:.1f}V  A:{:.2f}A".format(volts, amps)
        line2 = "W:{:.1f}W  E:{:.3f}Wh".format(watts, total_energy)
        lcd_show(line1, line2)
        print("V:{:.1f}V  A:{:.2f}A  W:{:.1f}W  E:{:.4f}Wh".format(
            volts, amps, watts, total_energy))

        # ── Blynk update every 5 seconds ──────────────────────────
        blynk_counter += 1
        if blynk_counter >= 5:
            motion_val = 1 if pir.value() == 1 else 0
            bulb_val   = 1 if relay.value() == 0 else 0
            blynk_send(volts, amps, watts, total_energy, motion_val, bulb_val)
            blynk_counter = 0

        # ── Auto timeout (auto mode only) ──────────────────────────
        if not manual_mode:
            if utime.time() - last_motion >= TIMEOUT:
                print("No motion for {}s — auto OFF".format(TIMEOUT))
                bulb_turn_off(session_energy)
                total_energy += session_energy
                utime.sleep_ms(COOLDOWN * 1000)
                return

        gc.collect()
        utime.sleep_ms(1000)

# ─────────────────────────────────────────
# STARTUP
# ─────────────────────────────────────────
lcd_init()
lcd_show(" Smart Motion  ", " Power System  ")
beep(1, 300)
utime.sleep_ms(1000)

wifi_ok = connect_wifi()

print("PIR warming up...")
lcd_show("PIR Warming Up ", "Please wait... ")
utime.sleep_ms(5000)

# ─────────────────────────────────────────
# MAIN LOOP
# ─────────────────────────────────────────
while True:
    trigger = wait_for_trigger()
    monitor_loop(trigger)
