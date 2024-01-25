import sys

import numpy as np
import matplotlib.pyplot as plt

filename = sys.argv[1]
idx = int(sys.argv[2])

print(f"Plotting index {idx} of file {filename}.")

with open(filename, "r") as f:
    data = f.readlines()
    col_name = data[0].strip().split(',')[idx]
    print(f"Reading column {col_name}...")

    data = [x.strip().split(',') for x in data[1:-1]]
    t = np.array([float(x[0]) for x in data if x[idx] != "Ø"])
    y = np.array([float(x[idx]) for x in data if x[idx] != "Ø"])


t_freq = 1. / np.diff(t, 1)
mean_freq = np.mean(t_freq)
stddev_freq = np.std(t_freq)

print(f"Mean sample frequency: {mean_freq:.3g} Hz")
print(f"Standard deviation: {stddev_freq:.3g} Hz")

plt.plot(t, y)
plt.title("Sensor Data Plot")
plt.xlabel("Time [s]")
plt.ylabel(col_name)
plt.show()
