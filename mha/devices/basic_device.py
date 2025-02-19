# SPDX-FileCopyrightText: Copyright (c) 2024 lbuque
#
# SPDX-License-Identifier: MIT

from ..ha_mqtt import HAMqtt
from ..utils.serializer import HASerializer
from ..utils import constants
import json


class HABaseDeviceType:
    AvailabilityDefault = 0
    AvailabilityOnline = 1
    AvailabilityOffline = 2

    def __init__(self, component_name, unique_id) -> None:
        self.component_name = component_name
        self.unique_id = unique_id
        self._name = None
        self._object_id = None
        self._serializer = None
        self._availability = self.AvailabilityDefault

        self.mqtt() and self.mqtt().add_device_type(self)

    def is_availability_configured(self):
        return self._availability != self.AvailabilityDefault

    def is_online(self):
        return self._availability == self.AvailabilityOnline

    def set_name(self, name):
        self._name = name

    def get_name(self):
        return self._name

    def set_object_id(self, object_id):
        self._object_id = object_id

    def get_object_id(self):
        return self._object_id

    def get_serializer(self):
        return self._serializer

    def set_availability(self, online):
        self._availability = self.AvailabilityOnline if online else self.AvailabilityOffline
        self.publish_availability()

    def mqtt(self):
        return HAMqtt.instance()

    def subscribe_topic(self, unique_id, topic):
        full_topic = HASerializer.generate_data_topic(unique_id, topic).encode("utf-8")
        HAMqtt.instance().subscribe(full_topic)

    def on_message(self, topic, payload):
        pass

    def build_serializer(self):
        raise NotImplementedError

    def destroy_serializer(self):
        if self._serializer is not None:
            del self._serializer

    def publish_config(self):
        self.build_serializer()

        if self._serializer is None:
            return

        topic = HASerializer.generate_config_topic(self.component_name, self.unique_id).encode(
            "utf-8"
        )
        payload = json.dumps(self._serializer.flush()).encode("utf-8")
        # print("MHA publish_config topic: ", topic)
        # print("MHA publish_config payload: ", payload)
        if topic is not None:
            self.mqtt().publish(topic, payload, True)

    def publish_availability(self):
        device = self.mqtt().device
        if (
            device is None
            or device.is_shared_availability_enabled()
            or (not self.is_availability_configured())
        ):
            return

        self.publish_on_data_topic(
            constants.HAAvailabilityTopic, constants.HAOnline if self._availability else constants.HAOffline, True
        )

    def publish_on_data_topic(self, topic, payload, retained=False):
        full_topic = HASerializer.generate_data_topic(self.unique_id, topic).encode("utf-8")
        if full_topic is None:
            return False

        return self.mqtt().publish(full_topic, payload.encode("utf-8"), retain=retained)
