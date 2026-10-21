from machine import Pin, PWM
import time

# Shoulder, Elbow, Wrist
servo_pins = [18, 19, 20]
servos = []

for pin in servo_pins:
    pwm = PWM(Pin(pin))
    pwm.freq(50)
    servos.append(pwm)

current = [90, 90, 90]


def set_angle(i, angle):
    angle = max(0, min(180, angle))
    pulse = 500 + angle * 2000 / 180          # 500-2500 us
    servos[i].duty_u16(int(pulse * 65535 / 20000))
    current[i] = angle


def ease(t):
    # Slow start, fast middle, slow stop
    return t * t * (3 - 2 * t)


def move_joint(i, target, duration=1.0, steps=50):
    start = current[i]
    for s in range(1, steps + 1):
        p = s / steps
        set_angle(i, start + (target - start) * ease(p))
        time.sleep(duration / steps)


SHOULDER, ELBOW, WRIST = 0, 1, 2

# Start position
for i in range(3):
    set_angle(i, 90)
time.sleep(1)

while True:
    move_joint(SHOULDER, 120)   # move shoulder
    time.sleep(0.3)

    move_joint(ELBOW, 50)       # move elbow
    time.sleep(0.3)

    move_joint(WRIST, 120)      # move wrist
    time.sleep(0.3)

    move_joint(ELBOW, 90)       # return elbow
    time.sleep(0.3)

    move_joint(SHOULDER, 90)    # return shoulder
    time.sleep(0.3)

    move_joint(WRIST, 90)       # return wrist
    time.sleep(1)