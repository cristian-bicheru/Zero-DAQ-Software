""" Implements the logic executing valve programs.

"""
import time
import logging
import os
from threading import Thread

logger = logging.getLogger(__name__)

class EngineTestProgram:
    """
    Load and execute a testing program. The program should be specified as a
    csv file with time, fuel valve position, oxidizer valve position, and ignitor status.
    """
    def __init__(self, peripheral_manager):
        self.program = []
        self.thread = None
        self.running = False
        self.pm = peripheral_manager
        self.callback = None

    def list_programs(self):
        return [
            filename.split(".prog")[0]
            for filename in os.listdir("../Engine Test Programs/")
            if filename.endswith(".prog")
        ]


    def load(self, filename):
        if not os.path.exists(filename):
            logger.error(f"File {filename} does not exist!")
            return
        
        if self.running is True:
            logger.error("Cannot set engine program while another is running!")
            return

        with open(filename, "r") as f:
            self.program = [
                list(map(float, row.split(','))) for row in f.readlines()
            ]

        for row in self.program:
            if len(row) != 4:
                logger.error("Malformed engine program.")
                print("Bad row:", row)

        logger.info(f"Successfully loaded program {filename}")

    def run_program(self, callback=None):
        self.running = True
        self.callback = callback
        self.thread = Thread(target=self._run, name="EngineProgramMainThread")
        self.thread.start()

    def abort(self):
        if self.thread is not None:
            self.running = False
            self.thread.join()
            self.thread = None
        else:
            logger.warning("Tried to abort test but no test is running!")

    def _run(self):
        i = 0
        stime = time.perf_counter()
        logger.warning("Executing valve program...")
        ign_off = True

        while self.running:
            ctime = time.perf_counter() - stime

            t2, fp2, op2, ign2 = self.program[i+1]

            if ctime > t2:
                i += 1
                if i+1 == len(self.program):
                    break
                continue

            t1, fp1, op1, ign1 = self.program[i]

            if t2 == t1:
                lerp = 1.
            else:
                lerp = (ctime - t1) / (t2 - t1)

            fp = fp1 + (fp2 - fp1) * lerp
            op = op1 + (op2 - op1) * lerp
            ign = ign1 + (ign2 - ign1) * lerp

            self.pm.fuel_valve.set_throttle(fp)
            self.pm.oxidizer_valve.set_throttle(op)

            if ign > 0.5:
                if ign_off:
                    self.pm.ignitor.fire()
                    ign_off = False
                    logger.warning("Ignitor activated.")
            elif not ign_off:
                self.pm.ignitor.safe()
                ign_off = True
                logger.warning("Ignitor safed.")

            # Give other parts of the program time to run
            time.sleep(0.01)

        self.pm.close_propellant_valves()
        self.pm.ignitor.safe()

        self.running = False

        logger.warning("Valve program complete.")

        if self.callback:
            self.callback()
