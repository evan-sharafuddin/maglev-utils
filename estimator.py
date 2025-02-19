"""Defines a state estimator for the maglev system. 

Currently, this is just using moving avg and median filters, but 
in the future can utilize Kalman filtering or some other more advanced techniques.
"""

from mcp3008 import MCP3008
from attrs import define, Factory, field

import time
from collections import deque
import numpy as np


@define 
class Estimator:

    # member variable

    window_size: int = field()
    buf_size: int = field(default=10000)

    adc: MCP3008 = Factory(MCP3008)
    data_buf: np.ndarray = field(init=False)


    def __attrs_post_init__(self):
        self.data_buf = np.empty( self.buf_size )
    
    """Enters loop to measure and filter position data"""
    def measure( self, chan: int, batch_save: bool = True ): 
        
        # TODO add any testing that needs to be done
        
        # create data sotrage method
        window = deque(maxlen=self.window_size)

        tic = time.time()
        print("Reading data...")
        # enter measurement loop
    
        i = 0
        while i < self.buf_size:
            data = self.adc.read( chan )
            window.append( data )
            # self.data_buf[i] = data

            # Apply filtering only when the window is full
            if len(window) == self.window_size:
                avg = np.mean(window)  # Moving average
                med = np.median(window)  # Median (currently unused)
                
                self.data_buf[i] = avg  # Store the moving average in the buffer

                i += 1

        # time to fill buffer
        buf_time = time.time() - tic

        print("Writing buffer...")
        # np.savetxt(f"buf_{buf_time:.4f}.txt", self.data_buf, fmt='%f')
        np.savetxt(f"buf.txt", self.data_buf, fmt='%f')
        print(f"File written as 'buf_{buf_time:.4f}.txt'!")



# for testing purposes
if __name__ == '__main__':
    thing = Estimator(window_size=400)
    
    thing.measure(0)
