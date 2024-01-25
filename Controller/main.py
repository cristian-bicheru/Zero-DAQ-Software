### ADD IMPORT DIRECTORY
import sys
sys.path.append('../')

### LOGGING SETUP
import logging
from zerolib.standard import logging_config
logging.basicConfig(**logging_config)

### IMPORTS
import os
import signal
from argparse import ArgumentParser
from pint import UnitRegistry

from zerolib.communications import MessageServer, DEFAULT_MONITOR_PORT
from zerolib.sensorcfg import SensorConfiguration
from zerolib.standard import formatter_config, sensor_cfg_location
from zerolib.message import LogForwarder
from zerolib.datalogging import LogLogger

from controller import TestBenchController

from interface import HardwareInterface
from peripherals import PeripheralManager
from program import EngineTestProgram

#from hanging_threads import start_monitoring
#monitoring_thread = start_monitoring(seconds_frozen=0.5, test_interval=50)

### ARGUMENT PARSING
parser = ArgumentParser(prog="Zero Controller Software")
parser.add_argument(
    "--dest",
    default = "127.0.0.1",
    help = "The IP address of the monitor. If unspecified, localhost is used."
)
args = parser.parse_args()

### SETUP
u = UnitRegistry()

if not args.dest:
    logging.warning("Monitor IP not specified so using localhost.")
server = MessageServer()
server.connect(args.dest, DEFAULT_MONITOR_PORT)

# Log forwarding to monitor
log_fw = LogForwarder()
log_fw.set_callback(server.dispatch)
formatter = logging.Formatter(**formatter_config)
log_fw.setFormatter(formatter)
logging.getLogger().addHandler(log_fw)

# Log saving to disk
log_writer = LogLogger()
log_writer.setFormatter(formatter)
log_writer.start()
logging.getLogger().addHandler(log_writer)

# Read the sensor configuration
sens_cfg = SensorConfiguration(sensor_cfg_location)
sens_cfg.read_config()

# Initialize the hardware interface and peripheral manager
interface = HardwareInterface()
peripheral_manager = PeripheralManager(interface)
peripheral_manager.set_default_states()

# Initialize the valve programming for this test
program = EngineTestProgram(peripheral_manager)

# Initialize the controller
controller = TestBenchController(peripheral_manager, server, sens_cfg, program)

### SETUP SERVER
server.register_request_hook(controller.handler)
server.register_connection_hook(controller.send_engine_program_list)
server.run()

def teardown_handler(*args, **kwargs):
    # Teardown the pigpio interface. Prevent KeyboardInterruprt during the
    # teardown process.
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    print("Cleaning up...")
    peripheral_manager.teardown()
    controller.sb_rx.data_logger.close()
    log_writer.cleanup()
    os.kill(os.getpid(), signal.SIGTERM)

signal.signal(signal.SIGINT, teardown_handler)

### RUN MAINLOOP
try:
    controller.run()
finally:
    teardown_handler()
