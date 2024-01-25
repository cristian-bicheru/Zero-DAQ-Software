### ADD IMPORT DIRECTORY
import sys
sys.path.append('../')

### LOGGING SETUP
import logging
from zerolib.standard import logging_config
logging.basicConfig(**logging_config)

from interface import HardwareInterface, ServoMapping

interface = HardwareInterface()

while True:
    x = float(input("Enter the duty cycle: "))
    interface.set_servo(ServoMapping.FUEL_VALVE, x)
