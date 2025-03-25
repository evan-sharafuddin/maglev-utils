import RPi.GPIO as GPIO

import mcp3008
import time
import csv
import RPi.GPIO as GPIO

# Initialize ADC
channel = 6
adc = mcp3008.MCP3008()
pwm_pin = 12

#set up PWM
GPIO.setmode(GPIO.BOARD)
GPIO.setup(pwm_pin, GPIO.OUT)
pi_pwm = GPIO.PWM(pwm_pin, 20000)
pi_pwm.start(0)
pwm_bool=0
start_time=time.time()
i = 0




# Open a CSV file for writing
with open("no_pwm.csv", "w", newline="") as file:
  writer = csv.writer(file)
  writer.writerow(["PWM", "Current Timestamp", "ADC Reading", "Timestamp at last Change"])
    
  while i < 10 :
    reading = adc.read(channel)
    timestamp = time.time()
    writer.writerow([pwm_bool*100, timestamp, reading, start_time])
    if start_time + 0.5 < time.time():
      start_time=time.time()
      #pwm_bool = not pwm_bool
      pi_pwm.ChangeDutyCycle(pwm_bool*100)
      i += 1

GPIO.cleanup()
