import pandas as pd
import matplotlib.pyplot as plt

# Load the CSV file
file_path = "sensor_dynamics.csv"  # Replace with actual file path
df = pd.read_csv(file_path)

# Extract the unique values from the "Timestamp at last change" column
unique_timestamps = df["Timestamp at last Change"].unique()

# Ensure there are at least two unique timestamps
if len(unique_timestamps) < 2:
    raise ValueError("Not enough unique timestamps in 'Timestamp at last change' column.")

# Get the second unique timestamp
second_timestamp = unique_timestamps[2]

# Filter the DataFrame
filtered_df = df[df["Timestamp at last Change"] == second_timestamp]

# Plot the filtered data
plt.figure(figsize=(10, 5))
plt.plot(filtered_df["Current Timestamp"], filtered_df["ADC Reading"], marker='o', linestyle='-')
plt.xlabel("Time (s)")
plt.ylabel("ADC Reading")
plt.title(f"ADC Readings for Timestamp at Last Change = {second_timestamp}")
plt.grid(True)

# Save the figure
plt.savefig("less_adc_readings.png", dpi=300)  # Saves as PNG

plt.show()  # Show the plot
