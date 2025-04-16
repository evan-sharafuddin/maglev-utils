import numpy as np

# Load the data (assuming 'your_data.csv' has two columns: x, y)
data = np.loadtxt('adc_to_position_lookup2.csv', delimiter=',')

x_original = data[:, 0]
y_original = data[:, 1]

# Create regularly spaced x values (0.1 steps from min to max of original x)
x_new = np.arange(x_original.min(), x_original.max(), 0.1)

# Interpolate y values at the new x values
y_new = np.interp(x_new, x_original, y_original)

# Combine x_new and y_new into a single array
interpolated_data = np.column_stack((x_new, y_new))

# Save to CSV
np.savetxt('adc_to_position_lookup3.csv', interpolated_data, delimiter=',', fmt='%.10f')

# import numpy as np

# # Fake example that matches your case: irregular x, some y values
# x_original = np.array([898, 905, 910])
# y_original = np.array([0.0054, 0.01, 2])

# # Generate new x values from min to max in steps of 0.1
# x_new = np.arange(x_original[0], x_original[-1] + 0.1, 0.1)

# # Interpolate new y values for those x values
# y_new = np.interp(x_new, x_original, y_original)

# # Combine and print results
# result = np.column_stack((x_new, y_new))
# np.savetxt("interpolated_data.csv", result, delimiter=",", fmt="%.10f")

# # Optional: print the first few lines to verify
# print(result[:10])

