"""
Creates helper functions for moving average and median filters

"""

from collections import deque
from statistics import median 

class Filter:

    THRESHOLD_CHANGE = 500

    def __init__( self, list_size=5, threshold=False ):
        self.list = deque()
        self.list_size = list_size
        self.threshold = True

    def _add( self, data, ): 
        if len(self.list) == self.list_size:
            self.list.pop()
        
        # add item to list
        self.list.appendleft(data)

        # if applicable, threshold
        if len( self.list ) > 1 and self.threshold: # cannot threshold if only have one value in the list
            prev_data = self.list[1]
            d_data = data - prev_data

            if abs( d_data ) > Filter.THRESHOLD_CHANGE:
                # revert first item
                self.list[0] = prev_data

    def add_data( self, data ) -> float:
        self._add(data)

        return data

    def add_data_mean( self, data ) -> float:
        self._add(data)

        return sum(self.list) / len(self.list)
        
    def add_data_median( self, data ) -> float: 
        self._add(data)

        return median(self.list)


