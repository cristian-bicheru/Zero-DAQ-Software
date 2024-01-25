""" Defines the Message ABC and its implementations.

These messages are transmitted over a MessageServer. Messages can be serialized
and deserialized for lower bandwidth requirements. The following message types
exist:
    SensorDataMessage   - Arbitrary length message containing sensor datapoints.
    ActionMessage       - Carries only an item from the ActionType enum.
    NotificationMessage - Carries a string. Encoded/decoded with UTF-8.
"""
import struct
import logging

from abc import ABC, abstractmethod

from zerolib.enums import MessageType, ActionType, SENSOR_READING_TYPE

logger = logging.getLogger(__name__)

# Each sensor data point is formatted as follows:
# Byte 1: Sensor ID (uchar8)
# Byte 2-5: Sensor Reading (float64)
SENSOR_DATA_FORMAT = struct.Struct("<Bd")

# Initializing classes for packing/unpacking data. Faster that calling
# struct.pack or struct.unpack directly.
BYTE_FORMAT = struct.Struct("<B")
DOUBLE_FORMAT = struct.Struct("<d")
USHORT_FORMAT = struct.Struct("<H")
UINT_FORMAT = struct.Struct("<I")

# Convert the sensor reading types into compiled struct objects. The raw values
# are either unsigned shorts or integers.
SENSOR_READING_FORMATS = {
    k:USHORT_FORMAT if v == "H" else UINT_FORMAT
    for k,v in SENSOR_READING_TYPE.items()
}

# Message class bindings
def get_message_class(m_type):
    match m_type:
        case MessageType.SENSOR_DATA:
            return SensorDataMessage
        case MessageType.ACTION:
            return ActionMessage
        case MessageType.NOTIFICATION:
            return NotificationMessage
        case MessageType.ENGINE_PROGRAM_SETTINGS:
            return EngineProgramSettingsMessage

    logger.error(f"Received message of type {m_type}, which is not supported.")
    raise TypeError("Unsupported message type.")


class Message(ABC):
    """ Generic Message ABC. To be implemented by the respective message types.
    
    """
    @staticmethod
    def from_bytes(msg_bytes):
        m_type = MessageType(msg_bytes[0])
        return get_message_class(m_type).create_from_bytes(msg_bytes[1:])

    def to_bytes(self):
        return BYTE_FORMAT.pack(self.get_type().value) + self.serialize_to_bytes()

    @abstractmethod
    def serialize_to_bytes(self):
        pass

    @staticmethod
    @abstractmethod
    def create_from_bytes():
        pass

    @staticmethod
    @abstractmethod
    def get_type():
        pass


class SensorDataMessage(Message):
    """ Message containing an arbitrary-length array of sensor data.
    
    """
    def __init__(self, timestamp, data):
        self.timestamp = timestamp
        self.data = data

    def serialize_to_bytes(self):
        data = b"".join([
            SENSOR_DATA_FORMAT.pack(*x) for x in self.data
        ])
        return DOUBLE_FORMAT.pack(self.timestamp) + data

    @staticmethod
    def create_from_bytes(msg_bytes):
        timestamp = DOUBLE_FORMAT.unpack(msg_bytes[:8])[0]
        data = list(SENSOR_DATA_FORMAT.iter_unpack(msg_bytes[8:]))
        return SensorDataMessage(timestamp, data)

    @staticmethod
    def get_type():
        return MessageType.SENSOR_DATA


class ActionMessage(Message):
    """ Message containing an action defined in ActionType.
    
    """
    def __init__(self, action):
        self.action = action

    def serialize_to_bytes(self):
        return BYTE_FORMAT.pack(self.action.value)

    @staticmethod
    def create_from_bytes(msg_bytes):
        return ActionMessage(
            ActionType( msg_bytes[0] )
        )

    @staticmethod
    def get_type():
        return MessageType.ACTION


class NotificationMessage(Message):
    """ Message wrapping a notification (string) to be displayed on the console.
    
    """
    def __init__(self, notification):
        self.notification = notification

    def serialize_to_bytes(self):
        return self.notification.encode("utf-8")

    @staticmethod
    def create_from_bytes(msg_bytes):
        return NotificationMessage(msg_bytes.decode("utf-8"))

    @staticmethod
    def get_type():
        return MessageType.NOTIFICATION


class EngineProgramSettingsMessage(Message):
    """ Used to configure the engine valve program

    The controller will send the available programs when the monitor connects.
    To set a program, the monitor...

    is_assigning - If this message is specifying a program to use. Otherwise, this
                   is just listing available programs.
    
    payload      - Available valve program listing or a program to load.
    """
    def __init__(self, is_assigning, payload):
        self.is_assigning = is_assigning
        self.payload = payload

    def serialize_to_bytes(self):
        return ( b"Y" if self.is_assigning else b"N" ) + self.payload.encode("utf-8")

    @staticmethod
    def create_from_bytes(msg_bytes):
        return EngineProgramSettingsMessage(
            True if chr(msg_bytes[0]) == "Y" else False,
            msg_bytes[1:].decode("utf-8")
        )

    @staticmethod
    def get_type():
        return MessageType.ENGINE_PROGRAM_SETTINGS


class LogForwarder(logging.Handler):
    """
    This class extends the logging.Handler class. It implements the handle
    method which is called whenever a record is added. The implementation
    formats the record and creates a NotificationMessage instance from the
    result. This is passed to a specified callback function if it exists. The
    intended use is for dispatching this message to the Monitor software for
    display on the dashboard console.
    """
    def handle(self, record):
        if hasattr(self, "callback_fn"):
            self.callback_fn(
                NotificationMessage(self.format(record)), log = False
            )

    def set_callback(self, fn):
        self.callback_fn = fn
