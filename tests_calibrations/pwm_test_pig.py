import RPi.GPIO as GPIO
import atexit
import pigpio

pwm_pin = 12
pwm_frequency = 5000
pwm_dc = 50

pi = pigpio.pi()
pi.set_PWM_frequency(17, 1000)  # Set frequency to 1kHz

while True:
    pass

