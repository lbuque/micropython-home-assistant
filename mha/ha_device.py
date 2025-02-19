# SPDX-FileCopyrightText: Copyright (c) 2024 lbuque
#
# SPDX-License-Identifier: MIT

from .utils.serializer import HASerializer
from .utils import constants
from .ha_mqtt import HAMqtt


class HADevice:

    def __init__(self, unique_id: str) -> None:
        self._unique_id = unique_id
        self._owns_unique_id = False
        self._serializer = HASerializer(None)
        self._availability_topic = None
        self._shared_availability = False
        self._available = True
        self._extended_unique_ids = False
        self._serializer.set_kv(constants.HADeviceIdentifiersProperty, unique_id)

    def get_unique_id(self) -> str:
        return self._unique_id

    def get_serializer(self):
        return self._serializer

    def is_shared_availability_enabled(self) -> bool:
        return self._shared_availability

    def is_extended_unique_ids_enabled(self) -> bool:
        return self._extended_unique_ids

    def get_availability_topic(self) -> str:
        return self._availability_topic

    def is_available(self) -> bool:
        return self._available

    def enable_extended_unique_ids(self):
        self._extended_unique_ids = True

    def set_unique_id(self, unique_id: str):
        self._unique_id = unique_id
        self._owns_unique_id = True
        self._serializer.set_kv(constants.HADeviceIdentifiersProperty, unique_id)

    def set_manufacturer(self, manufacturer: str):
        self._manufacturer = manufacturer
        self._serializer.set_kv(constants.HADeviceManufacturerProperty, manufacturer)

    def set_model(self, model: str):
        self._model = model
        self._serializer.set_kv(constants.HADeviceModelProperty, model)

    def set_name(self, name: str):
        self._name = name
        self._serializer.set_kv(constants.HANameProperty, name)

    def set_software_version(self, software_version: str):
        self._software_version = software_version
        self._serializer.set_kv(constants.HADeviceSoftwareVersionProperty, software_version)

    def set_configuration_url(self, configuration_url: str):
        self._configuration_url = configuration_url
        self._serializer.set_kv(constants.HADeviceConfigurationUrlProperty, configuration_url)

    def set_availability(self, online: bool):
        self._available = online
        self.publish_availability()

    def enable_shared_availability(self):
        if self._shared_availability:
            return True

        self._availability_topic = self._serializer.generate_data_topic(constants.HAAvailabilityTopic)
        return True

    def enable_last_will(self):
        mqtt = HAMqtt.instance()
        if mqtt is None or self._availability_topic is None:
            return

        mqtt.set_last_will(self._availability_topic, constants.HAOffline, retain=True)

    def publish_availability(self):
        mqtt = HAMqtt.instance()
        if mqtt is None or self._availability_topic is None:
            return

        payload = constants.HAOnline if self._available else constants.HAOffline
        mqtt.publish(self._availability_topic, payload, retain=True)
