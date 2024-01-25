""" Handle reading from the sensor configuration file.

The sensor config file is a .cfg file (parsed with the configparser Python
module).
"""
import configparser

from zerolib.enums import SensorType, SENSOR_UNITS, SENSOR_RANGE
from zerolib.enums import SENSOR_NOISE, SENSOR_READING_TYPE


class SensorConfiguration:
    """ Reads a sensor configuration file.
    
    """
    def __init__(self, config_file):
        self.config_file = config_file
        self.sensors = {} # sorted by ID
        self.sensors_by_name = {} # sorted by name


    def read_config(self):
        config = configparser.ConfigParser()

        r = config.read(self.config_file)
        if not r:
            raise FileNotFoundError(
                "Sensor configuration not found at {self.config_file}!"
            )

        self.sensor_names = config.sections()

        self.num_tabs = 0

        for sensor_name in self.sensor_names:
            sensor_data = config[sensor_name]

            sensor_type = getattr(SensorType, sensor_data["Type"])
            sensor_id = int(sensor_data["ID"])

            if "Number" in sensor_data:
                sensor_number = int(sensor_data["Number"])
            else:
                sensor_number = None

            if "Rate" in sensor_data:
                sensor_rate = int(sensor_data["Rate"])
            else:
                sensor_rate = None

            if "Tab" in sensor_data:
                tab = int(sensor_data["Tab"])-1
                self.num_tabs = max(self.num_tabs, tab+1)
            else:
                tab = 0

            self.sensors[sensor_id] = Sensor(
                sensor_name,
                sensor_type,
                sensor_id,
                rate = sensor_rate,
                number = sensor_number,
                tab = tab
            )

            self.sensors_by_name[sensor_name] = self.sensors[sensor_id]

    def get_sensors(self):
        return list(self.sensors.values())
    
    def get_tab_count(self):
        return self.num_tabs

    def get(self, s_id=None, name=None):
        if not s_id and not name:
            raise ValueError("Must specify either a sensor ID or a name!")
        return self.sensors[s_id] if s_id else self.sensors_by_name[name]
    
    def get_by_type(self, sensor_type):
        return [
            sensor for sensor in self.sensors.values()
            if sensor.get_type() == sensor_type
        ]


class Sensor:
    """ Stores data about an individual sensor.
    
    """
    def __init__(
            self, name, stype, s_id, rate=None, number=None, tab=0):
        self.name = name
        self.type = stype
        self.s_id = s_id
        self.rate = rate
        self.number = number
        self.tab = tab

    def get_name(self) -> str:
        return self.name

    def get_type(self) -> SensorType:
        return self.type

    def get_id(self) -> int:
        return self.s_id

    def get_rate(self) -> int | None:
        return self.rate

    def get_number(self) -> int | None:
        return self.number

    def get_tab(self) -> int:
        return self.tab

    def get_units(self) -> list[str]:
        return SENSOR_UNITS[self.type]

    def get_range(self) -> list[float]:
        return SENSOR_RANGE[self.type]

    def get_noise(self) -> float:
        return SENSOR_NOISE[self.type]

    def get_reading_type(self) -> str:
        return SENSOR_READING_TYPE[self.type]
