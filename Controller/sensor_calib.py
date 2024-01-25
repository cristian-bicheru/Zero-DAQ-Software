""" Handles the application of calibration data on sensors.

The apply_calibration function is used to call the correct calibration function
with the data provided in this file.
"""
import numpy as np

from scipy.interpolate import interp1d

from zerolib.enums import SensorType


def linear_calibration(calib_data, rval):
    return (rval - calib_data[0]) * calib_data[1]

def fn_calibration(calib_fn, rval):
    return calib_fn(rval)


CALIBRATION_FUNCTIONS = {
    SensorType.LOAD_CELL : linear_calibration,
    SensorType.THRUST : linear_calibration,
    SensorType.CC_PRESSURE : linear_calibration,
    SensorType.TANK_PRESSURE : linear_calibration,
    SensorType.BATTERY_LEVEL : fn_calibration,
}

CALIBRATION_DATA = {
    SensorType.LOAD_CELL : {
        1 : ( 696.467*423.076, 1/(-423.076*1000)),
        2 : (-1835.83*437.764, 1/( 437.764*1000)),
        3 : ( 2666.21*436.016, 1/(-436.016*1000))
    },

    SensorType.THRUST : (-145500, -0.0000267753),

    # PTs are 0.5-4.5V.
    SensorType.CC_PRESSURE : (0.5, 300/4.),
    SensorType.TANK_PRESSURE : (0.5, 1000/4.),

    # Interpolate from data at https://blog.ampow.com/lipo-voltage-chart/
    SensorType.BATTERY_LEVEL : {
        1: interp1d(
            x = np.array([
                0.0, 13.09, 14.43, 14.75, 14.83, 14.91, 14.99, 15.06, 15.14, 15.18,
                16.26, 15.34, 15.42, 15.50, 15.66, 15.81, 15.93, 16.09, 16.33, 16.45,
                16.6, 16.8, 20.0
            ]) / 4, # Hardware uses 4:1 voltage divider.
            y = [0] + [x for x in range(0, 101, 5)] + [100],
            kind = "linear"
        ),
        2: lambda x: x # TODO: Calibrate servo battery sensor.
    },

    # Thermocouples, valve sensors do not require calibration
}


def apply_calibration(sensor, reading):
    # Some sensors don't require calibration
    if sensor.get_type() not in CALIBRATION_DATA.keys():
        return reading

    # If there are multiple sensors connected of the same type, get the
    # respective calibration data.
    if sensor.get_number():
        cdata = CALIBRATION_DATA[sensor.get_type()][sensor.get_number()]
    else:
        cdata = CALIBRATION_DATA[sensor.get_type()]

    return CALIBRATION_FUNCTIONS[sensor.get_type()](cdata, reading)
