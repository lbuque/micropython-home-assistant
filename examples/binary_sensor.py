import mha
import time
# import machine
# import binascii

BROKER_ADDR = "192.168.2.2"

device = mha.HADevice("001122AABBCC")  # (binascii.hexlify(machine.unique_id()).decode('utf-8'))
mqtt = mha.HAMqtt(device)

device.set_name("MicroPython")
device.set_software_version("0.1.0")

sensor = mha.HABinarySensor("my_sensor")

sensor.set_current_state(True)
sensor.set_name("Door Sensor")
sensor.set_device_class("door")
sensor.set_icon("mdi:door")

mqtt.begin(BROKER_ADDR)

last_time = time.time()

while True:
    mqtt.loop()

    if time.time() - last_time > 5:
        print("Publishing state")
        sensor.set_state(not sensor.get_current_state())
        last_time = time.time()
