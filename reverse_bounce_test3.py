# adding functionality to the test that ramps pwm down instead of cutting it off completely

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
fs = 1000 # data sampling rate

period = 0.215 # number of seconds that cycle will complete
off_time = period / 2 # time that the magnet is off
pwm_step_time = off_time / 100 # time between stepping down the pwm
pwm_step_size = 1 # step down size for the pwm

on_time = period - off_time
if on_time < 0: 
   print("ERROR: off time must be smaller than period, aborting")
   sys.exit()

switch_cnt = 8
pwm = 100
max_pwm = 100
min_pwm = 0

total_time = switch_cnt * period # add some extra time buffer for any latency

counts = 0
ii = 0

switch = True

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
    # writer.writerow([f"PWM frequency of {pwm_frequency}"])
    writer.writerow(["Time", "PWM", "ADC Reading", "Current Reading", "Position"])
    
    t = time.time()
    sample_time = time.time()
    
    s_off_time = time.time()
    s_on_time = time.time()
    s_pwm_step_time = time.time() 
    is_on = False # have it turn on first

    while time.time() - t <= total_time:
      
      if not is_on and time.time() - s_off_time >= off_time: # time to switch on  
        is_on = not is_on # true
        s_on_time = time.time()

      elif is_on and time.time() - s_on_time >= on_time: # time to switch off
        is_on = not is_on # false
        s_off_time = time.time()
      
      # do on or off stuff
      if is_on:
        # if pwm != max_pwm:
        #   pwm = max_pwm 
        #   pipwm.set_dc(pwm)
        if time.time() - s_pwm_step_time > pwm_step_time:
          s_pwm_step_time = time.time()
          pwm += pwm_step_size
          if pwm > max_pwm: pwm = max_pwm # don't allow negative pwm!
          pipwm.set_dc(pwm)
        # else, don't need to do anything
      
      else: # is_off
        if time.time() - s_pwm_step_time > pwm_step_time:
          s_pwm_step_time = time.time()
          pwm -= pwm_step_size
          if pwm < min_pwm: pwm = min_pwm # don't allow negative pwm!
          pipwm.set_dc(pwm)


      # sampling code
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

print("end test -- dropping!")
pipwm.set_dc(100)
time.sleep(0.5)


