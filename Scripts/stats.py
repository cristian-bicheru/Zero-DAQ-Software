import sys

import numpy as np

filename = sys.argv[1]
idx = int(sys.argv[2])

print(f"Computing statistics of index {idx} of file {filename}.")

with open(filename, "r") as f:
    data = f.readlines()
    col_name = data[0].strip().split(',')[idx]
    print(f"Reading column {col_name}...")

    data = [x.strip().split(',') for x in data[1:-1]]
    t = np.array([float(x[0]) for x in data if x[idx] != "Ø"])
    y = np.array([float(x[idx]) for x in data if x[idx] != "Ø"])


t_diff = np.diff(t, 1)
t_freq = 1. / t_diff
mean_freq = np.mean(t_freq)
stddev_freq = np.std(t_freq)
mean_timestep = np.mean(t_diff)
max_timestep = np.max(t_diff)

print(f"Mean sample frequency: {mean_freq:.3g} Hz")
print(f"Standard deviation: {stddev_freq:.3g} Hz")
print(f"Mean sample timestep: {mean_timestep :.3g} s")
print(f"Max sample timestep: {max_timestep: .3g} s")
