"""
Creates helper functions for moving average and median filters

"""


class Filters:

    """Returns the average value in the list `data`"""
    @staticmethod
    def simple_mean( data ):
        return sum(data) / len(data)
    
    @staticmethod
    def moving_avg( data, window ):
        pass 
        # if window > len(data):
        #     print("ERROR: moving average window size larger than number of data points.")
        #     return
        
        # # let i be the tailend of the window
        # for k in range(len(data) + window):
        #     i = k - window + 1

        #     # check if front end of window is outside of array
        #     if i < 0:
        #         window_list = data[:k]
        #         avg = sum(window_list) / len(window_list)

    @staticmethod
    def median_filter(data, window):
        pass
