""" Datalogging class. Resistant to ctrl-c or process termination. Thread-safe.

Also implements the LogLogger class for writing logs to disk.
"""
import zlib
import datetime
import logging

from threading import Thread
from queue import Queue, Empty

class DataLogger:
    def __init__(self, filename=None, debug=False, prefix=None):
        if not filename:
            filename = datetime.datetime.today().strftime('%Y %b %d %I.%M %p')
        
        if debug:
            filename = f"DEBUG {filename}.csv.gz"
        else:
            filename = f"{filename}.csv.gz"
        
        if prefix:
            filename = f"{prefix} {filename}"

        self.filename = filename
        self.data_queue = Queue()
        self.thread = None
        self.running = False

    def add_row(self, row):
        self.data_queue.put((row + "\n").encode())

    def mainloop(self):
        compressor = zlib.compressobj(level=3)

        with open(f"Data/{self.filename}", mode="wb") as file:
            while self.running:
                try:
                    file.write(compressor.compress(self.data_queue.get(timeout=1)))
                except Empty:
                    pass
            file.write(compressor.flush())

    def start(self):
        self.thread = Thread(target=self.mainloop, name="DataLoggerThread", daemon=True)
        self.running = True
        self.thread.start()

    def close(self):
        self.running = False
        self.thread.join()


class LogLogger(logging.Handler, DataLogger):
    """ Write all logs to disk.
    
    """
    def __init__(self, filename=None, debug=False):
        DataLogger.__init__(self, filename, debug, "LOG")
        logging.Handler.__init__(self)

    def cleanup(self):
        DataLogger.close(self)
    
    def handle(self, record):
        self.add_row(self.format(record))
