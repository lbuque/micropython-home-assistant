# SPDX-FileCopyrightText: Copyright (c) 2024 lbuque
#
# SPDX-License-Identifier: MIT

from ..ha_mqtt import HAMqtt
from .constants import (
    HASerializerSlash,
    HAConfigTopic,
    HAAvailabilityTopic,
    HADeviceProperty,
    HAUniqueIdProperty,
    HASerializerUnderscore,
)


class EntryType:
    UnknownEntryType = 0
    PropertyEntryType = 1
    TopicEntryType = 2
    FlagEntryType = 3


class SerializerEntry:
    def __init__(self, type, subtype, property, value) -> None:
        self.type = type
        self.subtype = subtype
        self.property = property
        self.value = value


class HASerializer:
    WithDevice = 1
    WithAvailability = 2
    WithUniqueId = 3

    def __init__(self, device_type):
        self._device_type = device_type
        self._entries = []
        self._payload = {}

    def set_kv(self, key, value):
        if key is None or value is None:
            return

        self._entries.append(SerializerEntry(EntryType.PropertyEntryType, None, key, value))

    def set_topic(self, topic):
        self._entries.append(SerializerEntry(EntryType.TopicEntryType, None, topic, None))

    def set_flag(self, flag):
        if flag == self.WithDevice or flag == self.WithUniqueId:
            self._entries.append(SerializerEntry(EntryType.FlagEntryType, flag, None, None))
        elif flag == self.WithAvailability:
            mqtt = HAMqtt.instance()
            is_shared_availability = mqtt.device.is_shared_availability_enabled()
            is_availability_configured = self._device_type.is_availability_configured()
            if is_shared_availability or is_availability_configured:
                self._entries.append(
                    SerializerEntry(
                        EntryType.TopicEntryType,
                        None,
                        HAAvailabilityTopic,
                        mqtt.device.get_availability_topic() if is_shared_availability else None,
                    )
                )

    def flush(self) -> bool:
        mqtt = HAMqtt.instance()
        if mqtt is None or (self._device_type and mqtt.device is None):
            return False
        self._flush_entry()
        return self._payload

    @staticmethod
    def generate_data_topic(object_id, topic):
        mqtt = HAMqtt.instance()
        if mqtt is None or mqtt.data_prefix is None or mqtt.device is None:
            return None

        full_topic = (
            mqtt.data_prefix + HASerializerSlash + mqtt.device.get_unique_id() + HASerializerSlash
        )
        if object_id is None:
            full_topic += object_id + HASerializerSlash

        full_topic += topic
        return full_topic

    @staticmethod
    def generate_config_topic(component, object_id):
        mqtt = HAMqtt.instance()
        if mqtt is None or mqtt.data_prefix is None or mqtt.device is None:
            return None

        topic = (
            mqtt.discovery_prefix
            + HASerializerSlash
            + component
            + HASerializerSlash
            + mqtt.device.get_unique_id()
            + HASerializerSlash
            + object_id
            + HASerializerSlash
            + HAConfigTopic
        )

        return topic

    def _flush_entry(self):
        for entry in self._entries:
            if entry.type == EntryType.PropertyEntryType:
                self._payload[entry.property] = entry.value
            elif entry.type == EntryType.TopicEntryType:
                if entry.value is not None:
                    self._payload[entry.property] = str(entry.value)
                else:
                    self._payload[entry.property] = self.generate_data_topic(
                        self._device_type.unique_id, entry.property
                    )
            elif entry.type == EntryType.FlagEntryType:
                mqtt = HAMqtt.instance()
                device = mqtt.device
                if entry.subtype == self.WithDevice and device is not None:
                    self._payload[HADeviceProperty] = device.get_serializer().flush()
                elif entry.subtype == self.WithUniqueId and device is not None:
                    self._payload[HAUniqueIdProperty] = (
                        device.get_unique_id()
                        + HASerializerUnderscore
                        + self._device_type.unique_id
                    )
