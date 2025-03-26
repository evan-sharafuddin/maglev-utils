# Use this file to plot a curve for "charging" the inductor to see how long 
# it takes to switch currents

import RPi.GPIO as GPIO

import mcp3008
import time
import csv
import RPi.GPIO as GPIO

# Initialize ADC
channel = 1
adc = mcp3008.MCP3008()
pwm_pin = 12
pwm_frequency = 5000

total_time = 0.1 
on_time = 0.001

# set up PWM
GPIO.setmode(GPIO.BOARD)
GPIO.setup(pwm_pin, GPIO.OUT)
pi_pwm = GPIO.PWM(pwm_pin, 5000) 
pi_pwm.start(0)

pwm = 0
# Open a CSV file for writing
with open("inductor_charging_test.csv", "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow([f"PWM frequency of {pwm_frequency}"])
    writer.writerow(["PWM", "ADC Reading", "Current Reading"])

    t = time.time()
    while time.time() - t < total_time:
        count = adc.read(channel)
        
        if time.time() - t >= on_time:
            pi_pwm.ChangeDutyCycle(100)
            pwm = 100

        m = 0.0201
        b = -10.3652
        current = m * count + b
        writer.writerow([time.time(), count, current])

GPIO.cleanup()
