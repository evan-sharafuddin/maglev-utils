import pandas as pd
import matplotlib.pyplot as plt

# Load the CSV file
file_path = "dynamic_readings.csv"  # Replace with your actual file path
df = pd.read_csv(file_path)

# Extract relevant columns
timestamps = df["Current Timestamp"]
adc_readings = df["ADC Reading"]

# Plot the data
plt.figure(figsize=(10, 5))
plt.plot(timestamps, adc_readings, marker='o', linestyle='-')
plt.xlabel("Time (s)")
plt.ylabel("ADC Reading")
plt.title("ADC Readings Over Time")
plt.grid()
plt.show()
plt.savefig("adc_readings.png", dpi=300)
