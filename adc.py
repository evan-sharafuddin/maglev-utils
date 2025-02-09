# based off of https://learn.sparkfun.com/tutorials/raspberry-pi-spi-and-i2c-tutorial/all

import time
import spidev
import matplotlib.pyplot as plt
import numpy as np
import RPi.GPIO as GPIO

# GPIO.cleanup()

bus = 0
device = 0 # CE0

spi = spidev.SpiDev()

spi.open(device, bus) 
# spi.max_speed_hz = int( 1.35e6 ) # for 3.3V Vdd operation
spi.max_speed_hz = int( 3.6e6 ) # for 5V Vdd operation
spi.mode = 0


def readadc(adcnum):  # read out the ADC
    # check that our channel number is between 0 and 7
    if ((adcnum > 7) or (adcnum < 0)):
        return -1
    
    r = spi.xfer2([1, (8 + adcnum) << 4, 0])
    adcout = ((r[1] & 3) << 8) + r[2]


    return adcout

# https://forums.raspberrypi.com/viewtopic.php?t=272035

tic = time.time()
arr = np.zeros(100000)
c = 0

# GPIO.setmode(GPIO.BOARD)
# pin = 40
# GPIO.setup(pin, GPIO.OUT)
# ison = False
# GPIO.output(pin, 1)

while c < 100000:
    # if c % 10000 == 0:
    #     GPIO.output(pin, 0 if ison else 1)
    #     ison = not ison

    arr[c] = readadc(1)
    c += 1

toc = time.time()
# GPIO.output(pin, 0)

print(f"Total time: {toc-tic}")

plt.plot(arr)
plt.savefig("test.png")

# GPIO.cleanup()
