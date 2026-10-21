from machine import Pin, ADC, I2C
import time

# ---------- Pins ----------
soil = ADC(Pin(26))
relay = Pin(14, Pin.OUT)
dry_led = Pin(15, Pin.OUT)
moist_led = Pin(16, Pin.OUT)

DRY_THRESHOLD = 40000
WATERING_TIME = 10

# ---------- I2C LCD (PCF8574 backpack, SDA=GP0, SCL=GP1) ----------
i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=100000)
devices = i2c.scan()
lcd_ok = len(devices) > 0
LCD_ADDR = devices[0] if lcd_ok else None

BACKLIGHT = 0x08
ENABLE = 0x04


def lcd_nibble(nibble, rs):
    value = (nibble & 0xF0) | rs | BACKLIGHT
    i2c.writeto(LCD_ADDR, bytes([value | ENABLE]))
    time.sleep_us(2)
    i2c.writeto(LCD_ADDR, bytes([value]))
    time.sleep_us(60)


def lcd_write(data, rs):
    lcd_nibble(data & 0xF0, rs)
    lcd_nibble((data << 4) & 0xF0, rs)


def lcd_command(cmd):
    lcd_write(cmd, 0)
    time.sleep_ms(2)


def lcd_init():
    time.sleep_ms(50)
    lcd_nibble(0x30, 0)
    time.sleep_ms(5)
    lcd_nibble(0x30, 0)
    time.sleep_ms(5)
    lcd_nibble(0x30, 0)
    time.sleep_ms(1)
    lcd_nibble(0x20, 0)   # 4-bit mode
    time.sleep_ms(1)
    for cmd in (0x28, 0x0C, 0x06, 0x01):
        lcd_command(cmd)
    time.sleep_ms(2)


def lcd_line(row, text):
    lcd_command(0x80 if row == 0 else 0xC0)
    text = text[:16]
    text = text + " " * (16 - len(text))
    for char in text:
        lcd_write(ord(char), 1)


def show(line1, line2=""):
    # Safe: does nothing if the LCD isn't connected
    if lcd_ok:
        lcd_line(0, line1)
        lcd_line(1, line2)


# ---------- Startup ----------
relay.off()
dry_led.off()
moist_led.off()

if lcd_ok:
    print("LCD found at address:", hex(LCD_ADDR))
    lcd_init()
else:
    print("LCD NOT found - check SDA (GP0) and SCL (GP1)")

show("Smart Watering", "System Ready")
time.sleep(2)

# ---------- Main loop ----------
while True:
    raw = soil.read_u16()
    moisture = 100 - int(raw * 100 / 65535)

    print("Soil reading:", raw)
    print("Moisture:", moisture, "%")

    if raw > DRY_THRESHOLD:
        print("Soil is DRY - watering for", WATERING_TIME, "seconds")

        dry_led.on()
        moist_led.off()
        relay.on()

        for remaining in range(WATERING_TIME, 0, -1):
            show("Soil: DRY {}%".format(moisture),
                 "Pump ON {}s".format(remaining))
            time.sleep(1)

        relay.off()
        dry_led.off()

        print("Watering complete - pump OFF")
        print("Checking soil again...")
        show("Watering done", "Checking soil...")
        time.sleep(2)

    else:
        print("Soil is MOIST - pump OFF")

        relay.off()
        dry_led.off()
        moist_led.on()

        show("Soil: MOIST {}%".format(moisture), "Pump: OFF")
        time.sleep(2)