import RPi.GPIO as GPIO

import sys
import os
sys.path.append(os.path.abspath(".."))

import mcp3008
import time
import csv
import RPi.GPIO as GPIO


# Initialize ADC
channel = 1
adc = mcp3008.MCP3008()
pwm_pin = 12
pwm_frequency = 500 # anything above 1000 is dicey...
avg_time = 0.1

# set start and stop
start = 0
stop  = 100
incr = 1

#set up PWM
GPIO.setmode(GPIO.BOARD)
GPIO.setup(pwm_pin, GPIO.OUT)
pi_pwm = GPIO.PWM(pwm_pin, pwm_frequency) 
pi_pwm.start(0)

# Open a CSV file for writing
with open("pwm_to_i_test.csv", "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow([f"PWM frequency of {pwm_frequency}"])
    writer.writerow(["PWM", "ADC Reading", "Current Reading"])

    pwm = start
    while pwm <= stop:
        
        pi_pwm.ChangeDutyCycle(pwm)
        
        counts = 0
        ii = 0
        t = time.time()

        while time.time() - t < avg_time:
            counts += adc.read(channel)
            ii += 1

        counts = counts / ii # calculate average counts over the second of data collection

        m = 0.0201
        b = -10.3652
        current = m * counts + b
        writer.writerow([pwm, counts, current])

        if pwm % 10 == 0 and pwm != 0:
            print(".", flush=True)
        else:
            print(".", end = "", flush=True)
        
        pwm += incr

GPIO.cleanup()
