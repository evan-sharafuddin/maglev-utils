### Demo version of controller for maglev system ###
### Instructions
# 1. Select desired zero and pole for lead compensator. Default
#    values that work well are shown below
# 2. Select a loop frequency FL, which will be used to discretize the 
#    controller.
# 3. Start with the feedback gain K where the two root loci diverge
#    from the real axis. This will likely be too low of a gain. 
# 4. Slowly raise ball until it is caught by magnet. If the ball is
#    not caught by the magnet then K is too small.
# 5. Repeat (4) until the ball is stabilized with minimal oscillation.
#    Note that too high of a K results in oscillatory behavior and eventually
#    instability.

from mcp3008 import MCP3008
from pwm import PWM
from filter import Filter

import curses
import numpy as np
import time
import math
import argparse

### Default system parameters (note that these differ based on a variety of conditions,
#   and hand tuning of K will likely be required)
FL          = 1e3   # loop frequency [Hz]
C_Z         = -20    # zero location
C_P         = -600   # pole location
K           = 7e4 # feedback gain
WINDOW_SIZE = 7      # moving average window size

### Two possible control schemes
# 1. Low oscillation, low strength
#    cz = -40, cp = -400, k ~ 2.3e4
# 2. High oscillation, high strength
#    cz = -20, cp = -600, k ~ 7e4

### set up command line arguments
msg = "Uses feedback controller with lead compensator to control MagLev System"
parser = argparse.ArgumentParser(description=msg)
# parser.add_argument('-t', type=int, default=0, help="Number of seconds to wait until start data buffering")
parser.add_argument('-b', type=float, default=-1, help="Size of buffer to store data. Enter zero to have no buffering")
parser.add_argument('-w', type=int, default=WINDOW_SIZE, help="Moving average window size")
parser.add_argument('-l', type=float, default=FL, help="Control loop frequency. Beware of going above 1 kHz")
parser.add_argument('-g', type=float, default=K, help="Feedback proportional gain")
args = parser.parse_args()

### Other parameters
F_CURSES = False # for curses display, leave as false for demo to reduce latency
P_BUFSIZE = int(args.b) # buffer size; choose 0 for no buffering
P_WINSIZE = args.w # averaging window size

class Controller:
    def __init__(): pass
    def iter():     pass

class LeadCompensator:
    def __init__( self,
                  sampling_frequency=FL,
                  zero_location=C_Z,
                  pole_location=C_P,
                  feedback_gain=K,
    ):
        
        # calculate controller gains
        print("Calculating controller gains...")
        TL = FL ** -1
        self.a = TL*C_Z + 1
        self.b = TL*C_P + 1
        print( \
              f"""
LEAD COMPENSATOR
 X    s - c_z 
--- = -------- ==> u[n] = K * ( x[n] - ax[n-1] + bu[n-1] )
 U    s - c_p
           
a  = {self.a}
b  = {self.b}
FL = {FL} 
              """\
        )

        self.FL = sampling_frequency
        self.K = feedback_gain

        self.p_delta_x = 0
        self.p_delta_u = 0



    """Calculates control input using discretized feedforward controller"""    
    def iter( self, x, x_des ):
        # NOTE X = measured position offset from equilibrium
        #      U = control voltage to apply to the electromagnet

        # transfer function takes in measured position [m] and outputs voltage input [V]
        delta_x = x - x_des # position permutation from equilibrium
        delta_u = self.K * ( delta_x - self.a*self.p_delta_x ) + self.b*self.p_delta_u

        self.p_delta_x = delta_x
        self.p_delta_u = delta_u

        # print(delta_u)

        return delta_u

class MagLev:
    def __init__( self, 
                  controller: Controller,
                  window_size=P_WINSIZE, 
                  pwm_pin=18, 
                  ir_channel=0,
                  pwm_frequency=10000, 
                  buf_size=P_BUFSIZE,
    ):
        
        self.pwm_pin = pwm_pin
        self.pwm_frequency = pwm_frequency
        self.buf_size = buf_size
        self.ir_chan = ir_channel
       
        self.adc = MCP3008()
        self.pwm = PWM(pin=pwm_pin, freq=pwm_frequency)
        self.controller = controller

        # Load CSV (skip header if you included one)
        data = np.loadtxt('adc_to_position_lookup3.csv', delimiter=',', skiprows=0)  # skiprows=0 if no header
        self.adc_counts = data[:, 0].astype(int)
        self.positions = data[:, 1]
        
        # create filters
        self.filt = Filter(list_size=window_size, threshold=True)

        ### constants
        self.x0 = 6 * 1e-3   # [mm] -> [m], commanded equilibrium position of ball (TODO make this more accurate and reflective of MATLAB)
        self.Kk = 9.7091e-06  # [N-A^2/m^2], electromechanical constant
        self.m = 0.006       # [kg]        
        self.g = 9.81        # [m/s^2]
        self.R = 6        # [Ohm]
        self.V_MAX = 24      # [V], approx. max voltage accross the magnet
        self.PWM_MAX = 100
        self.PWM_MIN = 0     # TODO around 10% DC, the current through the magnet is about zero
            
    """Enters loop to measure and filter position data"""
    def control( self, 
                 ctime: int = -1,         # Time (in seconds) to run control loop, -1 for infinite loop
    ): 

        # calculate/prepare relevant parameters
        i0 = math.sqrt( self.m*self.g*self.x0**2 / self.Kk ) # [A]
        v0 = i0 * self.R                    # [V]
        x_des = self.x0 # mm
        TL = self.controller.FL ** -1
        PWM_MIN = self.PWM_MIN
        PWM_MAX = self.PWM_MAX
        V_MAX = self.V_MAX
        chan = self.ir_chan

        if ctime == -1:
            # self._cout("Press Ctrl-C to exit control loop", 0, info=True, force=True)
            print("Press Ctrl-C to exit the loop...")

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
                # self._cout(f'ADC counts: {reading}', 0)
                # self._cout(f'Position reading: {reading_x}', 2)

                dt = ( time.monotonic_ns() - t_loop ) * 1e-9
                if dt >= TL:

                    # check for jitter
                    jitter_tol = TL * 1e-1 # 10% of control period
                    if dt > TL + jitter_tol:
                        print(f'WARNING: dt of {dt} exceeds timing jitter tolerance (ideal TL = {TL})')

                    # updates disp lines 3 and 4
                    delta_u = self.controller.iter(reading_x, x_des)

                    u = v0 + delta_u # calculate voltage, sum together equilib. and offset
                    # self._cout(f'Voltage input: {u}', 5)
                    # map voltage to PWM
                    # TODO make sure to verify this relationship is linear wrt PWM DC
                    pwm = u / V_MAX * (PWM_MAX - PWM_MIN) + PWM_MIN # accounts for nonzero PWM minimum
    
                    if pwm > PWM_MAX: 
                        pwm = PWM_MAX
                        # self._cout('Max DC reached', 1, info=True)
                    elif pwm < PWM_MIN: 
                        pwm = PWM_MIN
                        # self._cout('Min DC reached', 1, info=True)

                    # self._cout(f'Calculated pwm: {pwm}', 6)
                    # self._cout(f'Position error: {reading_x - x_des}', 7)

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
            # self._cout("Writing buffers...", 3, info=True)
            # np.savetxt(f"x.txt", data_buf, fmt='%f')
            # np.savetxt(f"u.txt", input_buf, fmt='%f')
            # np.savetxt(f"t.txt", time_buf, fmt='%f')
            # np.savetxt(f"pwm.txt", pwm_buf, fmt='%f')
            # np.savetxt(f"err.txt", err_buf, fmt='%f')
            # Stack them column-wise
            combined = np.column_stack((time_buf, input_buf, pwm_buf, data_buf, err_buf))
            header = 'time,input,pwm,data,err'
            np.savetxt("controller_output_22.csv", combined, delimiter=",", header=header, comments='', fmt='%.6f')
            # self._cout("Buffers written as text files!", 3, info=True)

            # UNCOMMENT if you only want to save one buffer and then abort
            break

# run file as a script
if __name__ == '__main__':
    c = LeadCompensator()
    ball = MagLev( controller=c )
    ball.control()  
