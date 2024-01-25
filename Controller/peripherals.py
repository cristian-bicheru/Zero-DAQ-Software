""" Implements the PeripheralManager which interfaces with the Zero Shield V2.

"""
from enum import Enum

from interface import IOMapping, ServoMapping
from servo import ServoBallValve, ValveCalibration
from zerolib.enums import ActionType

class LightStatus(Enum):
    Safe = 1
    Warning = 2
    Danger = 3

"""
Set this value appropriately if the vent valve is the throttling object. (I.e if
there is not a flow control orifice downstream of the vent valve)
"""
VENT_THROTTLE = 1

class RelayDevice:
    def __init__(self, io_mapping, hw_interface):
        self.hw_intf = hw_interface
        self.io_port = io_mapping.value
    
    def fire(self):
        self.hw_intf.activate_relay(self.io_port)

    def safe(self):
        self.hw_intf.deactivate_relay(self.io_port)

class PeripheralManager:
    """
    Peripherals are hardcoded as these are not expected to change.
    """
    def __init__(self, hw_interface):
        self.hw_intf = hw_interface

        ### VALVES
        self.fill_valve = ServoBallValve(
            ServoMapping.FILL_VALVE, hw_interface, **ValveCalibration.FILL_VALVE.value
        )
        self.vent_valve = ServoBallValve(
            ServoMapping.VENT_VALVE, hw_interface, **ValveCalibration.VENT_VALVE.value
        )
        self.fuel_valve = ServoBallValve(
            ServoMapping.FUEL_VALVE, hw_interface,
            **ValveCalibration.OXIDIZER_VALVE.value, hardware_pwm=True
        )
        self.oxidizer_valve = ServoBallValve(
            ServoMapping.OXIDIZER_VALVE, hw_interface,
            **ValveCalibration.FUEL_VALVE.value, hardware_pwm=True
        ) # SWAPPED FOR THIS TEST

        ### RELAY-CONTROLLED DEVICES
        self.tank_heater = RelayDevice(IOMapping.HEATING_RELAY, hw_interface)
        self.ignitor = RelayDevice(IOMapping.IGNITOR_RELAY, hw_interface)
        self.warning_light = RelayDevice(IOMapping.WARNING_LIGHT, hw_interface)
        self.danger_light = RelayDevice(IOMapping.DANGER_LIGHT, hw_interface)

        self.valves = [
            self.fill_valve, self.vent_valve, self.fuel_valve, self.oxidizer_valve
        ]
    
    def set_default_states(self):
        for valve in self.valves:
            valve.close()
        
        self.ignitor.safe()
        self.tank_heater.safe()
        self.warning_light.safe()
        self.danger_light.safe()

    def teardown(self):
        for valve in self.valves:
            valve.close()

        self.ignitor.safe()
        self.tank_heater.safe()
        self.warning_light.safe()
        self.danger_light.safe()

        self.hw_intf.teardown()
    
    def close_propellant_valves(self):
        self.fuel_valve.close()
        self.oxidizer_valve.close()

    def set_light_status(self, status):
        match status:
            case LightStatus.Safe:
                self.warning_light.safe()
                self.danger_light.safe()
            case LightStatus.Warning:
                self.warning_light.fire()
                self.danger_light.safe()
            case LightStatus.Danger:
                self.warning_light.fire()
                self.danger_light.fire()

    def execute_action(self, action):
        match action:
            ### FILL VALVE CONTROLS
            case ActionType.OPEN_FILL:
                self.fill_valve.open()
            case ActionType.CLOSE_FILL:
                self.fill_valve.close()

            ### VENT VALVE CONTROLS
            case ActionType.OPEN_VENT:
                self.vent_valve.set_throttle(VENT_THROTTLE)
            case ActionType.CLOSE_VENT:
                self.vent_valve.close()
            
            ### TANK HEATING
            case ActionType.ENABLE_TANK_HEATING:
                self.tank_heater.fire()
            case ActionType.DISABLE_TANK_HEATING:
                self.tank_heater.safe()

            ### IGNITOR
            case ActionType.FIRE_IGNITOR:
                self.ignitor.fire()
            case ActionType.SAFE_IGNITOR:
                self.ignitor.safe()