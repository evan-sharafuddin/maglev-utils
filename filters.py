"""
Creates helper functions for moving average and median filters

"""

from collections import deque
from statistics import median 

class Filters:

    def __init__( self, list_size=5, threshold=True ):
        self.list = deque()
        self.list_size = list_size
        self.thresh = threshold # NOTE: thresholding currently not implemented
    
    def _add( self, data ): 
        if len(self.list) == self.list_size:
            self.list.pop()
        

        self.list.appendleft(data)
        


    def add_data( self, data ) -> float:
        self._add(data)

        return data

    def add_data_mean( self, data ) -> float:
        self._add(data)

        return sum(self.list) / len(self.list)
        
    def add_data_median( self, data ) -> float: 
        self._add(data)

        return median(self.list)
        

