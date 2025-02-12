import curses
import time
import mcp3008

def main(stdscr):
    # Initialize curses
    curses.curs_set(0)  # Hide the cursor
    stdscr.nodelay(1)   # Non-blocking input
    stdscr.timeout(100)  # Refresh every 100 ms
    
    # initialize ADC
    adc = mcp3008.MCP3008( Vdd_hi=True ) # assuming 5 Vdd

    # constants
    refresh = 0.5 # time in seconds to refresh reading 
    channel = 0
    while True:

        # get sensor data
        start = time.time()

        sum = 0
        cnt = 0

        while time.time() - start > refresh: 
            sum += adc.read(channel)
            cnt += 1

        reading = sum / cnt

        # Clear screen to avoid overwriting previous content
        stdscr.clear()

        # Create the text string
        text = f"Press Ctrl-C to cancel\n\nADC reading: {reading}" \
               f"Num samples: {cnt}"

        # Add the text to the window at position (1, 1)
        stdscr.addstr(1, 1, text)

        # Update the screen
        stdscr.refresh()

if __name__ == "__main__":
    curses.wrapper(main)