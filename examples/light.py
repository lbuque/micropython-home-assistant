# SPDX-FileCopyrightText: Copyright (c) 2025 lbuque
#
# SPDX-License-Identifier: MIT

import sys
sys.path.append('..')

import mha
import time
# import machine
# import binascii

BROKER_ADDR = "192.168.2.80"

device = mha.HADevice("001122AABBC2")  # (binascii.hexlify(machine.unique_id()).decode('utf-8'))
mqtt = mha.HAMqtt(device)

device.set_name("MHA Light")
device.set_software_version("0.1.0")

light = mha.HALight("prettyLight", features=mha.HALight.BrightnessFeature|mha.HALight.ColorTemperatureFeature|mha.HALight.RGBColorFeature)

light.set_name("Bathroom")

def on_switch_command(sender: mha.HALight, state: bool):
    print("Light state:", state)
    sender.set_state(state)
    # to some action here

def on_brightness_command(sender: mha.HALight, brightness: int):
    print("Brightness:", brightness)
    sender.setBrightness(brightness)
    # to some action here

def on_color_temperature_command(sender: mha.HALight, temperature: int):
    print("Color temperature:", temperature)
    sender.set_color_temperature(temperature)

def on_rgb_color_command(sender: mha.HALight, r: int, g: int, b: int):
    print("RGB color:", r, g, b)
    sender.set_rgb_color(r, g, b)

light.on_state_command(on_switch_command)

light.on_brightness_command(on_brightness_command)

light.on_color_temperature_command(on_color_temperature_command)

light.on_rgb_color_command(on_rgb_color_command)

mqtt.begin(BROKER_ADDR, user=b"test", password=b"test")

last_time = time.time()

while True:
    mqtt.loop()
    # if time.time() - last_time > 5:
    #     light.set_state(not light.get_current_state())
    #     last_time = time.time()
