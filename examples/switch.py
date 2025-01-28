# SPDX-FileCopyrightText: Copyright (c) 2025 lbuque
#
# SPDX-License-Identifier: MIT

import sys
sys.path.append('..')

import mha
import time
# import machine
# import binascii

BROKER_ADDR = "192.168.2.2"

device = mha.HADevice("001122AABBC1")  # (binascii.hexlify(machine.unique_id()).decode('utf-8'))
mqtt = mha.HAMqtt(device)

device.set_name("MHA Switch")
device.set_software_version("0.1.0")

switch = mha.HASwitch("my_switch")

switch.set_current_state(True)
switch.set_name("My Switch")
switch.set_icon("mdi:lightbulb")

def on_switch_command(sender: mha.HASwitch, state: bool):
    print("Switch state:", state)
    sender.set_state(state)
    # to some action here

switch.on_command(on_switch_command)

mqtt.begin(BROKER_ADDR)

last_time = time.time()

while True:
    mqtt.loop()
    if time.time() - last_time > 5:
        switch.set_state(not switch.get_current_state())
        last_time = time.time()
