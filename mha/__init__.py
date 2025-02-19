# SPDX-FileCopyrightText: Copyright (c) 2024 lbuque
#
# SPDX-License-Identifier: MIT

_attrs = {
    "HADevice": "ha_device",
    "HAMqtt": "ha_mqtt",
    "HABaseDeviceType": "devices.basic_device",
    "HABinarySensor": "devices.binary_sensor",
    "HALight": "devices.light",
    "HASwitch": "devices.switch",
}


def __getattr__(attr):
    mod = _attrs.get(attr, None)
    if mod is None:
        raise AttributeError(attr)
    value = getattr(__import__(mod, globals(), None, True, 1), attr)
    globals()[attr] = value
    return value
