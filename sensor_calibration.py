import mcp3008
import time
import csv

# Initialize ADC
channel = 7
adc = mcp3008.MCP3008()

# Open a CSV file for writing
with open("adc_readings.csv", "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["Height", "Timestamp", "ADC Reading"])
    
    while True:
        height = input("Enter the ball height (or type 'done' to finish): ")
        if height.lower() == "done":
            break
        
        try:
            height = float(height)
        except ValueError:
            print("Invalid input. Please enter a numeric height or 'done' to exit.")
            continue
        
        print("Collecting data for 5 seconds...")
        start_time = time.time()
        while time.time() - start_time < 5:
            reading = adc.read(channel)
            timestamp = time.time()
            writer.writerow([height, timestamp, reading])
            time.sleep(0.1)  # Adjust sampling rate as needed

print("Data collection complete. Saved to adc_readings.csv.")

