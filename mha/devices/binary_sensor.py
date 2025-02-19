# SPDX-FileCopyrightText: Copyright (c) 2024 lbuque
#
# SPDX-License-Identifier: MIT

from .basic_device import HABaseDeviceType
from ..utils.serializer import HASerializer
from ..utils import constants


class HABinarySensor(HABaseDeviceType):
    def __init__(self, unique_id) -> None:
        super().__init__(constants.HAComponentBinarySensor, unique_id)
        self._class = None
        self._icon = None
        self._expire_after = 0
        self._current_state = False

    def set_state(self, state: bool, force=False) -> bool:
        if force is False and state == self._current_state:
            return True

        if self._publish_state(state):
            self._current_state = state
            return True

        return False

    def set_expire_after(self, expire_after: int) -> None:
        if expire_after > 0:
            self._expire_after = expire_after
        else:
            self._expire_after = 0

    def set_current_state(self, state: bool) -> None:
        self._current_state = state

    def get_current_state(self) -> bool:
        return self._current_state

    def set_device_class(self, class_name: str) -> None:
        self._class = class_name

    def set_icon(self, icon: str) -> None:
        self._icon = icon

    def build_serializer(self):
        if self._serializer is not None or self.unique_id is None:
            return

        self._serializer = HASerializer(self)
        self._serializer.set_kv(constants.HANameProperty, self._name)
        self._serializer.set_kv(constants.HAObjectIdProperty, self._object_id)
        self._serializer.set_flag(HASerializer.WithUniqueId)
        self._serializer.set_kv(constants.HADeviceClassProperty, self._class)
        self._serializer.set_kv(constants.HAIconProperty, self._icon)

        self._serializer.set_flag(HASerializer.WithDevice)
        self._serializer.set_flag(HASerializer.WithAvailability)
        self._serializer.set_topic(constants.HAStateTopic)

    def on_mqtt_connected(self):
        if self.unique_id is None:
            return

        print("MHA: HABinarySensor on_mqtt_connected")

        self.publish_config()
        self.publish_availability()
        self._publish_state(self._current_state)

    def _publish_state(self, state) -> bool:
        return self.publish_on_data_topic(constants.HAStateTopic, constants.HAStateOn if state else constants.HAStateOff)
