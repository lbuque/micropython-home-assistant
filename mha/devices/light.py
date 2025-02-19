# SPDX-FileCopyrightText: Copyright (c) 2025 lbuque
#
# SPDX-License-Identifier: MIT

from .basic_device import HABaseDeviceType
from ..utils.serializer import HASerializer
from ..utils import constants


class HALight(HABaseDeviceType):

    DefaultFeatures = 0
    BrightnessFeature = 1
    ColorTemperatureFeature = 2
    RGBColorFeature = 4

    def __init__(self, unique_id: str, features: int = DefaultFeatures):
        super().__init__(constants.HAComponentLight, unique_id)
        self._features = features
        self._icon = None
        self._retain = False
        self._optimistic = False
        self._brightness_scale = 0
        self._current_state = False
        self._current_brightness = 0
        self._min_mireds = None
        self._max_mireds = None
        self._current_color_temperature = 0
        self._current_rgb_color = None
        self._state_callback = None
        self._brightness_callback = None
        self._color_temperature_callback = None
        self._rgb_color_callback = None

    def set_state(self, state: bool, force: bool = False) -> bool:
        if force is False and state == self._current_state:
            return True

        if self._publish_state(state):
            self._current_state = state
            return True

        return False

    def setBrightness(self, brightness: int, force: bool = False) -> bool:
        if force is False and brightness == self._current_brightness:
            return True

        if self._publish_brightness(brightness):
            self._current_brightness = brightness
            return True

        return False

    def set_color_temperature(self, temperature: int, force: bool = False) -> bool:
        if force is False and temperature == self._current_color_temperature:
            return True

        if self._publish_color_temperature(temperature):
            self._current_color_temperature = temperature
            return True

        return False

    def set_rgb_color(self, color, force: bool = False) -> bool:
        if force is False and color == self._current_rgb_color:
            return True

        if self._publish_rgb_color(color):
            self._current_rgb_color = color
            return True

        return False

    def turn_on(self, force: bool = False) -> bool:
        self.set_state(True, force)

    def turn_off(self, force: bool = False) -> bool:
        self.set_state(False, force)

    def set_current_state(self, state: bool) -> None:
        self._current_state = state

    def get_current_state(self) -> bool:
        return self._current_state

    def set_current_brightness(self, brightness: int) -> None:
        self._current_brightness = brightness

    def get_current_brightness(self) -> int:
        return self._current_brightness

    def set_current_color_temperature(self, temperature: int) -> None:
        self._current_color_temperature = temperature

    def get_current_color_temperature(self) -> int:
        return self._current_color_temperature

    def set_current_rgbcolor(self, color) -> None:
        self._current_rgb_color = color

    def get_current_rgbcolor(self):
        return self._current_rgb_color

    def set_icon(self, icon: str) -> None:
        self._icon = icon

    def set_retain(self, retain: bool) -> None:
        self._retain = retain

    def set_optimistic(self, optimistic: bool) -> None:
        self._optimistic = optimistic

    def set_min_mireds(self, mireds: int) -> None:
        self._min_mireds = mireds

    def set_max_mireds(self, mireds: int) -> None:
        self._max_mireds = mireds

    def on_state_command(self, callback) -> None:
        self._state_callback = callback

    def on_brightness_command(self, callback) -> None:
        self._brightness_callback = callback

    def on_color_temperature_command(self, callback) -> None:
        self._color_temperature_callback = callback

    def on_rgb_color_command(self, callback) -> None:
        self._rgb_color_callback = callback

    def build_serializer(self) -> None:
        if self._serializer or self.unique_id is None:
            return

        self._serializer = HASerializer(self)
        self._serializer.set_kv(constants.HANameProperty, self._name)
        self._serializer.set_kv(constants.HAObjectIdProperty, self._object_id)
        self._serializer.set_flag(HASerializer.WithUniqueId)
        self._serializer.set_kv(constants.HAIconProperty, self._icon)

        self._retain and self._serializer.set_kv(constants.HARetainProperty, self._retain)
        self._optimistic and self._serializer.set_kv(constants.HAOptimisticProperty, self._optimistic)

        if self._features & self.BrightnessFeature:
            self._serializer.set_topic(constants.HABrightnessStateTopic)
            self._serializer.set_topic(constants.HABrightnessCommandTopic)

            if self._brightness_scale:
                self._serializer.set_kv(constants.HABrightnessScaleProperty, self._brightnessScale)

        if self._features & self.ColorTemperatureFeature:
            self._serializer.set_topic(constants.HAColorTemperatureStateTopic)
            self._serializer.set_topic(constants.HAColorTemperatureCommandTopic)

            if self._min_mireds:
                self._serializer.set_kv(constants.HAMinMiredsProperty, self._min_mireds)

            if self._max_mireds:
                self._serializer.set_kv(constants.HAMaxMiredsProperty, self._max_mireds)

        if self._features & self.RGBColorFeature:
            self._serializer.set_topic(constants.HARGBCommandTopic)
            self._serializer.set_topic(constants.HARGBStateTopic)

        self._serializer.set_flag(HASerializer.WithDevice)
        self._serializer.set_flag(HASerializer.WithAvailability)
        self._serializer.set_topic(constants.HAStateTopic)
        self._serializer.set_topic(constants.HACommandTopic)

    def on_mqtt_connected(self) -> None:
        if self.unique_id is None:
            return

        self.publish_config()
        self.publish_availability()

        if self._retain:
            self._publish_state()
            self._publish_brightness()
            self._publish_color_temperature()
            self._publish_rgb_color()

        self.subscribe_topic(self.unique_id, constants.HACommandTopic)

        self._features & self.BrightnessFeature and self.subscribe_topic(self.unique_id, constants.HABrightnessCommandTopic)
        self._features & self.ColorTemperatureFeature and self.subscribe_topic(self.unique_id, constants.HAColorTemperatureCommandTopic)
        self._features & self.RGBColorFeature and self.subscribe_topic(self.unique_id, constants.HARGBCommandTopic)

    def on_message(self, topic, payload):
        if self._serializer.compare_data_topics(
            topic,
            self.unique_id,
            constants.HACommandTopic
        ):
            self._handle_state_command(payload)

        if self._serializer.compare_data_topics(
            topic,
            self.unique_id,
            constants.HABrightnessCommandTopic
        ):
            self._handle_brightness_command(payload)

        if self._serializer.compare_data_topics(
            topic,
            self.unique_id,
            constants.HAColorTemperatureCommandTopic
        ):
            self._handle_color_temperature_command(payload)

        if self._serializer.compare_data_topics(
            topic,
            self.unique_id,
            constants.HARGBCommandTopic
        ):
            print("RGB color command, payload: ", payload)
            self._handle_rgb_color_command(payload)

    def _publish_state(self, state: bool) -> bool:
        return self.publish_on_data_topic(constants.HAStateTopic, constants.HAStateOn if state else constants.HAStateOff)

    def _publish_brightness(self, brightness: int) -> bool:
        if self._features & self.BrightnessFeature:
            self.publish_on_data_topic(constants.HABrightnessStateTopic, str(brightness))
        else:
            return False

    def _publish_color_temperature(self, temperature: int) -> None:
        if self._features & self.ColorTemperatureFeature:
            self.publish_on_data_topic(constants.HAColorTemperatureStateTopic, str(temperature))
        else:
            return False

    def _publish_rgb_color(self, color) -> None:
        if self._features & self.RGBColorFeature:
            self.publish_on_data_topic(constants.HARGBCommandTopic, color)
        else:
            return False

    def _handle_state_command(self, payload: str) -> None:
        state = len(payload) == len(constants.HAStateOn)
        self._state_callback and self._state_callback(self, state)

    def _handle_brightness_command(self, payload: str) -> None:
        brightness = int(payload)
        self._brightness_callback and self._brightness_callback(self, brightness)

    def _handle_color_temperature_command(self, payload: str) -> None:
        temperature = int(payload)
        self._color_temperature_callback and self._color_temperature_callback(self, temperature)

    def _handle_rgb_color_command(self, payload: bytes) -> None:
        r, g, b = payload.split(b",")
        self._rgb_color_callback and self._rgb_color_callback(self, int(r), int(g), int(b)
        )
