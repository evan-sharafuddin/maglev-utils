"""Defines a controller for the Maglev system

Currently, this is just using moving avg and median filters for position estimation, but 
in the future can utilize Kalman filtering or some other more advanced techniques.

TODO 
* define mixer to convert ADC readings to accurate position
"""

from mcp3008 import MCP3008
from attrs import define, Factory, field

import time
from collections import deque
import numpy as np


@define 
class Controller:

    # member variables
    window_size: int = field()
    buf_size: int = field(default=10000)
    adc: MCP3008 = Factory(MCP3008)

    # do anything other than initializing member variables
    def __attrs_post_init__(self):
        pass # nothing to do here
    
    """Enters loop to measure and filter position data"""
    def control( self, 
                 chan: int,               # ADC channel for measuring data (0-7)
                 ctime: int = -1,         # Time (in seconds) to run control loop, -1 for infinite loop
                #  crate: int = -1,         # Control loop rate (not gaurenteed for high (kHz) frequencies)
                 csleep: int = -1,        # Time (in microseconds) to pause between loop iterations, -1 for no pausing
                 actuate: bool = False,   # If just want to measure data, actuate should be false
                 batch_save: bool = True  # Save data buffers to text file, TODO use parallelism to fix latency w/ saving buffer?
    ): 
        
        # TODO add any testing that needs to be done
        
        # create data sotrage method
        window = deque(maxlen=self.window_size)

        tstart = time.time()
        tic =    tstart # buffer timing

        csleep /= 1e6 # convert to seconds
        
        if ctime == -1:
            print("Press Ctrl-C to exit control loop")
	

        # enter control loop 
        while ctime == -1 or time.time() - tic < ctime: 

            data_buf = np.empty ( self.buf_size )
            input_buf = np.empty( self.buf_size )

            i = 0

            # enter buffer loop
            while i < self.buf_size:
                data = self.adc.read( chan )
                window.append( data )

                # Apply filtering only when the window is full
                # NOTE will only enter this loop when the program is first starting
                if len(window) == self.window_size:
                    
                    ### APPLY FILTERING 
                    avg = np.mean(window)  # Moving average
                    med = np.median(window)  # Median (currently unused)
                    
                    # average both of the filter results
                    val = ( avg + med ) / 2

                    data_buf[i] = val  # Store the moving average in the buffer

                    # print this only when our window is finally full
                    # when we first start this program, we don't have enough readings to perform
                    #   moving average and median averaging, so we wait until window is full
                    if i == 1: print("Window is loaded")


                    ### UPDATE CONTROL LOOP
                    dt=previous_time-time.perf_counter
                    previous_time=time.perf_counter
                    u = self.control_iter( x=val, dt )

                    # add calculated input to buffer
                    input_buf[i] = u


                    ### CHANGE ELECTROMAGNET CURRENT
                    # TODO not yet implemented


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
    def control_iter( self,
                      x: float, dt) -> float:
	x_des=99;
	Kp=10;
	Ki = 0;
	error=x_des-x
	integral=error*dt+integral
	#note that Kp, Ki have units of Amps/ADC reading 
	current = Kp*error+Ki*integral           
        
        return current
    
        # TODO Izzy, implement controller calculations here
        # NOTE currently this function just returns the input

# for testing purposes
if __name__ == '__main__':
    thing = Controller(window_size=400)
    thing.control( chan=0, csleep=100 )
