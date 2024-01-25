""" High throughput ADS1120 driver.

Does not support all chip features. This driver runs the chip in "turbo mode"
with all inputs assumed to be single-ended, and an analog vref provided.
"""
import time

from adafruit_bus_device.spi_device import SPIDevice
from busio import SPI
from digitalio import DigitalInOut

CMD_NOP = 0xFF
CMD_WREG = 0x40
CMD_RREG = 0x20
CMD_RESET = 0x06
CMD_START_SYNC = 0x08

class ADS1120:
    """ Baseline high-throughput ADS1120 driver.

    Does not support all features on the chip. This particular driver runs the
    ADC in turbo mode at 2k SPS. The gain is set to 1 and the PGA bypassed. No
    50/60 Hz rejection is performed and the voltage reference is set to AVDD.

    Many implementations seem to add random delays everywhere. They are not
    necessary except after the chip resets and in order to give the chip time to
    acquire a new reading.
    """
    def __init__(self, spi : SPI, cs : DigitalInOut):
        # IMPORTANT: phase=1
        self.dev = SPIDevice(spi, cs, baudrate=1000000, phase=1)
        
        # Remember the multiplexer state, switch if necessary to perform a read.
        self.mux_state = None
    
    def initialize(self):
        self.reset()
        # Chip needs 50us, we will give it 1ms
        time.sleep(0.001)

        # REG0: MUX[3:0], GAIN[2:0], PGA_BYPASS
        self.write_register(0, 0b10000001)
        # REG1: DR[2:0], MODE[1:0], CM, TS, BCS
        self.write_register(1, 0b11010100)
        # REG2: VREF[1:0], 50/60[1:0], PSW, IDAC[2:0]
        self.write_register(2, 0b11000000)
        # REG3: I1MUX[2:0], I2MUC[2:0], DRDYM, 0
        # Defaults are ok.

        self.start_sync()

    def read(self, mux_state):
        if self.mux_state != mux_state:
            self.set_multiplexer(mux_state)
            time.sleep(1/1800) # Allow the sensor time to acquire a reading
        
        return self._read()

    def reset(self):
        self.send_command(CMD_RESET)
    
    def start_sync(self):
        self.send_command(CMD_START_SYNC)

    def _read(self):
        rdata = bytearray(2)

        with self.dev as spi:
            spi.readinto(rdata, write_value=CMD_NOP)
        
        val = (rdata[0] << 8) | rdata[1]
        return val / 2**15 * 5 # Converted to voltage

    def read_register(self, address):
        recv = bytearray(1)

        with self.dev as spi:
            spi.write([ (address<<2) | CMD_RREG ])
            spi.readinto(recv, write_value=CMD_NOP)

        return recv[0]
    
    def send_command(self, cmd):
        with self.dev as spi:
            spi.write([cmd])

    def write_register(self, address, byte):
        with self.dev as spi:
            spi.write([
                (address<<2) | CMD_WREG,
                byte
            ])
    
    def print_registers(self):
        reg0 = self.read_register(0)
        reg1 = self.read_register(1)
        reg2 = self.read_register(2)
        reg3 = self.read_register(3)
        print("----REGISTERS----")
        print(reg0, reg1, reg2, reg3)
    
    def set_multiplexer(self, value):
        if not isinstance(value, int) or not 0 <= value <= 3:
            raise RuntimeError(f"Bad mux value {value}.")

        self.mux_state = value
        self.write_register(0, 0b10000001 + (value<<4))