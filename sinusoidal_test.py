import RPi.GPIO as GPIO

import mcp3008
import time
import csv
import RPi.GPIO as GPIO

import sys
import os


import numpy as np
import matplotlib.pyplot as plt

sys.path.append(os.path.abspath(".."))  # Add previous directory to pat

from filters import Filters

# Define parameters
amplitude = 50    # Amplitude of the sine wave
frequency = 1    # Frequency in Hz
phase = 0        # Phase shift in radians
sampling_rate = 100  # Samples per second
duration =  3    # Duration in seconds

# Create a time array
time_vec = np.linspace(0, duration, int(sampling_rate * duration), endpoint=False)

# Generate the sine wave
sine_wave = amplitude * np.sin(2 * np.pi * frequency * time_vec + phase)

# Offset to center at 0
sine_wave += 50



# Initialize ADC
channel = 1
adc = mcp3008.MCP3008()
pwm_pin = 12
pwm_frequency = 5000

#set up PWM
GPIO.setmode(GPIO.BOARD)
GPIO.setup(pwm_pin, GPIO.OUT)
pi_pwm = GPIO.PWM(pwm_pin, pwm_frequency) 
pi_pwm.start(0)

filt = Filters(10)
t = 0 
# Open a CSV file for writing
with open("./data/sinusoidal_test_0.1.csv", "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow([f"PWM frequency of {pwm_frequency}"])
    writer.writerow(["Frequency", "Time", "PWM", "ADC Reading", "Current Reading"])
    
    t = time.time()
    last_time = time.time()
    i = 0

    while time.time() - t < duration and i < len(sine_wave):

      if time.time() - last_time > 1/(frequency * 100):
        last_time = time.time()
        pi_pwm.ChangeDutyCycle(sine_wave[i])

        count = adc.read(channel)
        count = filt.add_data_mean_t(count)

        m = 0.0201
        b = -10.3652
        current = m * count + b
        curr_time = (time.time() - t) % 60;
        writer.writerow([curr_time, sine_wave[i], count, current])

        i += 1

GPIO.cleanup()
