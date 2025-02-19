# thanks Chat

import numpy as np
import matplotlib.pyplot as plt

# Load the data from the text file
loaded_array = np.loadtxt('buf.txt', dtype=float)
print(loaded_array)

plt.plot(loaded_array)
plt.title('1D Array Plot')
plt.xlabel('Index')
plt.ylabel('Value')
plt.show()

plt.savefig('plot.png')  # Save as PNG file