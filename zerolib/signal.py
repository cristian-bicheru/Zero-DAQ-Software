""" Real-time data interpretation algorithms.
"""
import numpy as np

from scipy import signal

def ema(arr, k=0.3):
    ret = [arr[0]]
    for x in arr[1:]:
        ret.append(x * k + ret[-1] * (1-k))
    return np.array(ret)

def get_crit_freq(sr):
    return (sr/1000)**0.5 * 5

class GenericSensorDenoiser:
    """ Denoising algorithms for analog sensors.
    
    """
    def __init__(self, sample_rate):
        self.freq = sample_rate
        self.filter = signal.butter(3, get_crit_freq(sample_rate), output="sos", fs=sample_rate)
        self.lookback = max(int(self.freq**0.75), 20)

        self.signal = []
        self.filtered_signal = []
    
    def update(self, y):
        if not self.signal:
            self.signal = [y for _ in range(self.lookback)]

        self.signal.append(y)
        sample = self.signal[-self.lookback:]

        output = signal.sosfiltfilt(self.filter, sample)[-1]
        self.filtered_signal.append(output)

        return output
    
    def get_value(self):
        if self.filtered_signal:
            return self.filtered_signal[-1]
        else:
            return 0
    
    def get_curve(self):
        return self.filtered_signal