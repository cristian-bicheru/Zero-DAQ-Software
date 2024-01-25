"""Handles communications between the controller and monitor software.

The communications library defines the MessageServer class, used to create a
bidrectional link between two applications. The link is powered by a PyZMQ
socket. Only zerolib.Message instances can be sent across the link. The messages
are serialized to a bytearray before transmission to save bandwidth (data is not
sent as plaintext).
"""
import zmq
import time
import logging
import traceback

from threading import Thread, Event
from queue import Queue

from zerolib.message import Message, MessageType

logger = logging.getLogger(__name__)

# Heartbeat constants
PING_BYTES = b"ZERO PING"
HEARTBEAT_HZ = 10

# Default port mappings
DEFAULT_MONITOR_PORT = 9376
DEFAULT_CONTROLLER_PORT = 9378

class ThreadedBidirectionalSocket:
    """ Threaded wrapper around a PyZMQ socket.
    
    PyZMQ sockets are not thread-safe so they cannot be used by more than one
    thread. This class solves this issue by caching send/recv operations into
    a queue (caching operations are thread-safe) and executing them in a single
    thread.

    Caching is done in the send_queue and receive_queue. Incoming requests
    are detected by the Poller object and then pushed to the receive_queue.
    Outgoing requests are cached to the send_queue and pushed as fast as
    possible.

    NOTE: Binding the socket or connecting to a destination should be done
    before creating an instance.
    """

    def __init__(self, context):
        self.context = context
        self.host = None
        self.dest = None

        self.send_queue = Queue()
        self.receive_queue = Queue()

        self.push_thread = None
        self.pull_thread = None
        self.running = False

    def send(self, msg):
        self.send_queue.put(msg)

    def recv(self):
        return self.receive_queue.get()

    def bind(self, host):
        if self.running:
            raise RuntimeError("Attempted to bind socket while it is running!")
        self.host = host

    def connect(self, dest):
        if self.running:
            raise RuntimeError("Attempted to connect socket while it is running!")
        self.dest = dest

    def recv_loop(self):
        pull_socket = self.context.socket(zmq.PULL)
        pull_socket.setsockopt(zmq.CONFLATE, 1)

        if self.host:
            pull_socket.bind(self.host[0])
        elif self.dest:
            pull_socket.connect(self.dest[1])
    
        while self.running:
            self.receive_queue.put(pull_socket.recv())

    def send_loop(self):
        push_socket = self.context.socket(zmq.PUSH)
        push_socket.setsockopt(zmq.CONFLATE, 1)
        push_socket.setsockopt(zmq.IMMEDIATE, 1)

        if self.host:
            push_socket.bind(self.host[1])
        elif self.dest:
            push_socket.connect(self.dest[0])

        while self.running:
            push_socket.send(self.send_queue.get())

    def run(self):
        if not self.host and not self.dest:
            raise RuntimeError("Attempted to spawn an unconnected socket!")

        self.push_thread = Thread(
            target=self.send_loop,
            daemon=True, name="ThreadedSocketPushThread"
        )
        self.pull_thread = Thread(
            target=self.recv_loop,
            daemon=True, name="ThreadedSocketPullThread"
        )
        self.running = True
        self.push_thread.start()
        self.pull_thread.start()

    def stop(self):
        self.running = False
        self.push_thread.join()
        self.pull_thread.join()


class MessageServer:
    """
    Bidirectional Zero MQ server. Both the controller and monitor run an
    instance of this class to communicate. A simple zmq pair type socket is used
    instead of a traditional TCP socket.

    NOTE: Zero MQ sockets are **NOT** thread-safe!! So, socket operations must
    be handled by a single thread. To facilitate this, a ThreadedSocket object
    is used, which is just a zmq Socket wrapped in a send/receive queue.
    """
    def __init__(self, host=None, port=None, timeout=0.5):
        # Create a ZMQ context, allowing up to 4 threads to be used for I/O
        self.context = zmq.Context(4)
        self.socket = ThreadedBidirectionalSocket(self.context)

        # Only the server needs to bind to a port
        if host and port:
            self.socket.bind([
                f"tcp://{host}:{port}",
                f"tcp://{host}:{port+1}"
            ])
            logger.info(f"Server running at {host}, ports {port}, {port+1}.")
        else:
            logger.info("Client ZMQ socket initialized.")

        # Function hooks on request or connection status change
        self.request_hook = None
        self.connection_hook = None

        # Used to determine connection status changes
        self.connection_event = Event()
        self.last_msg_time = 0
        self.timeout = timeout
        self.connection_status = False

        # Three threads are required for server operation. The self.running
        # variable is continutally checked against within the thread loops.
        # Setting it to false will terminate threads.
        self.threads = [None, None, None]
        self.running = False # Lock not required, Python assignments are atomic.

    def connect(self, host, port):
        """
        Connect to another MessageServer.
        """
        self.socket.connect([
            f"tcp://{host}:{port}",
            f"tcp://{host}:{port+1}"
        ])
        logger.info(f"Connecting to {host}, ports {port}, {port+1}...")

    def dispatch(self, msg, log=True):
        """
        Send a zerolib.Message to another MessageServer.
        """
        try:
            self.socket.send(msg.to_bytes())
        except:
            logger.error("Error sending message.")
            self.format_traceback()
        
        if log and msg.get_type() != MessageType.SENSOR_DATA:
            logger.debug(f"Sent message of type {msg.get_type()}.")

    def register_request_hook(self, fn):
        self.request_hook = fn
        logger.info("Registered request hook.")

    def register_connection_hook(self, fn):
        self.connection_hook = fn
        logger.info("Registered connection hook.")

    def format_traceback(self):
        print()
        print("-"*10 + " TRACEBACK " + "-"*10)
        print(traceback.format_exc())
        print("-"*31)
        print()
    
    def update_connection_hook(self, status):
        if self.connection_hook:
            try:
                self.connection_hook(status)
            except:
                logger.error(
                    "Error calling connection status hook with status {status}."
                )
                self.format_traceback()

    def connection_polling_loop(self):
        """
        The code waits until the connection event is triggered, executes the
        connection hook if it exists, then it sleeps for the timeout duration and
        if the connection has been dropped, it runs the appropriate callback.
        """
        while self.running:
            # Blocks until the event is triggered by the receiver loop
            self.connection_event.wait()

            logger.info("Client connected.")
            self.connection_status = True
            self.update_connection_hook(True)

            while self.running:
                # Sleep for self.timeout seconds. If no message has been received
                # within the timespan, consider the connection to be timed out.
                time.sleep(self.timeout)

                if time.perf_counter() - self.last_msg_time > self.timeout:
                    self.connection_event.clear()
                    logger.warning("Client timed out.")
                    self.connection_status = False
                    self.update_connection_hook(False)
                    break

    def receiver_loop(self):
        """
        Main receiver loop. The code blocks until a message has been received by
        the ZMQ socket. Then, if it is a simple ping message, it is ignored.
        Otherwise, attempt to deserialize the bytes into a Message instance.
        """
        while self.running:
            # Blocks until a message has been received
            msg_bytes = self.socket.recv()

            # Update the connection status
            self.connection_event.set()
            self.last_msg_time = time.perf_counter()

            if msg_bytes == PING_BYTES:
                # This is just a heartbeat signal, don't proceed
                continue

            try:
                msg = Message.from_bytes(msg_bytes)
            except:
                logger.error("Error decoding message.")
                # Dump the traceback into the console for debugging
                self.format_traceback()
                return

            # Execute the callback with the deserialized message
            if self.request_hook:
                try:
                    self.request_hook(msg)
                except:
                    logger.error(
                        f"Failed to execute request hook on {msg.get_type()}."
                    )
                    self.format_traceback()

    def heartbeat_loop(self):
        """
        Continously ping the other server.
        """
        while self.running:
            self.socket.send(PING_BYTES)
            time.sleep(1/HEARTBEAT_HZ)

    def run(self):
        self.threads = [
            Thread(
                target=self.connection_polling_loop,
                daemon=True, name="MessageServerPollingThread"
            ),
            Thread(
                target=self.receiver_loop,
                daemon=True, name="MessageServerReceivingThread"
            ),
            Thread(
                target=self.heartbeat_loop,
                daemon=True, name="MessageServerHeartbeatThread"
            )
        ]
        self.running = True
        self.socket.run()
        [thd.start() for thd in self.threads]

    def stop(self):
        self.running = False
        [thd.join() for thd in self.threads]
        self.socket.stop()
