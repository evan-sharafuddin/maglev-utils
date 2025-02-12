# based off of https://learn.sparkfun.com/tutorials/raspberry-pi-spi-and-i2c-tutorial/all

import time
import spidev
import matplotlib.pyplot as plt
import numpy as np
import RPi.GPIO as GPIO


class MCP3008:
    # define constants
    VDD_LO_CLK = 1.35e6 # maximum clock frequency for 3.3V operation
    VDD_HI_CLK = 3.60e6 # maximum clock frequency for 5V operation
    MIN_CLK    = 50e3   # minimum clock frequency of 10 kHz for all Vdd, add a bit of buffer
    
    def __init__( self, Vdd_hi=False, bus=0, device=0, debug=False):
        self.spi = spidev.SpiDev()
        self.spi.open(device, bus)
        self.spi.max_speed_hz = int( MCP3008.VDD_HI_CLK if Vdd_hi \
                                     else MCP3008.VDD_LO_CLK      ) # for 5V Vdd operation
        self.spi.mode = 0

    def read( self, chan ):
        # curtesy of https://forums.raspberrypi.com/viewtopic.php?t=272035
        if ((chan > 7) or (chan < 0)):
            return -1
        
        r = self.spi.xfer2([1, (8 + chan) << 4, 0])
        adcout = ((r[1] & 3) << 8) + r[2]

        return adcout

    # filter ideas
    # https://en.wikipedia.org/wiki/Median_filter
    