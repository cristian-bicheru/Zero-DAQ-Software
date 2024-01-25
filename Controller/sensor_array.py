""" Interface to the sensor hardware.

Adafruit drivers are used as much of the work has already been done. The only
exception is the ADS1120 chip which did not have a driver available.
"""
import collections
import logging
import time

import board
import adafruit_bitbangio as bitbangio

from digitalio import DigitalInOut
from adafruit_max31855 import MAX31855
from adafruit_tca9548a import TCA9548A
from cedargrove_nau7802 import NAU7802, ConversionRate

from zerolib.ads1120 import ADS1120
from zerolib.enums import SensorType

from sensor_calib import apply_calibration

logger = logging.getLogger(__name__)

### PINOUT
# TC Sensor Bindings
TC_CS = [
    board.D6,  # TC 1 CS on GPIO 6
    board.D17, # TC 2 CS on GPIO 17
    board.D27, # TC 3 CS on GPIO 27
    board.D22, # TC 4 CS on GPIO 22
    board.D5   # TC 5 CS on GPIO 5
]

ADC_CS = board.D4 # ADC CS on GPIO 4
# ADC Sensor Bindings
ADC_CHANNELS = {
    SensorType.BATTERY_LEVEL : 2,
    SensorType.CC_PRESSURE : 0,
    SensorType.TANK_PRESSURE : 1
}

# Time in seconds between log propagation.
LOG_TIMEOUT = 1


class SensorArray:
    """
    LC1-3 are the mdot load cells
    LC4 is the thrust load cell
    """
    def __init__(self, peripheral_manager):
        # Store a ref to the perf_mgr to read valve states
        self.perf_mgr = peripheral_manager

        # Using software SPI, hardware SPI appears to not work
        self.spi = bitbangio.SPI(board.D11, MISO=board.D9, MOSI=board.D10)
        # Hardware I2C. Make sure to boost the Pi I2C freq to 400khz!
        self.i2c = board.I2C()

        # Default MAX31855 baudrate is set to 100khz. Increase this to 2 MHz
        self.TCs = [
            MAX31855(self.spi, DigitalInOut(pin))
            for pin in TC_CS
        ]

        # Using custom ADS1120 driver. Important to initialize after all of the
        # CS pins have been defined and TCs instantiated to prevent SPI collision.
        self.ADC = ADS1120(self.spi, DigitalInOut(ADC_CS))
        self.ADC.initialize()

        # TC9548A IC is used to multiplex the 4x NAU7802 load cells
        self.I2C_switch = TCA9548A(self.i2c)
        # The first four channels of the switch are used
        self.LCs = [
            NAU7802(self.I2C_switch[i], address=0x2A, active_channels=1)
            for i in range(4)
        ]
        for lc in self.LCs:
            lc._c2_conv_rate = ConversionRate.RATE_80SPS
        [lc.enable(True) for lc in self.LCs]

        # Sensors are read frequently, so we need to throttle logs to prevent
        # flooding the console.
        self.last_log_time = collections.defaultdict(lambda: 0)

    def read(self, sensor):
        # Perform sensor lookup and call the respective method.
        try:
            reading = None

            match sensor.get_type():
                case SensorType.CC_PRESSURE | SensorType.TANK_PRESSURE:
                    reading = self.ADC.read(ADC_CHANNELS[sensor.get_type()])

                case SensorType.BATTERY_LEVEL:
                    reading = self.ADC.read(
                        ADC_CHANNELS[sensor.get_type()] + (sensor.get_number()-1)
                    )
                
                case SensorType.LOAD_CELL:
                    reading = self.LCs[sensor.get_number() - 1].read()

                case SensorType.THRUST:
                    reading = self.LCs[3].read()

                case SensorType.THERMOCOUPLE:
                    reading = self.TCs[sensor.get_number() - 1].temperature
                
                case SensorType.OXIDIZER_VALVE_THROTTLE:
                    reading = self.perf_mgr.oxidizer_valve.get_state()
                
                case SensorType.FUEL_VALVE_THROTTLE:
                    reading = self.perf_mgr.fuel_valve.get_state()

                case _:
                    logger.error("Tried to read from a sensor that does not exist!")
                    return

            return apply_calibration(sensor, reading)
        except Exception as e:
            self.log_error(sensor, e)

    def log_error(self, sensor, error):
        # Log a sensor reading failure, with timeout to prevent flooding.
        error_time = time.perf_counter()
        if error_time - self.last_log_time[sensor] < LOG_TIMEOUT:
            return
        
        logger.critical(f"{sensor.get_name()}: {error}")
        self.last_log_time[sensor] = error_time

    def is_physical_sensor(self, sensor):
        """
        return True if the sensor is not a computed quantity -- i.e it is
        an actual sensor to be read by this class.
        """
        return sensor.get_rate() is not None
