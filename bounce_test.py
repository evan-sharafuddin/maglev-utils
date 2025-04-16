import RPi.GPIO as GPIO

import mcp3008
import time
import csv
import RPi.GPIO as GPIO

import sys
import os

sys.path.append(os.path.abspath(".."))  # Add previous directory to pat

from filters import Filters

# Initialize ADC
ir_channel = 0
curr_channel=1
adc = mcp3008.MCP3008()
pwm_pin = 12
pwm_frequency = 5000
fs = 5000
switch_fs = 35
pwm = 0
max_pwm = 100
min_pwm = 0

# set elapsed time
# total_time = 0.02
total_time = 2/switch_fs
#total_time = 1

counts = 0
ii = 0

switch = False

#set up PWM
GPIO.setmode(GPIO.BOARD)
GPIO.setup(pwm_pin, GPIO.OUT)
pi_pwm = GPIO.PWM(pwm_pin, pwm_frequency) 
pi_pwm.start(0)

filt = Filters(10)

data = np.loadtxt('adc_to_position_lookup.csv', delimiter=',', skiprows=0)  # skiprows=0 if no header

# Open a CSV file for writing
with open("./data/bounce_test.csv", "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow([f"PWM frequency of {pwm_frequency}"])
    writer.writerow(["Time", "PWM", "ADC Reading", "Current Reading"])
    
    t = time.time()
    sample_time = time.time()
    switch_time = time.time()

    while time.time() - t <= total_time:
      
    
      if time.time() - switch_time > 1/switch_fs:
              # This will alternate between turning the driver on/off every time it samples
        switch_time = time.time()
        if switch:
          switch = False
          pwm = min_pwm
          pi_pwm.ChangeDutyCycle(pwm)
        else:
          switch = True
          pwm = max_pwm
          pi_pwm.ChangeDutyCycle(pwm)

      if time.time() - sample_time > 1/fs:
        sample_time = time.time()

        count = adc.read(curr_channel)
        count = filt.add_data_mean_t(count)

        ir_count = adc.read(ir_channel)

        # counts += adc.read(channel)
        # ii += 1
        
        # counts = counts / ii # calculate average counts over the second of data collection

        m = 0.0201
        b = -10.3652
        current = m * count + b
        curr_time = (time.time() - t) % 60;\
        writer.writerow([curr_time, pwm, count, current])

        # if pwm % 10 == 0 and pwm != 0:
        #   print(".", flush=True)
        # else:
        #   print(".", end = "", flush=True) 

GPIO.cleanup()
