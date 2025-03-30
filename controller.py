#Defines a controller for the Maglev system

#Currently, this is just using moving avg and median filters for position estimation, but 
#in the future can utilize Kalman filtering or some other more advanced techniques.

#TODO 
#* define mixer to convert ADC readings to accurate position
#""

from mcp3008 import MCP3008
import curses
import atexit

import time
from collections import deque
import numpy as np
import RPi.GPIO as GPIO
import csv
import os

integral = 0
dc = 0

class Controller:
    def __init__( self, 
                 window_size, 
                 pwm_pin=12, 
                 pwm_frequency=10000, 
                 buf_size=10000,
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
        
        # handle GPIO cleanup upon exit
        def _at_exit():
            GPIO.cleanup()
            print("Cleaned GPIO pins")

        atexit.register(_at_exit)

        # set up PWM
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.pwm_pin, GPIO.OUT)
        self.pi_pwm = GPIO.PWM(self.pwm_pin, self.pwm_frequency)
        self.pi_pwm.start(0)

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
                #  crate: int = -1,         # Control loop rate (not gaurenteed for high (kHz) frequencies)
                 csleep: int = -1,        # Time (in microseconds) to pause between loop iterations, -1 for no pausing
                 actuate: bool = False,   # If just want to measure data, actuate should be false
                 batch_save: bool = False  # Save data buffers to text file, TODO use parallelism to fix latency w/ saving buffer?
    ): 
        
        # TODO add any testing that needs to be done
        
        # create data sotrage method
        window = deque(maxlen=self.window_size)

        tstart = time.time()
        previous_time=time.time()
        tic =    tstart # buffer timing

        csleep /= 1e6 # convert to seconds
        
        if ctime == -1:
            self._cout("Press Ctrl-C to exit control loop", 0, info=True)
	

        # enter control loop 
        while ctime == -1 or time.time() - tic < ctime: 

            data_buf = np.empty ( self.buf_size )
            input_buf = np.empty( self.buf_size )

            i = 0

            # enter buffer loop
            # while i < self.buf_size:
            while True:
                data = self.adc.read( chan )
                window.append( data )

                # Apply filtering only when the window is full
                # NOTE will only enter this loop when the program is first starting
                if len(window) == self.window_size:
                    
                    ### APPLY FILTERING 
                    avg = np.mean(window)  # Moving average
                    med = np.median(window)  # Median average
                    
                    # average both of the filter results
                    # val = ( avg + med ) / 2
                    val = avg
                    # val = data # just take current reading

                    # data_buf[i] = val  # Store the moving average in the buffer

                    # print this only when our window is finally full
                    # when we first start this program, we don't have enough readings to perform
                    #   moving average and median averaging, so we wait until window is full
                    if i == 1: self._cout("Window is loaded", 1, info=True)


                    ### UPDATE CONTROL LOOP
                    dt=time.time() - previous_time
                    previous_time=time.time()
                    u = self.control_iter( val, dt, tstart )

                    # add calculated input to buffer
                    # input_buf[i] = u


                    ### CHANGE ELECTROMAGNET CURRENT
                    # TODO not yet implemented
                    self.pi_pwm.ChangeDutyCycle(u)
                    ### INCREMENT BUFFER INDEX
                    # equivelant to moving to the next time step in our controller
                    i += 1

                    # if applicable, pause
                    if csleep > 0:
                        time.sleep(csleep)

            # time to fill buffers
            buf_time = time.time() - tic

            print("Writing buffers...")
            # np.savetxt(f"buf_{buf_time:.4f}.txt", self.data_buf, fmt='%f')
            np.savetxt(f"x.txt", data_buf, fmt='%f')
            np.savetxt(f"u.txt", input_buf, fmt='%f')
            print("Buffers written as text files!")


    """Use to calculate the control input given a measured state"""
    #should output duty cycle
    def control_iter( self,
                     x: float, dt: float, tstart: float) -> float:
        global integral, dc
    
        #lets say we want to keep the ball between the IR sensors. We want to keep adc reading to zero. 
        #(x_des=0). if x > 0, the ball is too low, so we want current to increase. So we want error to be 
        #x-x_des
        x_des=700
        Kp= 0.01
        Ki = 0.01
        Kd = 0.01
        INT_MAX_ABS = 1

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
        filename = 'save_data.csv'
        file_exists = os.path.isfile(filename)
        with open(filename, mode="a", newline='') as file:
          writer = csv.writer(file)
          if not file_exists:
              writer.writerow(["Time", "Dutycycle", "Position", "Error"])
          writer.writerow([f"{time.time() - tstart}", dc , x, error])
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
    thing.control( chan=0, csleep=-1 ) # NOTE csleep is in microseconds!


if __name__ == '__main__':
    try:
        curses.wrapper(main)

    # # must print error messages outside of the curses wrapper
    # except SystemExit as e:
    #     print()

    except Exception as e:
        print(f"An error occured: {str(e)}")
