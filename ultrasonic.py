# Based on: https://thepihut.com/blogs/raspberry-pi-tutorials/hc-sr04-ultrasonic-range-sensor-on-the-raspberry-pi?srsltid=AfmBOorKEB1Seq2N5XPj66vJ0VT5_9Zyf4AtCD02njbdEHrXAn0SG5pn
# Datasheet: https://cdn.sparkfun.com/datasheets/Sensors/Proximity/HCSR04.pdf

import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BOARD)

TRIG = 40
ECHO = 38

GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

GPIO.output(TRIG, False)

time.sleep(0.1)

print("Send pulse")
GPIO.output(TRIG, True)
time.sleep(0.00001)
GPIO.output(TRIG, False)

print("Wait for echo")

while GPIO.input(ECHO) == 0:
    pulse_start = time.time()
while GPIO.input(ECHO) == 1:
    pulse_end = time.time()


pulse_duration = pulse_end - pulse_start
distance = pulse_duration * 17150
distance = round(distance, 2)

print(f"Distance: {distance} cm")

GPIO.cleanup()
