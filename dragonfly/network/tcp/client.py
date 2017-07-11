from threading import Thread, Event
from queue import Queue, Empty as QueueEmpty
from socket import socket, AF_INET, SOCK_STREAM
from select import select

import hive

from ...event import OnTick


class TCPClientClass:

    @hive.types(local_address="tuple", select_interval='float', buffer_size='int')
    def __init__(self, local_address=("localhost", 0), select_interval=0.01, buffer_size=1024):
        self._local_address = local_address
        self._socket = socket(AF_INET, SOCK_STREAM)
        self._socket.bind(local_address)

        self.received_data = None
        self.outgoing_data = None
        self.server_address = None

        self._received_queue = Queue()
        self._outgoing_queue = Queue()

        self._connected_state = False
        self._acknowledged_connected_state = False

        self._hive = hive.get_run_hive()
        self._thread = Thread(target=self._handle_connections_threaded, daemon=True)

        self._buffer_size = buffer_size
        self._select_interval = select_interval

        # TODO cleanup functions to close thread

    def do_connect(self):
        assert not self._thread.is_alive()
        self._thread.start()

    def do_send(self):
        self._outgoing_queue.put(self.outgoing_data)

    def _sync_received_data(self):
        received_queue = self._received_queue

        while True:
            try:
                data = received_queue.get_nowait()

            except QueueEmpty:
                break

            received_queue.task_done()

            self.received_data = data
            self._hive._on_received()

    def _sync_connections(self):
        if self._acknowledged_connected_state != self._connected_state:
            if self._connected_state:
                self._hive._on_connected()

            else:
                self._hive._on_disconnected()

            self._acknowledged_connected_state = self._connected_state

    def synchronise(self):
        self._sync_received_data()
        self._sync_connections()

    def _handle_connections_threaded(self):
        self._socket.connect(self.server_address)
        self._connected_state = True

        main_socket = self._socket
        received_queue = self._received_queue
        outgoing_queue = self._outgoing_queue

        while True:
            readable, _, _ = select([main_socket], (), (), self._select_interval)

            # Receive data
            for sock in readable:
                data, address = sock.recvfrom(self._buffer_size)
                if not data:
                    # On disconnected
                    self._connected_state = False
                    return

                else:
                    received_queue.put(data)

            # Send data
            while True:
                try:
                    data = outgoing_queue.get_nowait()

                except QueueEmpty:
                    break

                outgoing_queue.task_done()
                main_socket.send(data)


def build_server(cls, i, ex, args):
    i.connect_address = hive.property(cls, "server_address", "tuple")
    i.push_connect = hive.push_in(i.connect_address)
    ex.connect_to = hive.antenna(i.push_connect)

    i.do_connect = hive.triggerable(cls.do_connect)
    hive.trigger(i.push_connect, i.do_connect)

    # Hive callbacks
    i.on_disconnected = hive.triggerfunc()
    i.on_connected = hive.triggerfunc()
    i.on_received = hive.triggerfunc()

    # Receiving connection
    ex.on_connected = hive.hook(i.on_connected)

    # Lost connection
    ex.on_disconnected = hive.hook(i.on_disconnected)

    # Receiving
    i.received_data = hive.property(cls, "received_data", "bytes")
    i.push_received = hive.push_out(i.received_data)
    ex.on_received = hive.output(i.push_received)

    hive.trigger(i.on_received, i.push_received)

    # Sending
    i.outgoing_data = hive.property(cls, "outgoing_data", "bytes")
    i.push_outgoing_data = hive.push_in(i.outgoing_data)
    ex.send = hive.antenna(i.push_outgoing_data)

    i.do_send_data = hive.triggerable(cls.do_send)
    hive.trigger(i.push_outgoing_data, i.do_send_data)

    i.synchronise_data = hive.triggerable(cls.synchronise)
    i.on_tick = OnTick()
    hive.connect(i.on_tick.on_tick, i.synchronise_data)


TCPClient = hive.hive("TCPClient", build_server, drone_class=TCPClientClass)
