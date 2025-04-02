import RPi.GPIO as GPIO
import atexit
import time

pwm_pin = 12
pwm_frequency = 20000
pwm_dc = 99

GPIO.setmode(GPIO.BOARD)
GPIO.setup(pwm_pin, GPIO.OUT)
pi_pwm = GPIO.PWM(pwm_pin, pwm_frequency) 
pi_pwm.start(pwm_dc)

# Define an exit handler
def cleanup_gpio():
    print("Cleaning up GPIO...")
    GPIO.cleanup()

# Register the exit handler
atexit.register(cleanup_gpio)

#while True: pass

pi_pwm.ChangeDutyCycle(0)
time.sleep(2.5)
pi_pwm.ChangeDutyCycle(1)
time.sleep(2.5)
pi_pwm.ChangeDutyCycle(99)
time.sleep(2.5)
pi_pwm.ChangeDutyCycle(100)
time.sleep(2.5)                       

dc = 0
while True:
    pi_pwm.ChangeDutyCycle(dc)
    dc += 1
    print(dc)
    time.sleep(0.1)
    if abs(dc - 100) < 1e-4: dc = 0
    

