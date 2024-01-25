""" Zero Shield V2 HW Interface. Uses pigpio. Thread-safe.

"""
from enum import Enum
from threading import Lock

import logging
logger = logging.getLogger(__name__)

import pigpio

GPIO_LOCK = Lock()

def synchronized(func):
    def sync_func(*args, **kwargs):
        with GPIO_LOCK:
            func(*args, **kwargs)

    return sync_func

class IOMapping(Enum):
    IGNITOR_RELAY = 23
    HEATING_RELAY = 24
    WARNING_LIGHT = 25
    DANGER_LIGHT = 8

class ServoMapping(Enum):
    FILL_VALVE = 16
    VENT_VALVE = 26
    FUEL_VALVE = 13 # S2
    OXIDIZER_VALVE = 12 # S1

SERVO_PWM_FREQ = 180 #hz

class HardwareInterface:
    """ Controls the hardware outputs of the Zero Shield V2.
    """
    def __init__(self,):
        self.pi = pigpio.pi()
        self.servo_state = {}
        self.set_modes()

    def check_status(self):
        # Raise error if attempting to use IO on uninitialized or stopped status
        if not self.status:
            raise RuntimeError("Hardware interface is not active!")

    @synchronized
    def set_modes(self):
        for io in IOMapping:
            self.pi.set_mode(io.value, pigpio.OUTPUT)

        for io in ServoMapping:
            self.pi.set_mode(io.value, pigpio.OUTPUT)
            self.servo_state[io] = False
        
        self.status = True

    @synchronized
    def activate_relay(self, relay):
        self.check_status()
        logger.debug(f"Set pin {relay} to HIGH.")
        self.pi.write(relay, pigpio.HIGH)

    @synchronized
    def deactivate_relay(self, relay):
        self.check_status()
        logger.debug(f"Set pin {relay} to LOW.")
        self.pi.write(relay, pigpio.LOW)

    @synchronized
    def set_servo(self, servo, duty, hardware=False):
        # duty should be 0 to 1.
        self.check_status()
        if servo not in ServoMapping:
            raise RuntimeError("Unknown servo object!")
        pwm_type = "hardware" if hardware else "software"

        if duty == 0:
            self.servo_state[servo] = False

            if hardware:
                self.pi.hardware_PWM(servo.value, SERVO_PWM_FREQ, 0)
            else:
                self.pi.set_PWM_dutycycle(servo.value, 0)
                self.pi.set_PWM_frequency(servo.value, 0)

            logger.debug(f"Disabled {pwm_type} PWM on {servo}.")
        else:
            if not self.servo_state[servo]:
                self.servo_state[servo] = True
                if not hardware:
                    self.pi.set_PWM_frequency(servo.value, SERVO_PWM_FREQ)

            if hardware:
                self.pi.hardware_PWM(
                    servo.value, SERVO_PWM_FREQ,
                    int( duty * 0.0025 * SERVO_PWM_FREQ * 1000000 )
                )
            else:
                self.pi.set_servo_pulsewidth(servo.value, duty*2500)

            logger.debug(f"Set servo output to {duty*100:.4g}% on {servo} ({pwm_type} PWM).")

    @synchronized
    def teardown(self):
        self.pi.stop()
        self.status = False
