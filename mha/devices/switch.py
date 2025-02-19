# SPDX-FileCopyrightText: Copyright (c) 2025 lbuque
#
# SPDX-License-Identifier: MIT

from .basic_device import HABaseDeviceType
from ..utils.serializer import HASerializer
from ..utils import constants


class HASwitch(HABaseDeviceType):

    def __init__(self, unique_id):
        super().__init__(constants.HAComponentSwitch, unique_id)
        self._class = None
        self._icon = None
        self._retain = False
        self._optimistic = False
        self._current_state = False
        self._command_callback = None

    def set_state(self, state: bool, force: bool=False) -> bool:
        if force is False and state == self._current_state:
            return True

        if self._publish_state(state):
            self._current_state = state
            return True

        return False

    def turn_on(self) -> bool:
        return self.set_state(True)

    def turn_off(self) -> bool:
        return self.set_state(False)

    def set_current_state(self, state: bool) -> None:
        self._current_state = state

    def get_current_state(self) -> bool:
        return self._current_state

    def set_device_class(self, class_name: str) -> None:
        self._class = class_name

    def set_icon(self, icon: str) -> None:
        self._icon = icon

    def set_retain(self, retain: bool) -> None:
        self._retain = retain

    def set_optimistic(self, optimistic: bool) -> None:
        self._optimistic = optimistic

    def on_command(self, callback) -> None:
        self._command_callback = callback

    def build_serializer(self) -> None:
        if self._serializer is not None or self.unique_id is None:
            return

        self._serializer = HASerializer(self)
        self._serializer.set_kv(constants.HANameProperty, self._name)
        self._serializer.set_kv(constants.HAObjectIdProperty, self._object_id)
        self._serializer.set_flag(HASerializer.WithUniqueId)
        self._serializer.set_kv(constants.HADeviceClassProperty, self._class)
        self._serializer.set_kv(constants.HAIconProperty, self._icon)

        self._retain and self._serializer.set_kv(constants.HARetainProperty, self._retain)
        self._optimistic and self._serializer.set_kv(constants.HAOptimisticProperty, self._optimistic)

        self._serializer.set_flag(HASerializer.WithDevice)
        self._serializer.set_flag(HASerializer.WithAvailability)
        self._serializer.set_topic(constants.HAStateTopic)
        self._serializer.set_topic(constants.HACommandTopic)

    def on_mqtt_connected(self):
        if self.unique_id is None:
            return

        print("MHA: HASwitch on_mqtt_connected")

        self.publish_config()
        self.publish_availability()
        not self._retain and self._publish_state(self._current_state)
        self.subscribe_topic(self.unique_id, constants.HACommandTopic)

    def on_message(self, topic: str, payload: str) -> None:
        print("MHA: HASwitch on_message: ", topic, payload)
        if self._command_callback and self._serializer and self._serializer.compare_data_topics(topic, self.unique_id, constants.HACommandTopic):
            state = len(payload) == len(constants.HAStateOn)
            self._command_callback(self, state)

    def _publish_state(self, state) -> bool:
        return self.publish_on_data_topic(constants.HAStateTopic, constants.HAStateOn if state else constants.HAStateOff)
