#Defines a controller for the Maglev system

#Currently, this is just using moving avg and median filters for position estimation, but 
#in the future can utilize Kalman filtering or some other more advanced techniques.

#TODO 
#* define mixer to convert ADC readings to accurate position
#""

# NOTE if you get this error: wmove() returned ERR
#   try increasing the size of your terminal. Same with other curses errors, this is usually the root cause


from mcp3008 import MCP3008
from pwm import PWM
from filters import Filters
import curses
import atexit
import numpy as np

import time
from collections import deque
import numpy as np
import RPi.GPIO as GPIO
import csv
import os
import math

integral = 0
dc = 0

class Controller:
    def __init__( self, 
                 window_size, 
                 pwm_pin=18, # NOT physical pin
                 pwm_frequency=10000, 
                 buf_size=2000,
                 using_curses=False, 
                 info_win=None,
                 data_win=None, ):
        
        self.window_size = window_size
        self.pwm_pin = pwm_pin
        self.pwm_frequency = pwm_frequency
        self.buf_size = buf_size
        self.adc = MCP3008()
        self.using_curses = using_curses
        self.info_win = info_win
        self.data_win = data_win

        self.prev = -1 # use for derivative gain

        self.pwm = PWM(pin=pwm_pin, freq=pwm_frequency)

        # load adc to position lookup table
        import numpy as np

        # Load CSV (skip header if you included one)
        data = np.loadtxt('adc_to_position_lookup.csv', delimiter=',', skiprows=0)  # skiprows=0 if no header

        self.adc_counts = data[:, 0].astype(int)
        self.positions = data[:, 1]
        
        # create filters
        self.filt = Filters(list_size=window_size)

    """Handles curses output if using curses"""
    def _cout(self, text: str, row: int, info: bool=False):
        if self.using_curses:
            if info:
                self.info_win.move(row, 0)
                self.info_win.clrtoeol()
                self.info_win.addstr(row, 0, text)
                self.info_win.refresh()
            else:
                self.data_win.move(row, 0)
                self.data_win.clrtoeol()
                self.data_win.addstr(row, 0, text) # add text to column 0
                self.data_win.refresh()


        else: 
            print(text) # print to stdout
            
    """Enters loop to measure and filter position data"""
    def control( self, 
                 chan: int,               # ADC channel for measuring data (0-7)
                 ctime: int = -1,         # Time (in seconds) to run control loop, -1 for infinite loop
                 crate: int = -1,         # Control loop rate (not gaurenteed for high (kHz) frequencies)
    ): 
        

        tstart = time.monotonic_ns()
        previous_time=time.monotonic_ns()
        tic = tstart # buffer timing

        # SET PARAMETERS HERE
        FS = 1000 # sample frequency, changing this will change the gains for the DT compensator
        x0 = 5
        i0 = 0.3893

        x_des = x0 # mm
        global p_delta_x, p_delta_u
        p_delta_u = 0
        p_delta_x = 0
        
        if ctime == -1:
            self._cout("Press Ctrl-C to exit control loop", 0, info=True)

        t_sample = time.monotonic_ns()

        # enter control loop 
        while ctime == -1 or time.monotonic_ns() - tic < ctime: 
            
            data_buf = np.empty ( self.buf_size )
            input_buf = np.empty( self.buf_size )
            time_buf  = np.empty( self.buf_size )

            i = 0
            tic = time.monotonic_ns()


            # enter buffer loop
            while i < self.buf_size:
                data = self.adc.read( chan )

                val = self.filt.add_data_mean_t(data) # filter readings

                # convert counts to position
                self._cout(f'ADC counts: {val}', 0)

                # if at sampling time, run controller loop
                if time.monotonic_ns() - t_sample >= 1 / FS:

                    val = int( round(val) ) # convert to integer
                    val = self.positions[self.adc_counts == val][0]

                    self._cout(f'Position reading: {val}', 1)

                    deltau = self.control_iter_comp(val, x_des)

                    u = i0 + deltau
                    # use linear approximation to set pwm
                    self._cout(f'Current input: {u}', 4)
                    
                    # handle negative currents (and PMWs, indirectly)
                    if u < 0: u = 0
                    pwm = 72.489 * math.sqrt(u) # constant found using least squares
                    
                    # set upper bound on pwm
                    if pwm > 100: pwm = 100

                    self._cout(f'Calculated pwm: {pwm}', 5)

                    self.pwm.set_dc(pwm)


                # data_buf[i] = val
                # input_buf[i] = u
                # time_buf[i] = (time.monotonic_ns() - tic)*1e-9
                # i += 1


            # time to fill buffers
            # buf_time = time.time() - tic

            self._cout("Writing buffers...", 3, info=True)
            np.savetxt(f"x.txt", data_buf, fmt='%f')
            np.savetxt(f"u.txt", input_buf, fmt='%f')
            np.savetxt(f"t.txt", time_buf, fmt='%f')
            self._cout("Buffers written as text files!", 3, info=True)

            # break

    """Calculates control input using discretized feedforward controller"""
    def control_iter_comp( self, x, x_des ):
        # store previous values
        global p_delta_x, p_delta_u

        # controller based on sampling rate of 1000 Hz
        #  z - 0.967      U
        #  ----------  = ---
        #  z - 0.6703     X
        # \deltau[n] = 0.6703\deltau[n−1]+\deltax[n]−0.967\deltax[n−1]
        #            = A1*\deltau[n−1]+B0*\deltax[n]−B1*\deltax[n−1]
        FS = 1000
        A0 = 1
        A1 = 0.6703
        B0 = 1
        B1 = 0.967

        # transfer function takes in measured position (mm) and outputs current input
        delta_x = x - x_des # position permutation from equilibrium
        delta_u = A1*p_delta_u + B0*delta_x - B1*p_delta_x

        p_delta_x = delta_x
        p_delta_u = delta_u

        self._cout(f'Delta x: {delta_x}', 2)
        self._cout(f'Delta u: {delta_u}', 3)

        return delta_u


    """Use to calculate the control input given a measured state"""
    #should output duty cycle
    def control_iter( self,
                     x: float, dt: float, tstart: float, x_des: float) -> float:
        global integral, dc
    
        #lets say we want to keep the ball between the IR sensors. We want to keep adc reading to zero. 
        #(x_des=0). if x > 0, the ball is too low, so we want current to increase. So we want error to be 
        #x-x_des
        # x_des=200
        Kp= 1
        Ki = 0.1
        Kd = 0.005
        INT_MAX_ABS = 10

        max_int = INT_MAX_ABS # prevent integrator windup
        min_int = -INT_MAX_ABS
        error=x-x_des
        integral=error*dt+integral

        if integral > max_int:
            integral = max_int
        if integral < min_int: 
            integral = min_int

        if self.prev == -1:
            derivative = 0
        else:
            derivative = (error - self.prev) / dt
        
        self.prev = error

        # print out stuff
        self._cout(f'Error: {error}', 2)
        self._cout(f'Derivative: {derivative}', 3)
        self._cout(f'Integral: {integral}', 4)
        self._cout(f'dt: {dt}', 5)
        if x is not None: self._cout(f'Position (mm): {x}', 6)
        self._cout(f'Position setpoint (mm) {x_des}', 7)

        dc = Kp*error+ Ki*integral + Kd*derivative
        #saturation
        if dc > 99:
            dc = 99
            self._cout('Max Dutycycle Reached', 2, info=True)
        elif dc < 0: 
            dc = 0
            self._cout('Min Dutycycle Reached', 2, info=True)
        else:
            self._cout('', 2, info=True)

        self._cout(f"Position sensor reading: {x}", 0)

        self._cout(f"Duty cycle input: {dc}", 1)
        
        
        # filename = 'save_data.csv'
        # file_exists = os.path.isfile(filename)
        # with open(filename, mode="a", newline='') as file:
        #   writer = csv.writer(file)
        #   if not file_exists:
        #       writer.writerow(["Time", "Dutycycle", "Position", "Error"])
        #   writer.writerow([f"{time.time() - tstart}", dc , x, error])
        return dc

# for testing purposes
def main(stdscr):
    
    ### Boilerplate setup
    # Initialize curses terminal
    curses.curs_set(0)  # Hide the cursor
    stdscr.nodelay(1)   # Non-blocking input
    stdscr.timeout(100)  # Refresh every 100 ms

    height, width = stdscr.getmaxyx()
    info_section_height = 5
    data_section_height = height - info_section_height

    # Create a window for error messages (top part of the screen)
    info_win = curses.newwin(info_section_height, width, 0, 0)
    # Create a window for routine data (bottom part of the screen)
    data_win = curses.newwin(data_section_height, width, info_section_height, 0)
    
    # add info to info_win
    # info_win.addstr(0, 0, "Press Ctrl-C to exit program")
    info_win.addstr(4, 0, "-------")
    # info_win.refresh()

    ### Init controller
    thing = Controller(5, using_curses=True, info_win=info_win, data_win=data_win)
    thing.control( chan=0 ) 


if __name__ == '__main__':
    try:
        curses.wrapper(main)

    # # must print error messages outside of the curses wrapper
    # except SystemExit as e:
    #     print()

    except Exception as e:
        print(f"An error occured: {str(e)}")
