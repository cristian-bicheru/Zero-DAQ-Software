import logging

from zerolib.enums import ActionType
from zerolib.message import ActionMessage
from zerolib.communications import DEFAULT_CONTROLLER_PORT

logger = logging.getLogger(__name__)

ACTION_BUTTONS = [
    "Fill Valve",
    "Vent Valve",
    "Tank Heating",
    "Fire Ignitor",
    "Startup Sequence",
    "Abort",
]

class ActionDispatcher:
    def __init__(self, zmq_server, dest="", port=DEFAULT_CONTROLLER_PORT):
        self.dest_addr = dest
        self.dest_port = port

        self.dispatcher = zmq_server
    
    def set_dest(self, dest):
        self.dest_addr = dest
        self.dispatcher.connect(self.dest_addr, self.dest_port)
    
    def get_callback(self, action):
        """
        Generates a callback for the requested action button. The callback is
        given one value (the state of the button) which determines which action
        to send.
        """
        tv = fv = None

        match action:
            case "Fill Valve":
                tv, fv = ActionType.OPEN_FILL, ActionType.CLOSE_FILL
            case "Tank Heating":
                tv, fv = ActionType.ENABLE_TANK_HEATING, ActionType.DISABLE_TANK_HEATING
            case "Fire Ignitor":
                tv, fv = ActionType.FIRE_IGNITOR, ActionType.SAFE_IGNITOR
            case "Startup Sequence":
                tv, fv = ActionType.BEGIN_BURN_PHASE, ActionType.ABORT_BURN_PHASE
            case "Abort":
                tv, fv = ActionType.ABORT, ActionType.ABORT
            case "Vent Valve":
                tv, fv = ActionType.OPEN_VENT, ActionType.CLOSE_VENT

        def f(x):
            axn = tv if x else fv
            self.dispatcher.dispatch(ActionMessage(axn))
            logger.info(f"Sending action {axn.name} to client.")
        
        return f