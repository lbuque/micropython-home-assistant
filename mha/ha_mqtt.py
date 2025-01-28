# SPDX-FileCopyrightText: Copyright (c) 2024 lbuque
#
# SPDX-License-Identifier: MIT

from .umqtt import MQTTClient


class HAMqtt:
    _instance = None

    def __new__(cls, *args, **kw):
        if cls._instance is None:
            cls._instance = object.__new__(cls)
        return cls._instance

    @classmethod
    def instance(cls):
        return cls._instance

    def __init__(self, device) -> None:
        self.discovery_prefix = "homeassistant"
        self.data_prefix = "homeassistant"
        self.device = device
        self.on_message = None
        self.on_connect = None
        self.on_disconnect = None
        self.on_state_changed = None
        self._device_types = []

        self._last_will_topic = None
        self._last_will_message = None
        self._last_will_retain = None

        self._client = None
        self._current_state = MQTTClient.StateDisconnected

    def get_state(self):
        raise NotImplementedError

    def begin(self, server, port=1883, user=None, password=None):
        self._client = MQTTClient(b"umqtt_client", server, port, user, password)
        self._client.connect()
        if self._last_will_topic is not None:
            self._client.set_last_will(
                self._last_will_topic, self._last_will_message, retain=self._last_will_retain
            )
        self._client.set_callback(self._on_message)

    def disconnect(self):
        if self._client is not None:
            self._client.disconnect()

    def loop(self):
        self._client.check_msg()

        status = self._client.get_status()
        if self._current_state != status:
            self._current_state = status
            if status == MQTTClient.StateConnected:
                self._on_connect(None, None, None, None, None)
            elif status == MQTTClient.StateDisconnected:
                self._on_disconnect(None, None, None)

    def is_connected(self):
        if self._client is None:
            return False
        return self._client.is_connected() == MQTTClient.StateConnected

    def add_device_type(self, device_type):
        self._device_types.append(device_type)

    def publish(self, topic, payload, retain=False):
        if self._client is None:
            return False

        self._client.publish(topic, payload, retain=retain)
        return True

    def subscribe(self, topic):
        if self._client is None:
            return False

        self._client.subscribe(topic)
        return True

    def set_last_will(self, topic, payload, retain=False):
        self._last_will_topic = topic
        self._last_will_message = payload
        self._last_will_retain = retain

        if self._client is None:
            return

        if topic is not None:
            self._client.set_last_will(topic, payload, retain=retain)

    def process_messages(self, topic, payload):
        print("MHA: received call %s, len: %d" % (topic, len(payload)))
        if self.on_message is not None:
            self.on_message(topic, payload)

        for device in self._device_types:
            device.on_message(topic, payload)

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        print("MHA: MQTT connected")

        if self.on_connect is not None:
            self.on_connect()

        self.device.publish_availability()

        for device in self._device_types:
            device.on_mqtt_connected()

    def _on_message(self, topic, payload):
        self.process_messages(topic, payload)

    def _on_disconnect(self, client, userdata, reason_code):
        print("MHA: MQTT disconnected")

        if self.on_disconnect is not None:
            self.on_disconnect()

        if self.on_state_changed is not None:
            self.on_state_changed(False)
