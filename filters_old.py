"""
Creates helper functions for moving average and median filters

"""

import numpy as np

class Filters:

    """Returns the average value in the list `data`"""
    @staticmethod
    def simple_mean( data: np.ndarray ) -> float:
        
        return sum(data) / len(data)
    

    """Returns the moving average list of `data` using a window of size `window`"""
    @staticmethod
    def moving_avg( data: np.ndarray, window: int ) -> list:
        
        ret_len = len(data) - window + 1 # length of moving average list
        ret = np.array(ret_len)
        j = window # use for slicing

        for i in range( len(data) - window + 1 ):
            j += i # use for slicing
            
                
            

    

    """Returns a median filtered list of `data` using a window of size `window`"""
    @staticmethod
    def median_filter( data: np.ndarray, window: int ) -> list:
        pass
