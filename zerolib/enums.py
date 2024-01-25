""" Standard enums used by zerolib.

Common enums are stored here.
"""
from enum import Enum

### MESSAGE TYPES
class MessageType(Enum):
    SENSOR_DATA = 1
    ACTION = 2
    NOTIFICATION = 3
    ENGINE_PROGRAM_SETTINGS = 4

### ACTIONS
class ActionType(Enum):
    OPEN_FILL = 1
    CLOSE_FILL = 2
    ENABLE_TANK_HEATING = 3
    DISABLE_TANK_HEATING = 4
    FIRE_IGNITOR = 5
    SAFE_IGNITOR = 6
    BEGIN_BURN_PHASE = 7
    ABORT_BURN_PHASE = 8
    ABORT = 9
    OPEN_VENT = 10
    CLOSE_VENT = 11

### SENSORS
class SensorType(Enum):
    THRUST = 1
    TANK_MASS = 2
    THERMOCOUPLE = 3
    TANK_PRESSURE = 4
    CC_PRESSURE = 5
    BATTERY_LEVEL = 6
    LOAD_CELL = 7
    FUEL_VALVE_THROTTLE = 8
    OXIDIZER_VALVE_THROTTLE = 9
    MDOT = 10

# The first value is used for logging and communications, as well as the default
# for plotting.
SENSOR_UNITS = {
    SensorType.THRUST : ["lbf", "kN"],
    SensorType.TANK_MASS : ["kg", "lb"],
    SensorType.THERMOCOUPLE : ["degC", "K"],
    SensorType.TANK_PRESSURE : ["psi", "MPa", "bar"],
    SensorType.CC_PRESSURE : ["psi", "MPa", "bar"],
    SensorType.BATTERY_LEVEL : ["dimensionless"],
    SensorType.LOAD_CELL : ["kg", "lb"],
    SensorType.FUEL_VALVE_THROTTLE : ["dimensionless"],
    SensorType.OXIDIZER_VALVE_THROTTLE : ["dimensionless"],
    SensorType.MDOT : ["kg/s", "g/s"]
}

# The range should be specified in the default units.
SENSOR_RANGE = {
    SensorType.THRUST : [-20, 220],
    SensorType.TANK_MASS : [0, 35],
    SensorType.THERMOCOUPLE : [-20, 300],
    SensorType.TANK_PRESSURE : [0, 1000],
    SensorType.CC_PRESSURE : [0, 300],
    SensorType.BATTERY_LEVEL : [0, 100],
    SensorType.LOAD_CELL : [0, 10],
    SensorType.FUEL_VALVE_THROTTLE : [0, 1],
    SensorType.OXIDIZER_VALVE_THROTTLE : [0, 1],
    SensorType.MDOT : [0, 1]
}

# Standard deviation of measured noise in default units.
SENSOR_NOISE = {
    SensorType.THRUST : 1,
    SensorType.TANK_MASS : 0.1,
    SensorType.THERMOCOUPLE : 0.1,
    SensorType.TANK_PRESSURE : 10,
    SensorType.CC_PRESSURE : 3,
    SensorType.BATTERY_LEVEL : 1,
    SensorType.LOAD_CELL : 0.1,
    SensorType.FUEL_VALVE_THROTTLE : 0,
    SensorType.OXIDIZER_VALVE_THROTTLE : 0,
    SensorType.MDOT : 0.01
}

# The type of the raw reading supplied by the sensor board. See the
# documentation for the python library 'struct' for information about the type.
SENSOR_READING_TYPE = {
    SensorType.THRUST : "I",
    SensorType.THERMOCOUPLE : "H",
    SensorType.TANK_PRESSURE : "H",
    SensorType.CC_PRESSURE : "H",
    SensorType.BATTERY_LEVEL : "H",
    SensorType.LOAD_CELL : "I"

}

def get_default_sensor_units(u):
    return {
        stype : u( SENSOR_UNITS[stype][0] ) for stype in SensorType
    }

def get_estimated_sensor_noise(u):
    du = get_default_sensor_units(u)
    #for stype in du:
    #    if du[stype].is_compatible_with(u("K")):
    #        du[stype] = u(f"delta_{str(du[stype].units)}")

    return {
        stype : u.Quantity(SENSOR_NOISE[stype], du[stype]) for stype in SensorType
    }
