import time
import logging

from zerolib.message import MessageType, ActionType, SensorDataMessage, EngineProgramSettingsMessage

from sensor_controller import SensorController

logger = logging.getLogger(__name__)

class TestBenchController:
    """
    Handle the mainloop of the controller logic
    """

    def __init__(self, peripheral_manager, dispatcher, sens_cfg, test_program):
        self.peripheral_manager = peripheral_manager
        self.sens_cfg = sens_cfg

        self.dispatcher = dispatcher
        self.test_program = test_program

        self.sb_rx = SensorController(sens_cfg, peripheral_manager)
        self.sb_rx.register_callback(self.data_handler)
        
        self.initialization_time = time.perf_counter()

    def data_handler(self, timestamp, data):
        """
        data is an array of sensor, reading pairs.
        """
        msg = SensorDataMessage(timestamp, data)
        self.dispatcher.dispatch(msg)
    
    def send_engine_program_list(self, status):
        if status is True:
            logger.info("Sending engine program list to monitor...")
            self.dispatcher.dispatch(
                EngineProgramSettingsMessage(
                    False, ','.join( self.test_program.list_programs() )
                )
            )

    def handler(self, msg):
        if msg.get_type() == MessageType.ENGINE_PROGRAM_SETTINGS:
            if msg.is_assigning is False:
                logger.error("EngineProgramSettings message is set as non-assigning!")
                return
            
            if msg.payload == "":
                logger.error("No program is specified!")
                return
            
            self.test_program.load(f"../Engine Test Programs/{msg.payload}.prog")
            return

        if msg.get_type() != MessageType.ACTION:
            logger.error("Non-action type message received. This should not happen.")
            return
        
        action = msg.action
        logger.info(f"Received action type {action}.")
        match action:
            ### GENERAL ABORT SEQUENCE
            # Ensure that the propellant valves and fill valves are closed.
            # Then, open the vent valve.
            case ActionType.ABORT:
                self.test_program.abort()
                self.peripheral_manager.close_propellant_valves()
                self.peripheral_manager.fill_valve.close()
                self.peripheral_manager.vent_valve.open()
            
            ### BURN PHASE ABORT
            # Similar to the general abort sequence, but we will make sure that
            # the ignitor is safed and the vent valve is not opened (in case a
            # recycle is possible)
            case ActionType.ABORT_BURN_PHASE:
                self.test_program.abort()
                self.peripheral_manager.ignitor.safe()
                self.peripheral_manager.close_propellant_valves()
            
            ### INITIATE BURN PHASE
            # This is used to start the testing program (burn or cold flow)
            case ActionType.BEGIN_BURN_PHASE:
                self.test_program.run_program()

            ### All other cases are simple and handled by the hw interface.
            case _:
                self.peripheral_manager.execute_action(action)

    def mainloop(self):
        self.sb_rx.start_collection()

        while True:
            time.sleep(1)
    
    def run(self):
        self.mainloop()
