from machine import Pin, PWM, time_pulse_us
import time

# ---- Pins ----
STEP = Pin(3, Pin.OUT)     # GP3 -> A4988 STEP
DIR = Pin(2, Pin.OUT)      # GP2 -> A4988 DIR
TRIG = Pin(4, Pin.OUT)     # GP4 -> HC-SR04 TRIG
ECHO = Pin(5, Pin.IN)      # GP5 -> HC-SR04 ECHO

servo = PWM(Pin(19))       # GP19 -> servo signal
servo.freq(50)

# ---- Rail settings ----
STEPS_PER_REV = 200
MM_PER_REV = 40
RAIL_MM = 1000
TOTAL_STEPS = int(RAIL_MM / MM_PER_REV * STEPS_PER_REV)   # 5000 steps

# ---- Speed settings (microseconds per half-pulse) ----
FAST_US = 400
SLOW_US = 2000
RAMP_STEPS = 500

TO_END = 1
TO_START = 0

# ---- Sensor settings ----
STOP_DISTANCE_CM = 5       # object at 5 cm or closer triggers a return
CHECK_EVERY = 50           # measure distance every N steps while moving to the end

# ---- Servo settings ----
SERVO_START = 0            # starting position (degrees)
SERVO_END = 180            # position when the carriage is at the end of the rail

position = 0               # carriage position in steps (0 = start)
servo_angle = SERVO_START  # current servo angle


# =========================================================
#  SERVO FUNCTIONS
# =========================================================
def set_angle(angle):
    global servo_angle
    angle = max(0, min(180, angle))
    pulse = 500 + angle * 2000 / 180          # 500-2500 us
    servo.duty_u16(int(pulse * 65535 / 20000))
    servo_angle = angle


def ease(t):
    # Slow start, fast middle, slow stop
    return t * t * (3 - 2 * t)


def move_servo(target, duration=1.5, steps=60):
    start = servo_angle
    for s in range(1, steps + 1):
        p = s / steps
        set_angle(start + (target - start) * ease(p))
        time.sleep(duration / steps)


# =========================================================
#  SENSOR FUNCTIONS
# =========================================================
def distance_cm():
    TRIG.value(0)
    time.sleep_us(2)
    TRIG.value(1)
    time.sleep_us(10)
    TRIG.value(0)
    t = time_pulse_us(ECHO, 1, 25000)
    if t < 0:
        return None            # no echo = nothing in range
    return t * 0.0343 / 2


def object_too_close():
    d = distance_cm()
    if d is None:
        return False
    d = round(d)               # round to the nearest cm
    if d <= STOP_DISTANCE_CM:  # 5 cm or closer
        print("Object detected at", d, "cm")
        return True
    return False


# =========================================================
#  CARRIAGE FUNCTION
# =========================================================
def move(steps, direction, watch=False):
    """Move the carriage. Returns True if an object stopped it (only when watch=True)."""
    global position
    DIR.value(direction)
    time.sleep_us(10)
    done = 0
    blocked = False

    for n in range(steps):
        if watch and n % CHECK_EVERY == 0:
            if object_too_close():
                blocked = True
                break

        edge = min(n, steps - 1 - n)
        if edge < RAMP_STEPS:
            delay = SLOW_US - (SLOW_US - FAST_US) * edge // RAMP_STEPS
        else:
            delay = FAST_US

        STEP.value(1)
        time.sleep_us(delay)
        STEP.value(0)
        time.sleep_us(delay)
        done += 1

    position += done if direction == TO_END else -done
    return blocked


# =========================================================
#  START
# =========================================================
set_angle(SERVO_START)
time.sleep(1)
print("Rail length:", RAIL_MM, "mm =", TOTAL_STEPS, "steps")

while True:
    print("Moving to the end of the rail...")
    blocked = move(TOTAL_STEPS, TO_END, watch=True)

    if blocked:
        print("Going back to the start...")
        move(position, TO_START)
        print("At start. Trying again in 2 seconds.")
        time.sleep(2)
        continue                # try the full run again

    print("Reached the end. Turning servo to", SERVO_END, "degrees")
    move_servo(SERVO_END)
    time.sleep(1)

    print("Returning to the start...")
    move(position, TO_START)

    print("At start. Servo going back to", SERVO_START, "degrees")
    move_servo(SERVO_START)
    time.sleep(1)