from socketserver import BaseRequestHandler, ThreadingMixIn, TCPServer as TCPServer_
from threading import Thread
from queue import Queue, Empty as QueueEmpty
from socket import socket, AF_INET, SOCK_STREAM
from select import select

import hive

from ...event import OnTick

# TODO datagrams


class TCPServerClass:

    @hive.types(select_interval='float', buffer_size='int')
    def __init__(self, select_interval=0.01, buffer_size=1024):
        self.local_address = None

        self._socket = socket(AF_INET, SOCK_STREAM)

        self.from_address = None
        self.received_data = None

        self.to_address = None
        self.outgoing_data = None

        self.connected_address = None
        self.disconnected_address = None

        self._received_queue = Queue()
        self._outgoing_queue = Queue()

        self._connected_queue = Queue()
        self._disconnected_queue = Queue()

        self._hive = hive.get_run_hive()
        self._thread = Thread(target=self._handle_connections_threaded, daemon=True)

        self._buffer_size = buffer_size
        self._select_interval = select_interval

        # TODO cleanup functions to close thread

    def do_bind(self):
        self._socket.bind(self.local_address)
        self._socket.listen()

        self._thread.start()

    def do_send(self):
        self._outgoing_queue.put((self.to_address, self.outgoing_data))

    def _sync_received_data(self):
        received_queue = self._received_queue

        while True:
            try:
                from_address, data = received_queue.get_nowait()

            except QueueEmpty:
                break

            received_queue.task_done()

            self.received_data = data
            self.from_address = from_address

            self._hive._on_received()

    def _sync_connections(self):
        connected_queue = self._connected_queue

        while True:
            try:
                address = connected_queue.get_nowait()

            except QueueEmpty:
                break

            connected_queue.task_done()

            self.connected_address = address
            self._hive._on_connected()

    def _sync_disconnections(self):
        disconnected_queue = self._disconnected_queue

        while True:
            try:
                address = disconnected_queue.get_nowait()

            except QueueEmpty:
                break

            disconnected_queue.task_done()

            self.disconnected_address = address
            self._hive._on_disconnected()

    def synchronise(self):
        self._sync_received_data()
        self._sync_connections()
        self._sync_disconnections()

    def _handle_connections_threaded(self):
        main_socket = self._socket
        active_sockets = [main_socket]

        received_queue = self._received_queue
        outgoing_queue = self._outgoing_queue

        address_to_socket = {}
        socket_to_address = {}

        while True:
            readable, _, _ = select(active_sockets, (), (), self._select_interval)

            # Receive data
            for sock in readable:
                if sock is main_socket:
                    connection_sock, address = main_socket.accept()
                    active_sockets.append(connection_sock)

                    # Map address and socket
                    address_to_socket[address] = connection_sock
                    socket_to_address[connection_sock] = address

                    # On connected
                    self._connected_queue.put(address)

                else:
                    data = sock.recv(self._buffer_size)
                    address = socket_to_address[sock]

                    if not data:
                        del address_to_socket[address]
                        del socket_to_address[sock]
                        active_sockets.remove(sock)

                        # On disconnected
                        self._disconnected_queue.put(address)

                    else:
                        received_queue.put((address, data))

            # Send data
            while True:
                try:
                    to_address, data = outgoing_queue.get_nowait()

                except QueueEmpty:
                    break

                outgoing_queue.task_done()
                try:
                    connection_sock = address_to_socket[to_address]

                except KeyError:
                    # TODO
                    continue

                connection_sock.send(data)


def build_server(cls, i, ex, args):
    i.local_address = hive.property(cls, "local_address", "tuple")
    i.push_bind_address = hive.push_in(i.local_address)
    ex.bind_to = hive.antenna(i.push_bind_address)

    i.do_bind = hive.triggerable(cls.do_bind)
    hive.trigger(i.push_bind_address, i.do_bind)

    # Receiving connection
    i.connected_address = hive.property(cls, "connected_address", "tuple")
    i.push_connected_address = hive.push_out(i.connected_address)
    ex.on_client_connected = hive.output(i.push_connected_address)

    # Receiving connection
    i.disconnected_address = hive.property(cls, "disconnected_address", "tuple")
    i.push_disconnected_address = hive.push_out(i.disconnected_address)
    ex.on_client_disconnected = hive.output(i.push_disconnected_address)

    # Receiving
    i.from_address = hive.property(cls, "from_address", "tuple")
    i.pull_from_address = hive.pull_out(i.from_address)
    ex.from_address = hive.output(i.pull_from_address)

    i.received_data = hive.property(cls, "received_data", "bytes")
    i.push_received = hive.push_out(i.received_data)
    ex.on_received = hive.output(i.push_received)

    # Hive callbacks
    i.on_disconnected = hive.triggerfunc()
    i.on_connected = hive.triggerfunc()
    i.on_received = hive.triggerfunc()

    hive.trigger(i.on_received, i.push_received)
    hive.trigger(i.on_connected, i.push_connected_address)
    hive.trigger(i.on_disconnected, i.push_disconnected_address)

    # Sending
    i.to_address = hive.property(cls, "to_address", "tuple")
    i.pull_to_address = hive.pull_in(i.to_address)
    ex.to_address = hive.antenna(i.pull_to_address)

    i.outgoing_data = hive.property(cls, "outgoing_data", "bytes")
    i.push_outgoing_data = hive.push_in(i.outgoing_data)
    ex.send = hive.antenna(i.push_outgoing_data)

    i.do_send_data = hive.triggerable(cls.do_send)
    hive.trigger(i.push_outgoing_data, i.pull_to_address, pretrigger=True)
    hive.trigger(i.push_outgoing_data, i.do_send_data)

    i.synchronise_data = hive.triggerable(cls.synchronise)
    i.on_tick = OnTick()
    hive.connect(i.on_tick.on_tick, i.synchronise_data)


TCPServer = hive.hive("TCPServer", build_server, drone_class=TCPServerClass)
