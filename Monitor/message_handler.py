""" Processor for incoming sensor data.

"""
import time

from zerolib.enums import SensorType, MessageType, SENSOR_UNITS

class MessageHandler:
    """ Handles incoming messages from the controller.
    
    """
    def __init__(self, units, sensor_config, menu, plot_arrays):
        self.units = units
        self.sens_cfg = sensor_config
        self.menu = menu
        self.plt_arrs = plot_arrays

        self.tank_mass_sensor = sensor_config.get_by_type(SensorType.TANK_MASS)[0]

        self.start_time = time.perf_counter()
        self.offset = 0

    def handle_sensor_data(self, msg):
        load_cell_data = 0

        for dp in msg.data:
            id, val = dp
            sensor = self.sens_cfg.get(s_id=id)

            val = self.units.Quantity(val, SENSOR_UNITS[sensor.get_type()][0])
            plt_arr = self.plt_arrs[sensor.get_tab()]
            plt_arr.add_datapoint(id, (msg.timestamp + self.offset, val))

            if sensor.get_type() == SensorType.LOAD_CELL:
                load_cell_data += val

        if load_cell_data != 0:
            plt_arr = self.plt_arrs[self.tank_mass_sensor.get_tab()]
            plt_arr.add_datapoint(
                self.tank_mass_sensor.get_id(),
                (msg.timestamp + self.offset, load_cell_data)
            )

    def update_offset(self):
        self.offset = time.perf_counter() - self.start_time

    def handle(self, msg):
        match msg.get_type():
            case MessageType.SENSOR_DATA:
                self.handle_sensor_data(msg)
            case MessageType.NOTIFICATION:
                self.menu.add_log(f"{msg.notification} (CONTROLLER)")
            case MessageType.ENGINE_PROGRAM_SETTINGS:
                self.menu.set_programs(msg.payload.split(','))