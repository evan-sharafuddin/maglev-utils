import pigpio
import time
import atexit

class PWM:
    """Simple class for controlling hardware PWM on the pi"""

    def __init__(self, 
                 pin=18, # GPIO18, cooresponds to physical pin 12
                 freq=10000 # anything below 150 MHz; MOSFET driver designed for 20 kHz
    ):
        self.pin = pin
        self.freq = freq

        self.pi = pigpio.pi()
        if not self.pi.connected:
            print("Failed to connect to pigpio daemon.")
            exit()

        self.pi.hardware_PWM(self.pin, 0, 0)

        def _close_pwm():
            # Stop PWM by setting frequency and duty to 0
            self.pi.hardware_PWM(self.pin, 0, 0)
            self.pi.stop()
            print("Stopped pigpio daemon")

        atexit.register(_close_pwm)
        
        print(f"PWM initialized on GPIO{self.pin} at {self.freq} Hz.")

    def set_dc(self, dc):
        if dc < 0 or dc > 100:
            print("Must input value between 0 and 100 for desired duty cycle")
        
        else:
            MAX_DC_VAL = 1000000
            duty_cycle = int(MAX_DC_VAL * (dc / 100))  # duty in range 0 - 1,000,000
            self.pi.hardware_PWM(self.pin, self.freq, duty_cycle)


if __name__ == '__main__':
    pwm = PWM()

    import numpy as np
    import matplotlib.pyplot as plt

    N = 100  # Number of samples
    x = np.arange(N)
    sine_wave = np.sin(2 * np.pi * x / N)  # Sine wave in range [-1, 1]

    # Scale to range [0, 100]
    scaled_sine = 50 * (sine_wave + 1)  # Shift and scale to [0, 100]
    
    for i in scaled_sine:
        pwm.set_dc(i)
        time.sleep(0.1)