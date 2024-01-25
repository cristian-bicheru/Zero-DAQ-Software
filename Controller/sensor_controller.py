""" Main logic for reading the sensors.

"""
import time
import logging
import numpy as np

logger = logging.getLogger(__name__)

from threading import Thread

try:
    from sensor_array import SensorArray
except (NotImplementedError, AttributeError):
    logger.critical("Sensor driver import failed! This can be ignored if running in debug mode.")

from zerolib.datalogging import DataLogger

DATA_DELAY = 1/60 # Send data at a peak of 60 Hz

class SensorController:
    """ Class to continously sample the sensors at (roughly) the specified rates.
    """
    def __init__(self, sensor_config, peripheral_manager):
        self.thread = None
        self.running = False
        self.data_callback = None
        self.init_time = time.perf_counter()
        
        self.p_mgr = peripheral_manager
        self.sens_cfg = sensor_config
        self.array = SensorArray(peripheral_manager)

        self.physical_sensors = [
            sensor for sensor in sensor_config.get_sensors()
            if self.array.is_physical_sensor(sensor)
        ]
        self.num_sensors = len(self.physical_sensors)

        # Target time per loop iteration
        self.loop_timestep = None
        # Number of iterations per reading for each sensor
        self.mods = {}

        self.data_logger = DataLogger()
        self.data_logger.start()
        # Make the header
        self.data_logger.add_row(
            "Time [s]," + ','.join([
                f"{sensor.get_name()} [{sensor.get_units()[0]}]"
                for sensor in self.physical_sensors
            ])
        )

        self.compute_delay_parameters()

    def register_callback(self, fn):
        self.data_callback = fn

    def compute_delay_parameters(self):
        hfreq = max([sensor.get_rate() for sensor in self.physical_sensors])
        
        self.loop_timestep = 1/hfreq
        self.mods = {
            sensor : int( hfreq / sensor.get_rate() )
            for sensor in self.physical_sensors
        }

    def mainloop(self):
        i = 0
        last_time = time.perf_counter()

        data_row = {sensor:[] for sensor in self.physical_sensors}
        next_cb_time = time.perf_counter() + DATA_DELAY

        while True:
            timestamp = last_time-self.init_time
            row = f"{timestamp},"

            j = 0
            for sensor, mod in self.mods.items():
                # Readings are staggered to reduce jitter
                j += 1
                if (i+j) % mod == 0:
                    reading = self.array.read(sensor)
                    
                    if reading is None:
                        # There was an error... Logs are sent to the monitor.
                        row += "Ø,"
                        continue

                    data_row[sensor].append(reading)
                    row += f"{reading},"
                else:
                    row += "Ø,"

            if time.perf_counter() > next_cb_time:
                # Average collected data
                avg_data = [
                    (sensor.get_id(), np.mean(values))
                    for sensor, values in data_row.items()
                    if values
                ]
                # Pass it to the callback
                self.data_callback(timestamp, avg_data)
                # Refresh the params
                next_cb_time = time.perf_counter() + DATA_DELAY
                data_row = {sensor:[] for sensor in self.physical_sensors}

            self.data_logger.add_row(row[:-1])
            i += 1
            
            sleep_time = self.loop_timestep - (time.perf_counter() - last_time)
            if sleep_time > 0:
                time.sleep(sleep_time)

            last_time = time.perf_counter()

    def start_collection(self):
        # Entry point.
        if not self.data_callback:
            raise RuntimeError("Data callback must be provided!")

        self.thread = Thread(
            target=self.mainloop,
            daemon=True, name="SensorControllerMainThread"
        )
        self.running = True
        self.thread.start()

    def stop(self):
        self.running = False
        self.thread.join()