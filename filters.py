"""
Creates helper functions for moving average and median filters

"""

from collections import deque
from statistics import median 

class Filters:

    MEDIAN_THRESH = 0.05

    def __init__( self, list_size=5, med_threshold=True ):
        self.list = deque()
        self.list_size = list_size

        self.thresh = med_threshold # NOTE: thresholding currently not implemented
        if med_threshold:
            self.list_thresh = deque()
            self.list_size_thresh = list_size * 2


    def _add( self, data, thresh=False ): 
        if len(self.list) == self.list_size:
            self.list.pop()
        if len(self.list_thresh) == self.list_size_thresh:
            self.list_thresh.pop()
        
        # calculating median filter thresholding
        if len(self.list_thresh) == 0:
            self.list.appendleft(data)
            self.list_thresh.appendleft(data)
            return
        else:
            med = median(self.list_thresh)
        
        try: 

            # if thresh and len(self.list_thresh) == self.list_size_thresh and abs( (data - med) / data ) > Filters.MEDIAN_THRESH:
            if thresh and abs( (data - med) / data ) > Filters.MEDIAN_THRESH:
                # new data point is very off from median, skip adding
                most_recent_val = self.list[0]
                self.list.appendleft(most_recent_val)
                self.list_thresh.appendleft(data)
            else:
                # new data point is good to add
                self.list.appendleft(data)
                self.list_thresh.appendleft(data)

        except:
            most_recent_val = self.list[0]
            self.list.appendleft(most_recent_val)
            self.list_thresh.appendleft(data)
            # print(f"ERROR: dividebyzero... value you are trying to add is {data}. Cannot add value of zero.")
    def add_data( self, data ) -> float:
        self._add(data)

        return data

    def add_data_mean( self, data ) -> float:
        self._add(data)

        return sum(self.list) / len(self.list)
        
    def add_data_median( self, data ) -> float: 
        self._add(data)

        return median(self.list)
        
    def add_data_mean_t( self, data ) -> float:
        self._add(data, thresh=self.thresh)
        
        return sum(self.list) / len(self.list)


