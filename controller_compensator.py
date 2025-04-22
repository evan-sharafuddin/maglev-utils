# NEWEST VERSION OF MAGLEV CONTROLLER

# NOTE if you get this error: wmove() returned ERR
#   try increasing the size of your terminal. Same with other curses errors, this is usually the root cause

from mcp3008 import MCP3008
from pwm import PWM
from filter import Filter

import curses
import numpy as np
import time
import math
import argparse

# set up command line arguments
msg = "Uses feedback controller with lead compensator to control MagLev System"
parser = argparse.ArgumentParser(description=msg)

parser.add_argument('-t', type=int, default=0, help="Number of seconds to wait until start data buffering")
parser.add_argument('-b', type=float, default=-1, help="Size of buffer to store data. Enter zero to have no buffering")
parser.add_argument('-w', type=int, default=7, help="Moving average window size")
parser.add_argument('-l', type=float, default=1e3, help="Control loop frequency. Beware of going above 1 kHz")
parser.add_argument('-g', type=float, default=2.05e4, help="Feedback proportional gain")

args = parser.parse_args()

### SET FLAGS AND PARAM HERE ###
global K, FL, A0, A1, B0, B1
F_CURSES = False # for curses display
P_BUFSIZE = int(args.b) # buffer size; choose 0 for no buffering
P_WINSIZE = args.w # averaging window size
K = args.g
FL = args.l

A0 = 0.967
A1 = 1
B0 = 0.6703
B1 = 1
A0 *= K
A1 *= K



class Controller:
    def __init__( self, 
                  window_size, 
                  pwm_pin=18, 
                  pwm_frequency=10000, 
                  buf_size=1000,
                  using_curses=False, 
                  info_win=None,
                  data_win=None, 
    ):
        
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

        # Load CSV (skip header if you included one)
        data = np.loadtxt('adc_to_position_lookup3.csv', delimiter=',', skiprows=0)  # skiprows=0 if no header

        self.adc_counts = data[:, 0].astype(int)
        self.positions = data[:, 1]
        
        # create filters
        self.filt = Filter(list_size=window_size, threshold=True)

    """Handles curses output if using curses"""
    def _cout(self, text: str, row: int, info: bool=False, force: bool=False):
        
        # no-op if we are being really careful with timing
        if not force and not self.using_curses:
            return
        
        elif self.using_curses:
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
    ): 

        ### SET PARAMETERS HERE ###
        # FL = 1000 # loop frequency, changing this will change the gains for the DT compensator
        global FL
        TL = 1/FL
        x0 = 6 * 1e-3   # [mm] -> [m], commanded equilibrium position of ball
        
        # constants
        Kk = 9.7091e-06  # [N-A^2/m^2], electromechanical constant
        m = 0.006       # [kg]        
        g = 9.81        # [m/s^2]
        R = 8        # [Ohm]
        V_MAX = 24      # [V], approx. max voltage accross the magnet
        PWM_MAX = 100
        PWM_MIN = 0     # TODO around 10% DC, the current through the magnet is about zero
        # L = 0.14485     # [H]

        # calculate equilibrium current, voltage
        i0 = math.sqrt( m*g*x0**2 / Kk ) # [A]
        v0 = i0 * R                    # [V]
        
        # UNCOMMENT to prepare variables for the Lead compensator
        x_des = x0 # mm
        global p_delta_x, p_delta_u
        p_delta_u = 0
        p_delta_x = 0

        # # UNCOMMENT to prepare variables for PID controller
        # global integral, dc
        # integral = 0
        # dc = 0
        
        if ctime == -1:
            self._cout("Press Ctrl-C to exit control loop", 0, info=True, force=True)

        # init timing
        t_start  = time.monotonic_ns()
        t_loop = time.monotonic_ns()

        # enter control loop 
        while ctime == -1 or time.monotonic_ns() - t_start < ctime: 
            
            if self.buf_size > 0:
                data_buf  = np.empty( self.buf_size )
                input_buf = np.empty( self.buf_size )
                time_buf  = np.empty( self.buf_size )
                pwm_buf   = np.empty( self.buf_size )
                err_buf   = np.empty( self.buf_size )

            i = 0
            t_start = time.monotonic_ns() # ues for calculating time data

            # initialize other values
            pwm, u = 0, 0

            # enter buffer loop
            # NOTE if buf_size <= 0, then this is an infinite loop
            while self.buf_size <= 0 or i < self.buf_size * 2:
                
                data = self.adc.read( chan )
                reading = self.filt.add_data_mean(data) # filter readings
                reading_rnd = int( round(reading, 1) ) # convert to integer
                reading_x = self.positions[self.adc_counts == reading_rnd][0]
                self._cout(f'ADC counts: {reading}', 0)
                self._cout(f'Position reading: {reading_x}', 2)

                dt = ( time.monotonic_ns() - t_loop ) * 1e-9
                if dt >= TL:

                    # check for jitter
                    jitter_tol = TL * 1e-1 # 10% of control period
                    if dt > TL + jitter_tol:
                        self._cout(f'WARNING: dt of {dt} exceeds timing jitter tolerance (ideal TL = {TL})', \
                                   2, info=True, force=True)

                    self._cout(f'Control loop actual time: {(time.monotonic_ns() - t_loop) * 1e-9}', 1)

                    # updates disp lines 3 and 4
                    delta_u = self.control_iter_comp(reading_x, x_des)

                    u = v0 + delta_u # calculate voltage, sum together equilib. and offset
                    self._cout(f'Voltage input: {u}', 5)
                    # map voltage to PWM
                    # TODO make sure to verify this relationship is linear wrt PWM DC
                    pwm = u / V_MAX * (PWM_MAX - PWM_MIN) + PWM_MIN # accounts for nonzero PWM minimum
    
                    if pwm > PWM_MAX: 
                        pwm = PWM_MAX
                        self._cout('Max DC reached', 1, info=True)
                    elif pwm < PWM_MIN: 
                        pwm = PWM_MIN
                        self._cout('Min DC reached', 1, info=True)
                    else:
                        self._cout('', 1, info=True)

                    self._cout(f'Calculated pwm: {pwm}', 6)
                    self._cout(f'Position error: {reading_x - x_des}', 7)

                    self.pwm.set_dc(pwm)
                    t_loop = time.monotonic_ns()

                if self.buf_size > 0 and i % 2 == 0:
                    j = int(i / 2)
                    data_buf[j]  = reading_x
                    input_buf[j] = u
                    time_buf[j]  = (time.monotonic_ns() - t_start)*1e-9
                    pwm_buf[j]   = pwm
                    err_buf[j]   = reading_x - x_des
                i += 1

            # NOTE if you are not buffering, this code will never be reached
            self._cout("Writing buffers...", 3, info=True)
            # np.savetxt(f"x.txt", data_buf, fmt='%f')
            # np.savetxt(f"u.txt", input_buf, fmt='%f')
            # np.savetxt(f"t.txt", time_buf, fmt='%f')
            # np.savetxt(f"pwm.txt", pwm_buf, fmt='%f')
            # np.savetxt(f"err.txt", err_buf, fmt='%f')
            # Stack them column-wise
            combined = np.column_stack((time_buf, input_buf, pwm_buf, data_buf, err_buf))
            header = 'time,input,pwm,data,err'
            np.savetxt("controller_output_22.csv", combined, delimiter=",", header=header, comments='', fmt='%.6f')
            self._cout("Buffers written as text files!", 3, info=True)

            # UNCOMMENT if you only want to save one buffer and then abort
            break

    """Calculates control input using discretized feedforward controller"""
    def control_iter_comp( self, x, x_des ):
        # store previous values
        global p_delta_x, p_delta_u

        # controller based on sampling rate of 1000 Hz
        #   U      A1.z - A0
        #  --- ==> ---------
        #   X      B1.z - B0
        # NOTE X = measured position offset from equilibrium
        #      U = control voltage to apply to the electromagnet

        global K, A0, A1, B0, B1

        # transfer function takes in measured position [m] and outputs voltage input [V]
        delta_x = x - x_des # position permutation from equilibrium
        delta_u = 1 / B1 * ( A1*delta_x - A0*p_delta_x + B0*p_delta_u )

        p_delta_x = delta_x
        p_delta_u = delta_u

        self._cout(f'Delta x [m]: {delta_x}', 3)
        self._cout(f'Delta u [V]: {delta_u}', 4)

        return delta_u


    """Use to calculate the control input given a measured state"""
    #should output duty cycle
    def control_iter( self,
                     x: float, dt: float, t_start: float, x_des: float) -> float:
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
        if dc > 100:
            dc = 100
            self._cout('Max Dutycycle Reached', 1, info=True)
        elif dc < 0: 
            dc = 0
            self._cout('Min Dutycycle Reached', 1, info=True)
        else:
            self._cout('', 1, info=True)

        self._cout(f"Position sensor reading: {x}", 0)
        self._cout(f"Duty cycle input: {dc}", 1)
        
        return dc

# Curses window
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

# run file as a script
if __name__ == '__main__':

    if F_CURSES:
        try:
            curses.wrapper(main)

        except Exception as e:
            print(f"An error occured: {str(e)}")

    else:
        thing = Controller(window_size=P_WINSIZE, using_curses=False, buf_size=P_BUFSIZE)
        thing.control( chan=0 )  
