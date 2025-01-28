# SPDX-FileCopyrightText: Copyright (c) 2013-2014 micropython-lib contributors
# SPDX-FileCopyrightText: Copyright (c) 2024 lbuque
#
# SPDX-License-Identifier: MIT

import socket
import struct
import time
# from binascii import hexlify


class MQTTException(Exception):
    pass


class MQTTClient:
    DELAY = 2
    DEBUG = False
    StateConnecting = -5
    StateConnectionTimeout = -4
    StateConnectionLost = -3
    StateConnectionFailed = -2
    StateDisconnected = -1
    StateConnected = 0
    StateBadProtocol = 1
    StateBadClientId = 2
    StateUnavailable = 3
    StateBadCredentials = 4
    StateUnauthorized = 5

    def __init__(
        self,
        client_id,
        server,
        port=0,
        user=None,
        password=None,
        keepalive=0,
        ssl=None,
    ):
        if port == 0:
            port = 8883 if ssl else 1883
        self.client_id = client_id
        self.sock = None
        self.server = server
        self.port = port
        self.ssl = ssl
        self.pid = 0
        self.cb = None
        self.user = user
        self.pswd = password
        self.keepalive = keepalive
        self.lw_topic = None
        self.lw_msg = None
        self.lw_qos = 0
        self.lw_retain = False
        self.status = self.StateDisconnected

    def _send_str(self, s):
        self.sock.send(struct.pack("!H", len(s)))
        self.sock.send(s)

    def _recv_len(self):
        n = 0
        sh = 0
        while 1:
            b = self.sock.recv(1)[0]
            n |= (b & 0x7F) << sh
            if not b & 0x80:
                return n
            sh += 7

    def get_status(self):
        return self.status

    def set_callback(self, f):
        self.cb = f

    def set_last_will(self, topic, msg, retain=False, qos=0):
        assert 0 <= qos <= 2
        assert topic
        self.lw_topic = topic
        self.lw_msg = msg
        self.lw_qos = qos
        self.lw_retain = retain

    def connect(self, clean_session=True):
        self.status = self.StateConnecting  # added lbuque
        self.sock = socket.socket()
        addr = socket.getaddrinfo(self.server, self.port)[0][-1]
        self.sock.connect(addr)
        if self.ssl:
            self.sock = self.ssl.wrap_socket(self.sock, server_hostname=self.server)
        premsg = memoryview(bytearray(b"\x10\0\0\0\0\0"))
        msg = bytearray(b"\x04MQTT\x04\x02\0\0")

        sz = 10 + 2 + len(self.client_id)
        msg[6] = clean_session << 1
        if self.user:
            sz += 2 + len(self.user) + 2 + len(self.pswd)
            msg[6] |= 0xC0
        if self.keepalive:
            assert self.keepalive < 65536
            msg[7] |= self.keepalive >> 8
            msg[8] |= self.keepalive & 0x00FF
        if self.lw_topic:
            sz += 2 + len(self.lw_topic) + 2 + len(self.lw_msg)
            msg[6] |= 0x4 | (self.lw_qos & 0x1) << 3 | (self.lw_qos & 0x2) << 3
            msg[6] |= self.lw_retain << 5

        i = 1
        while sz > 0x7F:
            premsg[i] = (sz & 0x7F) | 0x80
            sz >>= 7
            i += 1
        premsg[i] = sz

        l = i + 2 if len(premsg) > i + 2 else len(premsg)
        self.sock.send(premsg[:l])
        self.sock.send(msg)
        # print(hex(len(msg)), hexlify(msg, ":"))
        self._send_str(self.client_id)
        if self.lw_topic:
            self._send_str(self.lw_topic)
            self._send_str(self.lw_msg)
        if self.user:
            self._send_str(self.user)
            self._send_str(self.pswd)
        resp = self.sock.recv(4)
        assert resp[0] == 0x20 and resp[1] == 0x02
        if resp[3] != 0:
            raise MQTTException(resp[3])
        self.status = self.StateConnected  # added lbuque
        return resp[2] & 1

    def disconnect(self):
        self.sock.send(b"\xe0\0")
        self.sock.close()
        self.status = self.StateDisconnected  # added lbuque

    def ping(self):
        self.sock.send(b"\xc0\0")

    def _publish(self, topic, msg, retain=False, qos=0):
        pkt = memoryview(bytearray(b"\x30\0\0\0"))
        pkt[0] |= qos << 1 | retain
        sz = 2 + len(topic) + len(msg)
        if qos > 0:
            sz += 2
        assert sz < 2097152
        i = 1
        while sz > 0x7F:
            pkt[i] = (sz & 0x7F) | 0x80
            sz >>= 7
            i += 1
        pkt[i] = sz
        # print(hex(len(pkt)), hexlify(pkt, ":"))
        l = i + 1 if len(pkt) > i + 1 else len(pkt)
        self.sock.send(pkt[:l])
        self._send_str(topic)
        if qos > 0:
            self.pid += 1
            pid = self.pid
            struct.pack_into("!H", pkt, 0, pid)
            self.sock.send(pkt[:2])
        self.sock.send(msg)
        if qos == 1:
            while 1:
                op = self._wait_msg()
                if op == 0x40:
                    sz = self.sock.recv(1)
                    assert sz == b"\x02"
                    rcv_pid = self.sock.recv(2)
                    rcv_pid = rcv_pid[0] << 8 | rcv_pid[1]
                    if pid == rcv_pid:
                        return
        elif qos == 2:
            assert 0

    def subscribe(self, topic, qos=0):
        assert self.cb is not None, "Subscribe callback is not set"
        pkt = bytearray(b"\x82\0\0\0")
        self.pid += 1
        struct.pack_into("!BH", pkt, 1, 2 + 2 + len(topic) + 1, self.pid)
        # print(hex(len(pkt)), hexlify(pkt, ":"))
        self.sock.send(pkt)
        self._send_str(topic)
        self.sock.send(qos.to_bytes(1, "little"))
        self.sock.setblocking(True)
        while 1:
            op = self._wait_msg()
            if op == 0x90:
                resp = self.sock.recv(4)
                # print(resp)
                assert resp[1] == pkt[2] and resp[2] == pkt[3]
                if resp[3] == 0x80:
                    raise MQTTException(resp[3])
                return

    # Wait for a single incoming MQTT message and process it.
    # Subscribed messages are delivered to a callback previously
    # set by .set_callback() method. Other (internal) MQTT
    # messages processed internally.
    def _wait_msg(self):
        res = self.sock.recv(1)
        self.sock.setblocking(True)
        if res is None:
            return None
        if res == b"":
            raise OSError(-1)
        if res == b"\xd0":  # PINGRESP
            sz = self.sock.recv(1)[0]
            assert sz == 0
            return None
        op = res[0]
        if op & 0xF0 != 0x30:
            return op
        sz = self._recv_len()
        topic_len = self.sock.recv(2)
        topic_len = (topic_len[0] << 8) | topic_len[1]
        topic = self.sock.recv(topic_len)
        sz -= topic_len + 2
        if op & 6:
            pid = self.sock.recv(2)
            pid = pid[0] << 8 | pid[1]
            sz -= 2
        msg = self.sock.recv(sz)
        self.cb(topic, msg)
        if op & 6 == 2:
            pkt = bytearray(b"\x40\x02\0\0")
            struct.pack_into("!H", pkt, 2, pid)
            self.sock.send(pkt)
        elif op & 6 == 4:
            assert 0
        return op

    def wait_msg(self):
        while 1:
            try:
                return self._wait_msg()
            except OSError as e:
                if e.errno in (11, 35):
                    return None
                self.status = self.StateDisconnected  # added lbuque
                self.log(False, e)
            self.reconnect()

    # Checks whether a pending message from server is available.
    # If not, returns immediately with None. Otherwise, does
    # the same processing as wait_msg.
    def check_msg(self, attempts=2):
        while attempts:
            self.sock.setblocking(False)
            try:
                return self._wait_msg()
            except OSError as e:
                if e.errno in (11, 35):
                    return None
                self.status = self.StateDisconnected  # added lbuque
                self.log(False, e)
            self.reconnect()
            attempts -= 1

    def delay(self, i):
        time.sleep(self.DELAY)

    def log(self, in_reconnect, e):
        if self.DEBUG:
            if in_reconnect:
                print("mqtt reconnect: %r" % e)
            else:
                print("mqtt: %r" % e)

    def reconnect(self):
        i = 0
        while 1:
            try:
                return self.connect(False)
            except OSError as e:
                self.log(True, e)
                i += 1
                self.delay(i)

    def publish(self, topic: bytes | bytearray, msg: bytes | bytearray, retain=False, qos=0):
        while 1:
            try:
                return self._publish(topic, msg, retain, qos)
            except OSError as e:
                self.status = self.StateDisconnected  # added lbuque
                self.log(False, e)
            self.reconnect()
