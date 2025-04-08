import numpy as np
import matplotlib.pyplot as plt

# Load the data
x = np.loadtxt("x.txt")
u = np.loadtxt("u.txt")
t = np.loadtxt("t.txt")

# Create the plot
fig, ax1 = plt.subplots()

# Plot x vs t on the left y-axis
ax1.plot(t, x, 'b-', label='x')
ax1.set_xlabel('Time (t)')
ax1.set_ylabel('x', color='b')
ax1.tick_params(axis='y', labelcolor='b')
ax1.set_ylim([np.min(x), np.max(x)])

# Create a second y-axis for u
ax2 = ax1.twinx()
ax2.plot(t, u, 'r--', label='u')
ax2.set_ylabel('u (%)', color='r')
ax2.tick_params(axis='y', labelcolor='r')
ax2.set_ylim([0, 100])

# Optional: Add legends
fig.legend(loc='upper right')

plt.title("x and u vs t")
plt.grid(True)
plt.tight_layout()
# Save the figure

plt.savefig("x_u_vs_t.png", dpi=300)
