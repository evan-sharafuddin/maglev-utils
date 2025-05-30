import RPi.GPIO as GPIO

import mcp3008
from pwm import PWM
import time
import csv
import RPi.GPIO as GPIO
import numpy as np

import sys
import os

sys.path.append(os.path.abspath(".."))  # Add previous directory to pat

from filters import Filters

# Initialize ADC
ir_channel = 0
current_channel=2
adc = mcp3008.MCP3008()
pwm_pin = 18
pwm_frequency = 10000
fs = 1000
switch_fs = 15
switch_time = 1/switch_fs
switch_cnt = 10
pwm = 100
max_pwm = 100
min_pwm = 0

# stuff for pausing between bounces 
pause = 0.02
turn_off_time = 0

# set elapsed time
# total_time = 0.02

total_time = 2*switch_cnt/switch_fs + switch_cnt*pause
#total_time = 1

counts = 0
ii = 0

switch = True



#set up PWM
# GPIO.setmode(GPIO.BOARD)
# GPIO.setup(pwm_pin, GPIO.OUT)
# pi_pwm = GPIO.PWM(pwm_pin, pwm_frequency) 
# pi_pwm.start(100)
# time.sleep(2)
pipwm = PWM(pwm_pin, pwm_frequency)
pipwm.set_dc(100)
time.sleep(2)
print("start test")

# Load CSV (skip header if you included one)
data = np.loadtxt('adc_to_position_lookup3.csv', delimiter=',') 
adc_counts = data[:, 0].astype(int)
positions = data[:, 1]

filt_ir = Filters(5)
filt_cur = Filters(5)

# Open a CSV file for writing
with open("./data/bounce_test.csv", "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow([f"PWM frequency of {pwm_frequency}"])
    #writer.writerow(["Time", "PWM", "ADC Reading", "Position", "Current Reading"])
    writer.writerow(["Time", "PWM", "ADC Reading", "Current Reading", "Position"])
    
    t = time.time()
    sample_time = time.time()
    switch_time = time.time()

    while time.time() - t <= total_time:
      
      if time.time() - switch_time > 1/switch_fs:
              # This will alternate between turning the driver on/off every time it samples
        switch_time = time.time()
        
        if switch and time.time() - turn_off_time >pause:
          switch = False
          print("turn off magnet")
          pwm = min_pwm
          pipwm.set_dc(pwm)
        elif not switch:
          switch = True
          print("turn on magnet")
          turn_off_time=time.time()
          pwm = max_pwm
          pipwm.set_dc(pwm)

      if time.time() - sample_time > 1/fs:
        sample_time = time.time()

        current_count = adc.read(current_channel)
        current_count = filt_cur.add_data_mean(current_count)

        ir_count=adc.read(ir_channel)
        ir_count = filt_ir.add_data_mean(ir_count)
        ir_count = int( round(ir_count) ) # convert to integer
        #pos_read = positions[adc_counts == ir_count][0]


        # counts += adc.read(channel)
        # ii += 1
        
        # counts = counts / ii # calculate average counts over the second of data collection

        m = 0.0201
        b = -10.3652
        current = m * current_count + b
        curr_time = (time.time() - t) % 60
        #writer.writerow([curr_time, pwm, ir_count, pos_read, current])
        position = positions[adc_counts == ir_count][0]
        writer.writerow([curr_time, pwm, ir_count, current, position])

        # if pwm % 10 == 0 and pwm != 0:
        #   print(".", flush=True)
        # else:
        #   print(".", end = "", flush=True) 

print("end test")
pipwm.set_dc(100)
time.sleep(1)


