""" Servo ball valve control.

"""
from enum import Enum

class ValveCalibration(Enum):
    # Calibration data for the valves
    FUEL_VALVE = {
        "closed_duty" : 0.98,
        "cracking_duty" : 0.93,
        "open_duty" : 0.74
    }
    OXIDIZER_VALVE = {
        "closed_duty" : 0.95,
        "cracking_duty" : 0.91,
        "open_duty" : 0.71
    }
    FILL_VALVE = {
        "closed_duty" : 0.98,
        "cracking_duty" : 0.92,
        "open_duty" : 0.74
    }
    VENT_VALVE = {
        "closed_duty" : 0.95,
        "cracking_duty" : 0.89,
        "open_duty" : 0.71
    }

class ServoBallValve:
    """
    Class implementing servo ball valve control. movement_range cooresponds to
    the range of pwm signal with the first value being the minimum (closed)
    state and the second value being the fully opened state. throttle_range
    likewise corresponds to the pwm values with minimum and maximum throttle,
    i.e, when the valve first cracks open and first fully opens.
    """
    def __init__(
            self, io_mapping, hw_interface, closed_duty=None, cracking_duty=None,
            open_duty=None, hardware_pwm=False
        ):
        if closed_duty is None or cracking_duty is None or open_duty is None:
            raise RuntimeError("All duty values must be specified!")

        self.port = io_mapping
        self.hw_itf = hw_interface
        self.closed_duty = closed_duty
        self.cracking_duty = cracking_duty
        self.open_duty = open_duty
        self.throttle_state = -1
        self.hardware_pwm = hardware_pwm
    
    def get_state(self):
        # return 0 for closed, 1 for open, and in between for throttled.
        return self.throttle_state
    
    def set_throttle(self, throttle):
        self.throttle_state = throttle

        x = self.cracking_duty + (
            self.open_duty - self.cracking_duty
        ) * throttle
        self.hw_itf.set_servo(self.port, x, hardware=self.hardware_pwm)
    
    def open(self):
        self.throttle_state = 1
        self.hw_itf.set_servo(self.port, self.open_duty, hardware=self.hardware_pwm)

    def close(self):
        self.throttle_state = 0
        self.hw_itf.set_servo(self.port, self.closed_duty, hardware=self.hardware_pwm)